// Comparison page functionality

class ComparisonManager {
    constructor() {
        this.comparisonResults = null;
        this.currentSheet = null;
        this.currentFile = null;
    }
    
    init() {
        this.checkForComparisonResults();
        this.setupEventListeners();
    }
    
    async checkForComparisonResults() {
        try {
            const results = await api.getComparisonResults();
            if (results && results.results) {
                this.comparisonResults = results;
                this.displayResults();
            } else {
                this.showNoDataMessage();
            }
        } catch (error) {
            console.error('Error loading comparison results:', error);
            this.showNoDataMessage();
        }
    }
    
    showNoDataMessage() {
        const content = document.getElementById('comparison-content');
        const noDataDiv = document.getElementById('no-comparison-data');
        if (noDataDiv) {
            noDataDiv.style.display = 'block';
        }
        
        // Hide other sections
        const sections = ['comparison-config-summary', 'comparison-results', 'comparison-actions'];
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });
    }
    
    displayResults() {
        const summary = this.comparisonResults.summary;
        
        // Show results sections
        const sections = ['comparison-results', 'comparison-actions'];
        sections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'block';
        });
        
        // Hide no data message
        const noDataDiv = document.getElementById('no-comparison-data');
        if (noDataDiv) noDataDiv.style.display = 'none';
        
        // Update metrics
        this.updateMetrics(summary);
        
        // Populate sheet selector
        this.populateSheetSelector();
        
        // Display first sheet by default
        const sheets = Object.keys(this.comparisonResults.results);
        if (sheets.length > 0) {
            this.selectSheet(sheets[0]);
        }
    }
    
    updateMetrics(summary) {
        document.getElementById('sheets-compared').textContent = summary.total_sheets_compared || 0;
        document.getElementById('total-differences').textContent = summary.total_differences || 0;
        
        // Calculate match rate
        const cellsCompared = summary.total_cells_compared || 1;
        const differences = summary.total_differences || 0;
        const matchRate = Math.max(0, 100 - ((differences / cellsCompared) * 100));
        document.getElementById('match-rate').textContent = `${matchRate.toFixed(1)}%`;
        
        document.getElementById('processing-time').textContent = `${(summary.execution_time_seconds || 0).toFixed(2)}s`;
    }
    
    populateSheetSelector() {
        const select = document.getElementById('sheet-select');
        if (!select) return;
        
        select.innerHTML = '';
        Object.keys(this.comparisonResults.results).forEach(sheet => {
            const option = document.createElement('option');
            option.value = sheet;
            option.textContent = sheet;
            select.appendChild(option);
        });
    }
    
    selectSheet(sheetName) {
        this.currentSheet = sheetName;
        const sheetResults = this.comparisonResults.results[sheetName];
        
        if (sheetResults && sheetResults.length > 0) {
            // Show file selector if multiple files
            if (sheetResults.length > 1) {
                this.populateFileSelector(sheetResults);
                document.getElementById('file-selector').style.display = 'block';
                this.selectFile(sheetResults[0].comparison_file);
            } else {
                document.getElementById('file-selector').style.display = 'none';
                this.selectFile(sheetResults[0].comparison_file);
            }
        } else {
            this.displayNoSheetData();
        }
    }
    
    populateFileSelector(sheetResults) {
        const select = document.getElementById('file-select');
        if (!select) return;
        
        select.innerHTML = '';
        sheetResults.forEach(result => {
            const option = document.createElement('option');
            option.value = result.comparison_file;
            option.textContent = result.comparison_file;
            select.appendChild(option);
        });
    }
    
    selectFile(fileName) {
        this.currentFile = fileName;
        const sheetResults = this.comparisonResults.results[this.currentSheet];
        const fileResult = sheetResults.find(r => r.comparison_file === fileName);
        
        if (fileResult) {
            this.displaySheetResults(fileResult);
        }
    }
    
    displaySheetResults(result) {
        // Update titles
        document.getElementById('differences-title').textContent = 
            `Différences dans ${this.currentSheet} (${result.comparison_file})`;
        document.getElementById('duplicates-title').textContent = 
            `Doublons dans ${this.currentSheet}`;
        
        // Display differences
        this.displayDifferences(result.differences, result.differences_columns);
        
        // Display duplicates
        this.displayDuplicates(result.duplicates, result.duplicates_columns);
    }
    
    displayDifferences(differences, columns) {
        const content = document.getElementById('differences-content');
        
        if (differences && differences.length > 0) {
            // Translate column names for display
            const translatedColumns = columns.map(col => {
                const translations = {
                    'Key': 'Clé',
                    'Column': 'Colonne',
                    'Base Value': 'Valeur de base',
                    'Comparison Value': 'Valeur de comparaison',
                    'Status': 'Statut'
                };
                return translations[col] || col;
            });
            
            const tableHtml = utils.createTable(differences, translatedColumns, 'data-table differences-table');
            content.innerHTML = `
                <p><strong>${differences.length}</strong> différence(s) trouvée(s)</p>
                ${tableHtml}
            `;
        } else {
            content.innerHTML = `<p class="success-message">Aucune différence trouvée dans la feuille '${this.currentSheet}'</p>`;
        }
    }
    
    displayDuplicates(duplicates, columns) {
        const content = document.getElementById('duplicates-content');
        
        if (duplicates && duplicates.length > 0) {
            const tableHtml = utils.createTable(duplicates, columns, 'data-table duplicates-table');
            content.innerHTML = `
                <p><strong>${duplicates.length}</strong> doublon(s) trouvé(s)</p>
                ${tableHtml}
            `;
        } else {
            content.innerHTML = `<p class="success-message">Aucun doublon trouvé dans la feuille '${this.currentSheet}'</p>`;
        }
    }
    
    displayNoSheetData() {
        document.getElementById('differences-content').innerHTML = 
            `<p>Aucune donnée de comparaison disponible pour la feuille '${this.currentSheet}'</p>`;
        document.getElementById('duplicates-content').innerHTML = 
            `<p>Aucune donnée de comparaison disponible pour la feuille '${this.currentSheet}'</p>`;
    }
    
    setupEventListeners() {
        // Sheet selector
        const sheetSelect = document.getElementById('sheet-select');
        if (sheetSelect) {
            sheetSelect.addEventListener('change', (e) => {
                this.selectSheet(e.target.value);
            });
        }
        
        // File selector
        const fileSelect = document.getElementById('file-select');
        if (fileSelect) {
            fileSelect.addEventListener('change', (e) => {
                this.selectFile(e.target.value);
            });
        }
        
        // Action buttons
        const saveReportBtn = document.getElementById('save-report');
        if (saveReportBtn) {
            saveReportBtn.addEventListener('click', this.saveReport.bind(this));
        }
        
        const newComparisonBtn = document.getElementById('new-comparison');
        if (newComparisonBtn) {
            newComparisonBtn.addEventListener('click', () => {
                app.navigateToPage('upload');
            });
        }
        
        const exportResultsBtn = document.getElementById('export-results');
        if (exportResultsBtn) {
            exportResultsBtn.addEventListener('click', () => {
                app.navigateToPage('reports');
            });
        }
    }
    
    async saveReport() {
        try {
            app.showLoading(true);
            const result = await api.saveReport();
            
            if (result.success) {
                app.showNotification(result.message, 'success');
                
                // Create complete report data for session
                const reportData = {
                    id: result.report_id,
                    date: new Date().toLocaleDateString('fr-FR', {
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                    }),
                    base_file: app.sessionData.baseFileInfo?.filename || 'Fichier de base',
                    comparison_files: app.sessionData.compFilesInfo?.map(f => f.filename) || [],
                    comparison_file: app.sessionData.compFilesInfo?.map(f => f.filename).join(', ') || '',
                    differences: this.comparisonResults?.summary?.total_differences || 0,
                    match_rate: this.calculateMatchRate(),
                    sheets_compared: this.comparisonResults?.summary?.total_sheets_compared || 0
                };
                
                // Update session data
                app.sessionData.reports.push(reportData);
                
                // Navigate to reports page to show the saved report
                setTimeout(() => {
                    app.navigateToPage('reports');
                }, 1000);
                
            } else {
                app.showNotification(result.error || 'Erreur lors de la sauvegarde', 'error');
            }
        } catch (error) {
            console.error('Error saving report:', error);
            app.showNotification('Erreur lors de la sauvegarde du rapport', 'error');
        } finally {
            app.showLoading(false);
        }
    }
    
    calculateMatchRate() {
        if (!this.comparisonResults?.summary) return '0%';
        
        const cellsCompared = this.comparisonResults.summary.total_cells_compared || 1;
        const differences = this.comparisonResults.summary.total_differences || 0;
        const matchRate = Math.max(0, 100 - ((differences / cellsCompared) * 100));
        return `${matchRate.toFixed(1)}%`;
    }
}

// Create global comparison manager instance
window.comparisonManager = new ComparisonManager();
