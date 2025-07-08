from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import tempfile
import shutil
import sys
import pandas as pd
import numpy as np
import io
import xlsxwriter
import base64
from time import time
from datetime import datetime, date, time as dt_time
from werkzeug.utils import secure_filename
import traceback
import logging
import argparse

# Handle both development and PyInstaller packaged modes
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    application_path = sys._MEIPASS
    sys.path.insert(0, application_path)
    print(f"PyInstaller mode - base path: {application_path}")
    
    # List what's actually available in the bundle
    print("Available files in bundle:")
    for item in os.listdir(application_path):
        print(f"  {item}")
    
    # Try to import from the bundle with fallbacks
    try:
        from config import config, Config
        print("[OK] Imported config")
    except ImportError:
        print("[ERROR] config not found, using defaults")
        # Create minimal config fallback
        config = {'max_file_size_mb': 200}
        class Config:
            @staticmethod
            def safe_convert(data):
                return data
    
    try:
        from comparison_engine import ComparisonEngine
        print("[OK] Imported ComparisonEngine")
    except ImportError:
        print("[ERROR] ComparisonEngine not found")
        class ComparisonEngine:
            @staticmethod
            def run_comparison(session_data, excel_processor, safe_convert):
                return {"error": "ComparisonEngine not available"}
    
    try:
        from excel_processor import ExcelProcessor
        print("[OK] Imported ExcelProcessor")
    except ImportError:
        print("[ERROR] ExcelProcessor not found")
        class ExcelProcessor:
            def __init__(self, filepath):
                self.filepath = filepath
                self.sheet_names = []
            def load_workbook(self):
                return False
            def get_sheet_data(self, sheet_name, is_base_file=False):
                import pandas as pd
                return pd.DataFrame()
    
    try:
        from site_matcher import SiteMatcher
        print("[OK] Imported SiteMatcher")
    except ImportError:
        print("[ERROR] SiteMatcher not found")
        class SiteMatcher:
            pass
    
    try:
        from data_models import FileInfo, ComparisonSummary
        print("[OK] Imported data_models")
    except ImportError:
        print("[ERROR] data_models not found")
        class FileInfo:
            def __init__(self, file_name, sheet_names):
                self.file_name = file_name
                self.sheet_names = sheet_names
            @classmethod
            def from_path(cls, filepath, sheet_names):
                import os
                return cls(os.path.basename(filepath), sheet_names)
        
        class ComparisonSummary:
            pass
    
    try:
        from report_generating import ReportGenerator
        print("[OK] Imported ReportGenerator")
    except ImportError:
        print("[ERROR] ReportGenerator not found")
        class ReportGenerator:
            @staticmethod
            def generate_excel_report_temp(report, session_data, temp_dir):
                return None
            @staticmethod
            def generate_csv_report_temp(report, session_data, temp_dir):
                return None
            @staticmethod
            def generate_pdf_report_temp(report, session_data, temp_dir):
                return None

else:
    # Development mode - your original code
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    print(f"Development mode - project root: {project_root}")
    
    # Import application modules
    from src.utils.config import config, Config
    from src.core.comparison_engine import ComparisonEngine
    from src.core.excel_processor import ExcelProcessor
    from src.core.site_matcher import SiteMatcher
    from src.models.data_models import FileInfo, ComparisonSummary
    from src.core.report_generating import ReportGenerator

safe_convert = Config.safe_convert

app = Flask(__name__)
CORS(app)

# Handle paths for both development and PyInstaller modes
if getattr(sys, 'frozen', False):
    # PyInstaller mode
    project_root = os.path.dirname(sys.executable)
    frontend_dir = None  # Not used in PyInstaller mode
else:
    # project_root is already defined in development mode
    frontend_dir = os.path.join(project_root, 'src', 'frontend')

# Configuration - Use backend temp directory
temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
app.config['UPLOAD_FOLDER'] = temp_dir
app.config['MAX_CONTENT_LENGTH'] = config.get('max_file_size_mb', 200) * 1024 * 1024

# Ensure temp directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage for session-like data
session_data = {
    'base_file_info': None,
    'comp_file_info': [],
    'comparison_settings': None,
    'comparison_results': None,
    'reports': [],
    'site_mappings': {"LE": "Lens", "BGL": "BGL"}
}

def is_packaged_app():
    """Detect if running in packaged mode"""
    app_path = os.path.abspath(__file__)
    return 'Temp' in app_path and 'resources' in app_path

app.isPackaged = is_packaged_app()

# # Serve frontend files
# @app.route('/')
# def serve_frontend():
#     if getattr(sys, 'frozen', False):
#         return jsonify({
#             "status": "ECT Technis Backend Running", 
#             "message": "Backend is operational",
#             "frontend": "Use Electron app interface"
#         })
#     else:
#         return send_from_directory(frontend_dir, 'index.html')

# @app.route('/<path:filename>')
# def serve_static(filename):
#     if getattr(sys, 'frozen', False):
#         return jsonify({'error': 'Static files not available in packaged mode'}), 404
#     else:
#         try:
#             return send_from_directory(frontend_dir, filename)
#         except FileNotFoundError:
#             return jsonify({'error': 'File not found'}), 404

@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "ECT Technis Backend is running",
        "mode": "PyInstaller" if getattr(sys, 'frozen', False) else "Development"
    })

@app.route('/api/upload-base-file', methods=['POST'])
def upload_base_file():
    print("Uploading base file")
    try:
        if 'file' not in request.files:
            print("No file provided")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file
        processor = ExcelProcessor(filepath)
        if processor.load_workbook():
            session_data['base_file_info'] = FileInfo.from_path(filepath, processor.sheet_names)
            print(f"Base file uploaded successfully: {filename}")
            return jsonify({
                'success': True,
                'filename': filename,
                'sheets': processor.sheet_names,
                'message': f'Fichier de base chargé: {filename}'
            })
        else:
            return jsonify({'error': 'Failed to process Excel file'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-comparison-files', methods=['POST'])
def upload_comparison_files():
    try:
        if 'files' not in request.files:
            print("No files provided")
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        processed_files = []
        session_data['comp_file_info'] = []
        
        for file in files:
            if file.filename != '':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                processor = ExcelProcessor(filepath)
                if processor.load_workbook():
                    file_info = FileInfo.from_path(filepath, processor.sheet_names)
                    session_data['comp_file_info'].append(file_info)
                    processed_files.append({
                        'filename': filename,
                        'sheets': processor.sheet_names
                    })
        print(f"Uploaded comparison files: {len(processed_files)}")
        return jsonify({
            'success': True,
            'files': processed_files,
            'message': f'{len(processed_files)} fichier(s) de comparaison téléchargé(s)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-base-file-info')
def get_base_file_info():
    if session_data['base_file_info']:
        print("Retrieving base file info")
        return jsonify({
            'filename': session_data['base_file_info'].file_name,
            'sheets': session_data['base_file_info'].sheet_names
        })
    return jsonify({'error': 'No base file loaded'}), 404

@app.route('/api/get-comparison-files-info')
def get_comparison_files_info():
    files_info = []
    for file_info in session_data['comp_file_info']:
        files_info.append({
            'filename': file_info.file_name,
            'sheets': file_info.sheet_names
        })
    return jsonify({'files': files_info})

@app.route('/api/preview-sheet', methods=['POST'])
def preview_sheet():
    try:
        data = request.get_json()
        filename = data.get('filename')
        sheet_name = data.get('sheet_name')
        is_base_file = data.get('is_base_file', False)

        # Find the file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return jsonify({'error': 'File not found'}), 404
        
        processor = ExcelProcessor(filepath)
        if processor.load_workbook():
            # Get processed data
            processed_data = processor.get_sheet_data(sheet_name, is_base_file=is_base_file)
            processed_preview = processed_data.head(5).fillna('').to_dict('records')

            return jsonify({
                'processed_preview': safe_convert(processed_preview),
                'processed_columns': safe_convert(processed_data.columns.tolist())
            })
        else:
            return jsonify({'error': 'Failed to process file'}), 400
            
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-site-mappings', methods=['POST'])
def set_site_mappings():
    try:
        data = request.get_json()
        session_data['site_mappings'] = data.get('mappings', {})
        print("Site mappings updated")
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating site mappings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-site-mappings')
def get_site_mappings():
    print("Retrieving site mappings")
    return jsonify({'mappings': session_data['site_mappings']})

@app.route('/api/start-comparison', methods=['POST'])
def start_comparison():
    try:
        data = request.get_json()
        selected_sheets = data.get('selected_sheets', [])
        comparison_mode = data.get('comparison_mode', 'full')

        if not session_data['base_file_info'] or not session_data['comp_file_info']:
            return jsonify({'error': 'Files not uploaded'}), 400       
        
        if not selected_sheets:
            return jsonify({'error': 'No sheets selected'}), 400

        # Store comparison settings
        session_data['comparison_settings'] = {
            'base_file': session_data['base_file_info'],
            'comparison_files': session_data['comp_file_info'],
            'selected_sheets': selected_sheets,
            'site_mappings': session_data['site_mappings'],
            'site_column': 'Site',
            'column_indices': list(range(1, 10)),
            'comparison_mode': comparison_mode,
            'use_dynamic_detection': data.get('use_dynamic_detection', True)
        }
        
        # Run comparison
        results = ComparisonEngine.run_comparison(session_data, ExcelProcessor, safe_convert)
        return jsonify({
            'success': True,
            'results': results
        })
            
    except Exception as e:
        print(f"Error in start_comparison : {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-comparison-results')
def get_comparison_results():
    if session_data['comparison_results']:
        return jsonify(session_data['comparison_results'])
    return jsonify({
        'results': {},
        'summary': {
            'total_sheets_compared': 0,
            'total_differences': 0,
            'total_cells_compared': 0,
            'execution_time_seconds': 0
        },
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/save-report', methods=['POST'])
def save_report():
    try:
        if not session_data['comparison_results']:
            return jsonify({'error': 'No comparison results to save'}), 400
        
        report_id = f"report_{len(session_data['reports']) + 1:03d}"
        summary = session_data['comparison_results']['summary']
        settings = session_data['comparison_settings']
        
        # Calculate match rate
        cells_compared = summary.get('total_cells_compared', 1)
        if cells_compared == 0: cells_compared = 1
        diffs = summary.get('total_differences', 0)
        dups = summary.get('total_duplicates', 0)
        match_rate = max(0, 100 - (((diffs + dups) / cells_compared) * 100))
        
        comp_files = [f.file_name for f in settings['comparison_files']]
        
        report = {
            "id": report_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "base_file": settings['base_file'].file_name,
            "comparison_files": comp_files,
            "comparison_file": ", ".join(comp_files),
            "differences": summary['total_differences'],
            "duplicates": summary['total_duplicates'],
            "match_rate": f"{match_rate:.2f}%",
            "comparison_mode": settings['comparison_mode']
        }
        
        session_data['reports'].append(report)
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': f'Rapport enregistré avec ID: {report_id}'
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-reports')
def get_reports():
    return jsonify({'reports': session_data['reports']})

@app.route('/api/export-report', methods=['POST'])
def export_report():
    try:
        data = request.get_json()
        report_id = data.get('report_id')
        format_type = data.get('format', 'excel')
        filename = data.get('filename')

        if not filename:
            ext = {'excel': 'xlsx', 'csv': 'csv', 'pdf': 'pdf'}.get(format_type, 'xlsx')
            filename = f"ECT_Technis_Report_{report_id}_{datetime.now().strftime('%Y%m%d')}.{ext}"

        # Find the report
        report = next((r for r in session_data['reports'] if r['id'] == report_id), None)
        if not report:
            return jsonify({'error': 'Report not found'}), 404

        # Create temporary file
        temp_file = None
        try:
            if format_type == 'excel':
                temp_file = ReportGenerator.generate_excel_report_temp(report, session_data, app.config['UPLOAD_FOLDER'])
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif format_type == 'csv':
                temp_file = ReportGenerator.generate_csv_report_temp(report, session_data, app.config['UPLOAD_FOLDER'])
                mimetype = 'text/csv'
            elif format_type == 'pdf':
                temp_file = ReportGenerator.generate_pdf_report_temp(report, session_data, app.config['UPLOAD_FOLDER'])
                mimetype = 'application/pdf'
            else:
                return jsonify({'error': 'Format non supporté'}), 400

            if not temp_file or not os.path.exists(temp_file):
                return jsonify({'error': 'Erreur lors de la génération du fichier temporaire'}), 500

            # Send file and clean up automatically
            return send_file(
                temp_file,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
            
        except Exception as e:
            # Clean up temp file in case of error
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
            raise e
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Erreur lors de l\'export: {str(e)}'}), 500
        
# Serve documentation files
@app.route('/docs/<path:filename>')
def serve_docs(filename):
    """Serve documentation files from docs directory"""
    if app.isPackaged:
        docs_dir = os.path.join(project_root, 'docs')
    else:
        docs_dir = os.path.join(project_root, 'docs')
    
    print(f"Looking for docs in: {docs_dir}")
    print(f"Requested file: {filename}")
    
    # Check if docs directory exists
    if not os.path.exists(docs_dir):
        print(f"Docs directory not found: {docs_dir}")
        return jsonify({'error': 'Documentation directory not found'}), 404
    
    try:
        return send_from_directory(docs_dir, filename)
    except FileNotFoundError:
        print(f"Documentation file not found: {filename}")
        return jsonify({'error': 'Documentation file not found'}), 404

@app.route('/docs/legal/<path:filename>')
def serve_legal_docs(filename):
    """Serve legal documentation files"""
    if app.isPackaged:
        legal_docs_dir = os.path.join(project_root, 'docs', 'legal')
    else:
        legal_docs_dir = os.path.join(project_root, 'docs', 'legal')
    
    print(f"Looking for legal docs in: {legal_docs_dir}")
    print(f"Requested legal file: {filename}")
    
    # Check if legal docs directory exists
    if not os.path.exists(legal_docs_dir):
        print(f"Legal docs directory not found: {legal_docs_dir}")
        return jsonify({'error': 'Legal documentation directory not found'}), 404
    
    try:
        return send_from_directory(legal_docs_dir, filename)
    except FileNotFoundError:
        print(f"Legal documentation file not found: {filename}")
        return jsonify({'error': 'Legal document not found'}), 404

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Entry point for cleanup and shutdown."""
    cleanup_and_shutdown()
    return ('', 204)

def cleanup_and_shutdown():
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
    except Exception as e:
        app.logger.error(f"Erreur lors du cleanup temp: {e}")

    # Get log file path before closing handlers
    log_file = config.get('logging.file', 'app.log')
    logging.shutdown()

    try:
        if os.path.exists(log_file):
            with open(log_file, 'w'):
                pass
            print(f"Log file truncated: {log_file}")
    except Exception as e:
        print(f"Erreur lors de la réinitialisation du log: {e}")

    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
    else:
        os._exit(0)

def main():
    parser = argparse.ArgumentParser(description='ECT Technis Backend Server')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the server on')
    try:
        args, unknown = parser.parse_known_args()
        if unknown:
            print(f"Warning: Unknown arguments ignored: {unknown}")
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        args = parser.parse_args([])  # Use empty args as fallback

    if getattr(sys, 'frozen', False):
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

    print(f"Starting Flask server on port {args.port}")
    app.run(
        host='127.0.0.1',
        port=args.port,
        debug=False,
        use_reloader=False,
        threaded=True
    )

if __name__ == '__main__':
    main()