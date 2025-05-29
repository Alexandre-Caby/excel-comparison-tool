from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import sys
import pandas as pd
import numpy as np
import time
import io
import xlsxwriter
import base64
from datetime import datetime
from werkzeug.utils import secure_filename

# Handle frozen/executable vs development environment
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Development environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Determine if we're running as a frozen executable
if getattr(sys, 'frozen', False):
    # Running as executable
    application_path = os.path.dirname(sys.executable)
    project_root = sys._MEIPASS
    frontend_dir = os.path.join(project_root, 'src', 'frontend')
    
    # Add the bundled src directory to Python path
    sys.path.insert(0, os.path.join(project_root, 'src'))
    
else:
    # Running in development
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    application_path = project_root
    frontend_dir = os.path.join(project_root, 'src', 'frontend')
    
    # Add the project root to the Python path
    sys.path.insert(0, project_root)

# Import configuration and existing modules with fallback handling
try:
    if getattr(sys, 'frozen', False):
        # Frozen executable - use simpler imports
        from core.comparison_engine import ComparisonEngine
        from core.excel_processor import ExcelProcessor
        from core.site_matcher import SiteMatcher
        from models.data_models import FileInfo, ComparisonSummary
        from utils.config import config
    else:
        # Development environment
        from src.utils.config import config
        from src.core.comparison_engine import ComparisonEngine
        from src.core.excel_processor import ExcelProcessor
        from src.core.site_matcher import SiteMatcher
        from src.models.data_models import FileInfo, ComparisonSummary
        
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Frozen state: {getattr(sys, 'frozen', False)}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    
    # Fallback for missing modules - create basic implementations
    class SimpleConfig:
        def get(self, key, default=None):
            defaults = {
                'temp_dir': 'temp',
                'max_file_size_mb': 200,
                'app_name': 'Excel Comparison Tool',
                'version': '1.0.0',
                'logging.level': 'INFO',
                'logging.format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'logging.file': 'app.log'
            }
            return defaults.get(key, default)
    
    config = SimpleConfig()
    
    # Create placeholder classes if modules are missing
    class ComparisonEngine:
        def find_differences(self, *args, **kwargs):
            return pd.DataFrame()
        def find_duplicates(self, *args, **kwargs):
            return pd.DataFrame()
    
    class ExcelProcessor:
        def __init__(self, filepath):
            self.filepath = filepath
            self.sheet_names = []
        def load_workbook(self):
            return False
        def get_sheet_data(self, *args, **kwargs):
            return pd.DataFrame()
        def get_sheet_preview(self, *args, **kwargs):
            return pd.DataFrame()
    
    class SiteMatcher:
        def set_site_mappings(self, mappings):
            pass
    
    class FileInfo:
        def __init__(self, file_path, file_name, sheet_names):
            self.file_path = file_path
            self.file_name = file_name
            self.sheet_names = sheet_names
        
        @classmethod
        def from_path(cls, filepath, sheet_names):
            return cls(filepath, os.path.basename(filepath), sheet_names)

app = Flask(__name__)
CORS(app)

# Configuration - Use paths appropriate for frozen/development
if getattr(sys, 'frozen', False):
    # Frozen executable - use temp directory relative to executable
    temp_dir = os.path.join(os.path.dirname(sys.executable), 'temp')
else:
    # Development - use backend temp directory
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')

app.config['UPLOAD_FOLDER'] = temp_dir
app.config['MAX_CONTENT_LENGTH'] = config.get('max_file_size_mb', 200) * 1024 * 1024

# Frontend directory for serving static files during development
# frontend_dir = os.path.join(project_root, 'src', 'frontend')

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

# Serve frontend files for development (Electron will handle this in production)
@app.route('/')
def serve_frontend():
    return send_from_directory(frontend_dir, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    try:
        return send_from_directory(frontend_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "app_name": config.get('app_name'),
        "version": config.get('version'),
        "upload_folder": app.config['UPLOAD_FOLDER'],
        "frontend_dir": frontend_dir
    }), 200

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
            return jsonify({'error': 'File not found'}), 404
        
        processor = ExcelProcessor(filepath)
        if processor.load_workbook():
            # Get raw preview
            raw_preview = processor.get_sheet_preview(sheet_name)
            raw_data = raw_preview.head(10).fillna('').to_dict('records')
            
            # Get processed data
            processed_data = processor.get_sheet_data(sheet_name, is_base_file=is_base_file)
            processed_preview = processed_data.head(5).fillna('').to_dict('records')
            
            return jsonify({
                'raw_preview': raw_data,
                'raw_columns': raw_preview.columns.tolist(),
                'processed_preview': processed_preview,
                'processed_columns': processed_data.columns.tolist()
            })
        else:
            return jsonify({'error': 'Failed to process file'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set-site-mappings', methods=['POST'])
def set_site_mappings():
    try:
        data = request.get_json()
        session_data['site_mappings'] = data.get('mappings', {})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-site-mappings')
def get_site_mappings():
    return jsonify({'mappings': session_data['site_mappings']})

@app.route('/api/start-comparison', methods=['POST'])
def start_comparison():
    try:
        data = request.get_json()
        selected_sheets = data.get('selected_sheets', [])
        
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
            'site_column': 'A',
            'column_indices': list(range(1, 10))
        }
        
        # Run comparison
        results = run_comparison()
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_comparison():
    settings = session_data['comparison_settings']
    
    site_matcher = SiteMatcher()
    comparison_engine = ComparisonEngine()
    site_matcher.set_site_mappings(settings['site_mappings'])
    
    all_results = {}
    start_time = time.time()
    total_differences_count = 0
    total_duplicates_count = 0
    total_comparable_cells = 0
    
    # Process each selected sheet
    for sheet_name in settings['selected_sheets']:
        sheet_results = []
        
        # Load base file data
        base_processor = ExcelProcessor(settings['base_file'].file_path)
        if not base_processor.load_workbook():
            continue
            
        base_data = base_processor.get_sheet_data(sheet_name, is_base_file=True)
        if base_data.empty:
            all_results[sheet_name] = []
            continue
        
        # Find duplicates in base data
        base_dupes = comparison_engine.find_duplicates(base_data, ["Locomotive", "CodeOp"])
        total_duplicates_count += len(base_dupes)
        
        # Process each comparison file
        for comp_file_info in settings['comparison_files']:
            comp_processor = ExcelProcessor(comp_file_info.file_path)
            if not comp_processor.load_workbook():
                continue
                
            if not comp_processor.sheet_names:
                continue
                
            comp_sheet_name = comp_processor.sheet_names[0]
            comp_data = comp_processor.get_sheet_data(comp_sheet_name, is_base_file=False)
            
            if comp_data.empty:
                continue
                
            # Filter comparison data by site
            site_codes = list(settings['site_mappings'].keys())
            if site_codes:
                filtered_comp_data = comp_data[comp_data["Site"].str.contains(
                    site_codes[0], case=False, na=False)]
            else:
                filtered_comp_data = comp_data
            
            if filtered_comp_data.empty:
                continue
                
            # Calculate comparable cells
            value_cols = ["Commentaire", "Date Butee", "Date programmation", "Heure programmation", "Date sortie", "Heure sortie"]
            total_comparable_cells += len(base_data) * len(value_cols)
            
            # Find differences
            differences = comparison_engine.find_differences(
                base_data,
                filtered_comp_data,
                key_columns=["Locomotive", "CodeOp"],
                value_columns=value_cols
            )
            
            # Convert DataFrames to serializable format
            file_result = {
                "comparison_file": comp_file_info.file_name,
                "differences": differences.fillna('').to_dict('records'),
                "differences_columns": differences.columns.tolist(),
                "duplicates": base_dupes.fillna('').to_dict('records'),
                "duplicates_columns": base_dupes.columns.tolist(),
                "base_rows": len(base_data),
                "comp_rows": len(filtered_comp_data)
            }
            
            sheet_results.append(file_result)
            total_differences_count += len(differences)
        
        all_results[sheet_name] = sheet_results
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Create summary
    summary = {
        'total_sheets_compared': len(settings['selected_sheets']),
        'total_rows_compared': 0,
        'total_cells_compared': total_comparable_cells if total_comparable_cells > 0 else 1,
        'total_differences': total_differences_count,
        'total_duplicates': total_duplicates_count,
        'execution_time_seconds': execution_time
    }
    
    # Store results
    session_data['comparison_results'] = {
        "results": all_results,
        "summary": summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return {
        "results": all_results,
        "summary": summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

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
        match_rate = max(0, 100 - ((diffs / cells_compared) * 100))
        
        comp_files = [f.file_name for f in settings['comparison_files']]
        
        report = {
            "id": report_id,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "base_file": settings['base_file'].file_name,
            "comparison_files": comp_files,
            "comparison_file": ", ".join(comp_files),
            "differences": summary['total_differences'],
            "match_rate": f"{match_rate:.1f}%"
        }
        
        session_data['reports'].append(report)
        
        return jsonify({
            'success': True,
            'report_id': report_id,
            'message': f'Rapport enregistré avec ID: {report_id}'
        })
        
    except Exception as e:
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
        
        # Find the report
        report = next((r for r in session_data['reports'] if r['id'] == report_id), None)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        if format_type == 'excel':
            # Generate Excel report
            excel_buffer = generate_excel_report(report)
            
            # Return the file
            return send_file(
                excel_buffer,
                as_attachment=True,
                download_name=f"ECT_Technis_Report_{report_id}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        
        elif format_type == 'csv':
            # Generate CSV - simplified version
            if session_data['comparison_results']:
                results = session_data['comparison_results']['results']
                # Get first sheet with differences
                for sheet_name, sheet_results in results.items():
                    for result in sheet_results:
                        if result['differences']:
                            df = pd.DataFrame(result['differences'])
                            csv_buffer = io.StringIO()
                            df.to_csv(csv_buffer, index=False)
                            csv_buffer.seek(0)
                            
                            return send_file(
                                io.BytesIO(csv_buffer.getvalue().encode()),
                                as_attachment=True,
                                download_name=f"ECT_Technis_Report_{report_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                                mimetype='text/csv'
                            )
        
        return jsonify({'error': 'No data to export'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def generate_excel_report(report_data):
    """Generate an Excel report with the comparison results"""
    output = io.BytesIO()
    
    with xlsxwriter.Workbook(output) as workbook:
        # Add summary worksheet
        summary_ws = workbook.add_worksheet("Résumé")
        
        # Add formatting
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#007147',
            'font_color': 'white'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#4CA27E',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = workbook.add_format({'border': 1})
        
        # Add title
        summary_ws.merge_range('A1:G1', 'Rapport de Comparaison Excel', title_format)
        
        # Add report information
        summary_ws.write('A3', 'Rapport ID:', header_format)
        summary_ws.write('B3', report_data["id"], cell_format)
        
        summary_ws.write('A4', 'Date:', header_format)
        summary_ws.write('B4', report_data["date"], cell_format)
        
        summary_ws.write('A5', 'Fichier de base:', header_format)
        summary_ws.write('B5', report_data["base_file"], cell_format)
        
        summary_ws.write('A6', 'Fichiers de comparaison:', header_format)
        summary_ws.write('B6', report_data["comparison_file"], cell_format)
        
        summary_ws.write('A7', 'Différences trouvées:', header_format)
        summary_ws.write('B7', report_data["differences"], cell_format)
        
        summary_ws.write('A8', 'Taux de correspondance:', header_format)
        summary_ws.write('B8', report_data["match_rate"], cell_format)
        
        # Set column widths
        summary_ws.set_column('A:A', 20)
        summary_ws.set_column('B:B', 40)
    
    output.seek(0)
    return output

# Serve documentation files with frozen-aware paths
@app.route('/docs/<path:filename>')
def serve_docs(filename):
    if getattr(sys, 'frozen', False):
        docs_dir = os.path.join(project_root, 'docs')
    else:
        docs_dir = os.path.join(project_root, 'docs')
    
    try:
        return send_from_directory(docs_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Documentation file not found'}), 404

@app.route('/docs/legal/<path:filename>')
def serve_legal_docs(filename):
    if getattr(sys, 'frozen', False):
        legal_docs_dir = os.path.join(project_root, 'docs', 'legal')
    else:
        legal_docs_dir = os.path.join(project_root, 'docs', 'legal')
    
    try:
        return send_from_directory(legal_docs_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Legal document not found'}), 404

if __name__ == '__main__':
    # Set up logging with frozen-aware paths
    import logging
    
    # Create logs directory if it doesn't exist
    if getattr(sys, 'frozen', False):
        log_file = os.path.join(os.path.dirname(sys.executable), 'app.log')
    else:
        log_file = config.get('logging.file', 'app.log')
    
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, config.get('logging.level', 'INFO')),
        format=config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    print(f"Starting {config.get('app_name', 'Excel Comparison Tool')} v{config.get('version', '1.0.0')}")
    print(f"Frozen state: {getattr(sys, 'frozen', False)}")
    print(f"Application path: {application_path}")
    print(f"Project root: {project_root}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Frontend directory: {frontend_dir}")

    if getattr(sys, 'frozen', False):
        try:
            from waitress import serve
            import webbrowser
            import threading
            
            def open_browser():
                time.sleep(1.5)  # Give the server time to start
                webbrowser.open('http://localhost:5000')
            
            threading.Thread(target=open_browser).start()
            
            print("Server starting in production mode on http://localhost:5000")
            serve(app, host='localhost', port=5000)
        except ImportError:
            print("Waitress not available, falling back to Flask development server")
            app.run(debug=False, port=5000, host='localhost')
    else:
        # Development mode
        print("Server starting in development mode on http://localhost:5000")
        print("You can test the frontend at: http://localhost:5000")
        app.run(debug=True, port=5000, host='localhost')
