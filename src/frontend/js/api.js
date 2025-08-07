// API communication module

class API {
    constructor() {
        this.baseURL = 'http://localhost:5000';
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const finalOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, finalOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return response;
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    // Health check
    async healthCheck() {
        return this.request('/health');
    }
    
    // File upload methods
    async uploadBaseFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        return this.request('/api/upload-base-file', {
            method: 'POST',
            body: formData,
            headers: {} // Remove Content-Type to let browser set boundary
        });
    }
    
    async uploadComparisonFiles(files) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        
        return this.request('/api/upload-comparison-files', {
            method: 'POST',
            body: formData,
            headers: {} // Remove Content-Type to let browser set boundary
        });
    }
    
    // File info methods
    async getBaseFileInfo() {
        return this.request('/api/get-base-file-info');
    }
    
    async getComparisonFilesInfo() {
        return this.request('/api/get-comparison-files-info');
    }
    
    // Preview methods
    async previewSheet(filename, sheetName, isBaseFile = false, fileType = null) {
        return this.request('/api/preview-sheet', {
            method: 'POST',
            body: JSON.stringify({
                filename,
                sheet_name: sheetName,
                is_base_file: isBaseFile,
                file_type: fileType
            })
        });
    }

    // Site mappings
    async setSiteMappings(mappings) {
        return this.request('/api/set-site-mappings', {
            method: 'POST',
            body: JSON.stringify({ mappings })
        });
    }
    
    async getSiteMappings() {
        return this.request('/api/get-site-mappings');
    }
    
    // Comparison methods
    async startComparison(selectedSheets, comparisonMode = 'full', useDynamicDetection = true) { 
        return this.request('/api/start-comparison', {
            method: 'POST',
            body: JSON.stringify({ 
                selected_sheets: selectedSheets, 
                comparison_mode: comparisonMode,
                use_dynamic_detection: useDynamicDetection
            })
        });
    }
    
    async getComparisonResults() {
        return this.request('/api/get-comparison-results');
    }

    // Analysis methods
    async startPHPAnalysis(filename, sheetName, analysisOptions) {
        return this.request('/api/start-php-analysis', {
            method: 'POST',
            body: JSON.stringify({
                filename: filename,
                sheet_name: sheetName,
                analysis_options: analysisOptions
            })
        });
    }

    async getAnalysisResults() {
        return this.request('/api/get-analysis-results');
    }

    async exportAnalysis(format, filename, exportOptions) {
        const response = await fetch(`${this.baseURL}/api/export-analysis`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format: format,
                filename: filename,
                export_options: exportOptions
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Export failed');
        }
        
        return response.blob();
    }

    // Keep legacy method for backward compatibility
    async exportPHPAnalysis(format, filename, exportOptions) {
        return this.exportAnalysis(format, filename, exportOptions);
    }

    // Reports methods
    async saveReport() {
        return this.request('/api/save-report', {
            method: 'POST'
        });
    }
    
    async getReports() {
        return this.request('/api/get-reports');
    }

    async exportReport(reportId, format, filename) {
        console.log(`Exporting report ${reportId} in ${format} format`);
        const response = await this.request('/api/export-report', {
            method: 'POST',
            body: JSON.stringify({
                report_id: reportId,
                format: format,
                filename: filename
            })
        });
        
        // Handle file download
        if (response instanceof Response) {
            const blob = await response.blob();
            this.downloadBlob(blob, filename, format);
        }
        
        return response;
    }

    // Helper method for downloading blobs
    downloadBlob(blob, filename, format) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Determine file extension
        const extensionMap = {
            'excel': 'xlsx',
            'csv': 'csv', 
            'pdf': 'pdf'
        };
        
        const extension = extensionMap[format] || 'xlsx';
        a.download = filename.endsWith(`.${extension}`) ? filename : `${filename}.${extension}`;
        
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    // Generic export method for future extensibility
    async exportData(exportType, options) {
        const endpoint = exportType === 'comparison' ? '/api/export-report' : '/api/export-analysis';
        
        const response = await fetch(`${this.baseURL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(options)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Export failed');
        }
        
        return response.blob();
    }
}

// Create global API instance
window.api = new API();
