// Reports page functionality

class ReportsManager {
    constructor() {
        this.reports = [];
        this.selectedReport = null;
    }
    
    init() {
        this.loadReports();
        this.setupEventListeners();
    }
    
    async loadReports() {
        try {
            const result = await api.getReports();
            if (result.reports) {
                this.reports = result.reports;
                this.displayReports();
            } else {
                this.showNoReportsMessage();
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            this.showNoReportsMessage();
        }
    }
    
    displayReports() {
        const content = document.getElementById('reports-content');
        
        if (this.reports.length === 0) {
            this.showNoReportsMessage();
            return;
        }
        
        let html = `
            <h2>Rapports disponibles</h2>
            <div class="reports-table-container">
                ${this.createReportsTable()}
            </div>
            
            <div class="report-selector">
                <label for="report-select">Sélectionnez un rapport à visualiser ou exporter:</label>
                <select id="report-select">
                    <option value="">-- Sélectionner un rapport --</option>
                    ${this.reports.map(report => 
                        `<option value="${report.id}">${report.id} - ${report.base_file} vs ${report.comparison_file}</option>`
                    ).join('')}
                </select>
            </div>
            
            <div id="report-details" class="report-details" style="display: none;">
                <!-- Report details will be populated here -->
            </div>
        `;
        
        content.innerHTML = html;
    }
    
    createReportsTable() {
        const columns = ['ID', 'Date', 'Fichier de base', 'Fichiers de comparaison', 'Différences', 'Taux de correspondance'];
        const data = this.reports.map(report => ({
            'ID': report.id,
            'Date': report.date,
            'Fichier de base': report.base_file,
            'Fichiers de comparaison': report.comparison_file || report.comparison_files?.join(', ') || '',
            'Différences': report.differences,
            'Taux de correspondance': report.match_rate
        }));
        
        return utils.createTable(data, columns, 'data-table reports-table');
    }
    
    showNoReportsMessage() {
        const content = document.getElementById('reports-content');
        content.innerHTML = `
            <div class="info-box">
                <h3>Aucun rapport disponible</h3>
                <p>Effectuez une comparaison pour générer des rapports.</p>
                <button class="btn primary-btn" onclick="app.navigateToPage('upload')">
                    Aller à la page de téléchargement
                </button>
            </div>
        `;
    }
    
    setupEventListeners() {
        // Report selector change
        document.addEventListener('change', (e) => {
            if (e.target.id === 'report-select') {
                const reportId = e.target.value;
                if (reportId) {
                    this.selectReport(reportId);
                } else {
                    this.hideReportDetails();
                }
            }
        });
        
        // Export format change
        document.addEventListener('change', (e) => {
            if (e.target.id === 'export-format') {
                this.updateFileName();
            }
        });
        
        // Export button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'export-report-btn') {
                this.exportReport();
            }
        });
    }
    
    selectReport(reportId) {
        this.selectedReport = this.reports.find(r => r.id === reportId);
        if (this.selectedReport) {
            this.displayReportDetails();
        }
    }
    
    displayReportDetails() {
        const detailsDiv = document.getElementById('report-details');
        if (!detailsDiv || !this.selectedReport) return;
        
        const compFiles = this.selectedReport.comparison_files || 
                         (this.selectedReport.comparison_file ? this.selectedReport.comparison_file.split(', ') : []);
        
        detailsDiv.innerHTML = `
            <h3>Détails du rapport</h3>
            
            <div class="report-summary">
                <h4>Résumé</h4>
                <div class="summary-metrics">
                    <div class="metric-card">
                        <div class="metric-value">${this.selectedReport.differences}</div>
                        <div class="metric-label">Différences trouvées</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${this.selectedReport.match_rate}</div>
                        <div class="metric-label">Taux de correspondance</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${compFiles.length}</div>
                        <div class="metric-label">Fichiers de comparaison</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${this.selectedReport.date}</div>
                        <div class="metric-label">Généré le</div>
                    </div>
                </div>
            </div>
            
            <div class="export-section">
                <h4>Exporter le rapport</h4>
                <div class="export-controls">
                    <div class="export-format">
                        <label>Format d'exportation:</label>
                        <div class="radio-group">
                            <label>
                                <input type="radio" name="export-format" value="excel" id="export-format" checked>
                                Excel (.xlsx)
                            </label>
                            <label>
                                <input type="radio" name="export-format" value="csv">
                                CSV (.csv)
                            </label>
                        </div>
                    </div>
                    
                    <div class="filename-input">
                        <label for="export-filename">Nom du fichier:</label>
                        <input type="text" id="export-filename" 
                               value="ECT_Technis_Report_${this.selectedReport.id}_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx">
                    </div>
                    
                    <button class="btn primary-btn" id="export-report-btn">
                        Exporter
                    </button>
                </div>
            </div>
        `;
        
        detailsDiv.style.display = 'block';
    }
    
    hideReportDetails() {
        const detailsDiv = document.getElementById('report-details');
        if (detailsDiv) {
            detailsDiv.style.display = 'none';
        }
    }
    
    updateFileName() {
        const formatRadios = document.querySelectorAll('input[name="export-format"]');
        const filenameInput = document.getElementById('export-filename');
        
        if (!filenameInput || !this.selectedReport) return;
        
        const selectedFormat = Array.from(formatRadios).find(r => r.checked)?.value || 'excel';
        const extension = selectedFormat === 'excel' ? 'xlsx' : 'csv';
        const baseName = `ECT_Technis_Report_${this.selectedReport.id}_${new Date().toISOString().slice(0,10).replace(/-/g,'')}`;
        
        filenameInput.value = `${baseName}.${extension}`;
    }
    
    async exportReport() {
        if (!this.selectedReport) {
            app.showNotification('Aucun rapport sélectionné', 'warning');
            return;
        }
        
        const formatRadios = document.querySelectorAll('input[name="export-format"]');
        const selectedFormat = Array.from(formatRadios).find(r => r.checked)?.value || 'excel';
        
        try {
            app.showLoading(true);
            
            await api.exportReport(this.selectedReport.id, selectedFormat);
            app.showNotification('Rapport exporté avec succès', 'success');
            
        } catch (error) {
            console.error('Error exporting report:', error);
            app.showNotification('Erreur lors de l\'exportation du rapport', 'error');
        } finally {
            app.showLoading(false);
        }
    }
}

// Create global reports manager instance
window.reportsManager = new ReportsManager();
