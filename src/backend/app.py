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

def setup_logging():
    try:
        # Create user logs directory
        app_data_path = os.environ.get('APPDATA', os.path.expanduser('~'))
        log_dir = os.path.join(app_data_path, 'ECT_Technis', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a log file with timestamp
        log_file = os.path.join(log_dir, f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_file, mode='a', encoding='utf-8')
            ]
        )
        logger = logging.getLogger(__name__)
        logger.info(f"Backend started - Log file: {log_file}")
        
        return logger, log_file
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__), None

logger, log_file_path = setup_logging()

# Handle both development and PyInstaller packaged modes
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    application_path = sys._MEIPASS
    sys.path.insert(0, application_path)
    logger.info("Running in PyInstaller mode")
    
    # Import modules with fallbacks
    try:
        from config import config, Config
    except ImportError:
        logger.warning("Config module not found, using defaults")
        config = {'max_file_size_mb': 200}
        class Config:
            @staticmethod
            def safe_convert(data):
                return data
    
    try:
        from comparison_engine import ComparisonEngine
    except ImportError:
        logger.error("ComparisonEngine not found")
        class ComparisonEngine:
            @staticmethod
            def run_comparison(session_data, excel_processor, safe_convert):
                return {"error": "ComparisonEngine not available"}
    
    try:
        from excel_processor import ExcelProcessor
    except ImportError:
        logger.error("ExcelProcessor not found")
        class ExcelProcessor:
            def __init__(self, filepath):
                self.filepath = filepath
                self.sheet_names = []
            def load_workbook(self):
                return False
            def get_sheet_data(self, sheet_name, is_base_file=False):
                return pd.DataFrame()
    
    try:
        from site_matcher import SiteMatcher
    except ImportError:
        logger.warning("SiteMatcher not found")
        class SiteMatcher:
            pass
    
    try:
        from data_models import FileInfo, ComparisonSummary
    except ImportError:
        logger.error("data_models not found")
        class FileInfo:
            def __init__(self, file_name, sheet_names):
                self.file_name = file_name
                self.sheet_names = sheet_names
            @classmethod
            def from_path(cls, filepath, sheet_names):
                return cls(os.path.basename(filepath), sheet_names)
        
        class ComparisonSummary:
            pass
    
    try:
        from report_generating import ReportGenerator
    except ImportError:
        logger.error("ReportGenerator not found")
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
    # Development mode
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, project_root)
    logger.info("Running in development mode")
    
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
    project_root = os.path.dirname(sys.executable)
else:
    frontend_dir = os.path.join(project_root, 'src', 'frontend')

# Configuration
def ensure_working_directory():
    """Ensure working directory is set correctly when running as PyInstaller bundle"""
    if getattr(sys, 'frozen', False):
        executable_dir = os.path.dirname(sys.executable)
        os.chdir(executable_dir)
        
        app_data_path = os.environ.get('APPDATA', os.path.expanduser('~'))
        temp_dir = os.path.join(app_data_path, 'ECT_Technis', 'temp_uploads')
        return temp_dir
    return None

custom_temp_dir = ensure_working_directory()

if getattr(sys, 'frozen', False):
    app_data_path = os.environ.get('APPDATA', os.path.expanduser('~'))
    temp_dir = custom_temp_dir or os.path.join(app_data_path, 'ECT_Technis', 'temp_uploads')
else:
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

app.config['UPLOAD_FOLDER'] = temp_dir
app.config['MAX_CONTENT_LENGTH'] = config.get('max_file_size_mb', 200) * 1024 * 1024

# Ensure temp directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage for session data
session_data = {
    'base_file_info': None,
    'comp_file_info': [],
    'comparison_settings': None,
    'comparison_results': None,
    'reports': [],
    'site_mappings': {"LE": "Lens", "BGL": "BGL"}
}

@app.route('/health')
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "ECT Technis Backend is running",
        "mode": "PyInstaller" if getattr(sys, 'frozen', False) else "Development"
    })

@app.route('/api/debug-info')
def debug_info():
    if getattr(sys, 'frozen', False):
        docs_dir = os.path.join(sys._MEIPASS, 'docs')
    else:
        docs_dir = os.path.join(project_root, 'docs')
    
    info = {
        'mode': 'PyInstaller' if getattr(sys, 'frozen', False) else 'Development',
        'executable_path': sys.executable if getattr(sys, 'frozen', False) else 'N/A',
        'application_path': getattr(sys, '_MEIPASS', 'N/A'),
        'project_root': project_root,
        'temp_dir': app.config['UPLOAD_FOLDER'],
        'temp_exists': os.path.exists(app.config['UPLOAD_FOLDER']),
        'docs_dir': docs_dir,
        'docs_exists': os.path.exists(docs_dir),
        'cwd': os.getcwd()
    }
    
    return jsonify(info)

@app.route('/api/upload-base-file', methods=['POST'])
def upload_base_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the file
        processor = ExcelProcessor(filepath)
        if processor.load_workbook():
            session_data['base_file_info'] = FileInfo.from_path(filepath, processor.sheet_names)
            logger.info(f"Base file uploaded: {filename}")
            return jsonify({
                'success': True,
                'filename': filename,
                'sheets': processor.sheet_names,
                'message': f'Fichier de base chargé: {filename}'
            })
        else:
            logger.error(f"Failed to process Excel file: {filename}")
            return jsonify({'error': 'Failed to process Excel file'}), 400
            
    except Exception as e:
        logger.exception(f"Error uploading base file: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-comparison-files', methods=['POST'])
def upload_comparison_files():
    try:
        if 'files' not in request.files:
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
                else:
                    logger.error(f"Failed to process comparison file: {filename}")
        
        logger.info(f"Uploaded {len(processed_files)} comparison files")
        return jsonify({
            'success': True,
            'files': processed_files,
            'message': f'{len(processed_files)} fichier(s) de comparaison téléchargé(s)'
        })
        
    except Exception as e:
        logger.exception(f"Error uploading comparison files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-base-file-info')
def get_base_file_info():
    if session_data['base_file_info']:
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
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        processor = ExcelProcessor(filepath)
        if processor.load_workbook():
            processed_data = processor.get_sheet_data(sheet_name, is_base_file=is_base_file)
            processed_preview = processed_data.head(5).fillna('').to_dict('records')
            
            return jsonify({
                'processed_preview': safe_convert(processed_preview),
                'processed_columns': safe_convert(processed_data.columns.tolist())
            })
        else:
            return jsonify({'error': 'Failed to process file'}), 400
            
    except Exception as e:
        logger.exception(f"Error previewing sheet: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-site-mappings', methods=['POST'])
def set_site_mappings():
    try:
        data = request.get_json()
        session_data['site_mappings'] = data.get('mappings', {})
        return jsonify({'success': True})
    except Exception as e:
        logger.exception(f"Error updating site mappings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-site-mappings')
def get_site_mappings():
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
        
        logger.info(f"Starting comparison with {len(selected_sheets)} sheets")
        results = ComparisonEngine.run_comparison(session_data, ExcelProcessor, safe_convert)
        logger.info("Comparison completed")
        
        return jsonify({
            'success': True,
            'results': results
        })
            
    except Exception as e:
        logger.exception(f"Error in comparison: {str(e)}")
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
        logger.info(f"Report saved: {report_id}")
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': f'Rapport enregistré avec ID: {report_id}'
        })
        
    except Exception as e:
        logger.exception(f"Error saving report: {str(e)}")
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

            return send_file(
                temp_file,
                as_attachment=True,
                download_name=filename,
                mimetype=mimetype
            )
            
        except Exception as e:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
            raise e
        
    except Exception as e:
        logger.exception(f"Error exporting report: {str(e)}")
        return jsonify({'error': f'Erreur lors de l\'export: {str(e)}'}), 500

# Serve documentation files
@app.route('/docs/<path:filename>')
def serve_docs(filename):
    """Serve documentation files from docs directory"""
    if getattr(sys, 'frozen', False):
        docs_dir = os.path.join(sys._MEIPASS, 'docs')
    else:
        docs_dir = os.path.join(project_root, 'docs')
    
    if not os.path.exists(docs_dir):
        return jsonify({'error': 'Documentation directory not found'}), 404
    
    try:
        return send_from_directory(docs_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': f'File not found: {filename}'}), 404

@app.route('/docs/legal/<path:filename>')
def serve_legal_docs(filename):
    """Serve legal documentation files"""
    if getattr(sys, 'frozen', False):
        legal_docs_dir = os.path.join(sys._MEIPASS, 'docs', 'legal')
    else:
        legal_docs_dir = os.path.join(project_root, 'docs', 'legal')
    
    try:
        return send_from_directory(legal_docs_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': f'Legal file not found: {filename}'}), 404

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown endpoint"""
    logger.info("Shutdown requested")
    cleanup_and_shutdown()
    return ('', 204)

def cleanup_and_shutdown():
    try:
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

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
    except Exception as e:
        logger.error(f"Error parsing arguments: {e}")
        args = parser.parse_args([])

    if getattr(sys, 'frozen', False):
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

    logger.info(f"Starting Flask server on port {args.port}")
    app.run(
        host='127.0.0.1',
        port=args.port,
        debug=False,
        use_reloader=False,
        threaded=True
    )

if __name__ == '__main__':
    main()