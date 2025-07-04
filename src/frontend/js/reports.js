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
                this.populateReportSelect();
                this.hideNoReportsMessage();
            } else {
                this.showNoReportsMessage();
            }
        } catch (error) {
            console.error('Error loading reports:', error);
            this.showNoReportsMessage();
        }
    }
    
    populateReportSelect() {
        const select = document.getElementById('report-select');
        if (!select) return;

        select.innerHTML = '<option value="">Sélectionner un rapport...</option>';

        this.reports.forEach(report => {
            const files = report.comparison_files || [];
            let displayFiles = files.slice(0, 2).join(', ');
            if (files.length > 2) {
                displayFiles += ` ... (+${files.length - 2} autres)`;
            }
            const option = document.createElement('option');
            option.value = report.id;
            option.textContent = `${report.id} - ${report.base_file} vs ${displayFiles} (${report.date})`;
            select.appendChild(option);
        });

        if (this.reports.length === 0) {
            const option = document.createElement('option');
            option.textContent = 'Aucun rapport disponible';
            option.disabled = true;
            select.appendChild(option);
        }
    }
    
    showNoReportsMessage() {
        const noReportsDiv = document.getElementById('no-reports');
        const reportContent = document.getElementById('report-content');
        
        if (noReportsDiv) noReportsDiv.style.display = 'block';
        if (reportContent) reportContent.style.display = 'none';
    }
    
    hideNoReportsMessage() {
        const noReportsDiv = document.getElementById('no-reports');
        if (noReportsDiv) noReportsDiv.style.display = 'none';
    }
    
    setupEventListeners() {
        // Report selector change - enable/disable load button
        document.addEventListener('change', (e) => {
            if (e.target.id === 'report-select') {
                const loadBtn = document.getElementById('load-report-btn');
                if (loadBtn) {
                    loadBtn.disabled = !e.target.value;
                }
            }
        });
        
        // Load report button
        document.addEventListener('click', (e) => {
            if (e.target.id === 'load-report-btn') {
                const select = document.getElementById('report-select');
                if (select && select.value) {
                    this.selectReport(select.value);
                }
            }
        });
        
        // Export format change
        document.addEventListener('change', (e) => {
            if (e.target.name === 'export-format') {
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
        // console.log('Selecting report:', reportId);
        
        this.selectedReport = this.reports.find(r => r.id === reportId);
        if (this.selectedReport) {
            // console.log('Selected report data:', this.selectedReport);
            this.displayReportDetails();
            this.showReportContent();
        } else {
            // console.error('Report not found:', reportId);
            app.showNotification('Rapport non trouvé', 'error');
        }
    }
    
    showReportContent() {
        const reportContent = document.getElementById('report-content');
        if (reportContent) {
            reportContent.style.display = 'block';
        }
    }
    
    displayReportDetails() {
        if (!this.selectedReport) {
            // console.error('No report selected');
            return;
        }
        
        // Update summary metrics
        this.updateSummaryMetrics();
        
        // Update detailed table
        this.updateDetailedTable();
        
        // Update export filename
        this.updateFileName();
    }
    
    updateSummaryMetrics() {
        const report = this.selectedReport;
        
        // Update metric values
        const elements = {
            'report-sheets': report.sheets_compared || report.sheets || this.getSheetCount(report),
            'report-differences': report.differences || report.total_differences || '0',
            'report-duplicates': report.duplicates || report.total_duplicates || '0', 
            'report-date': this.formatDate(report.date) || '-'
        };
        
        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
                // console.log(`Updated ${id}:`, elements[id]);
            }
        });
    }
    
    getSheetCount(report) {
        // Try to determine sheet count from various possible properties
        if (report.comparison_files) {
            return report.comparison_files.length + 1; // +1 for base file
        }
        if (report.comparison_file) {
            return report.comparison_file.includes(',') ? 
                   report.comparison_file.split(',').length + 1 : 2;
        }
        return 1;
    }
    
    updateDetailedTable() {
        const tableContent = document.getElementById('report-table-content');
        const detailedSection = document.getElementById('detailed-data-section');
        const summaryTable = document.getElementById('report-summary-table');
        const report = this.selectedReport;

        // Determine comparison mode (default to 'full' if not present)
        const mode = report.comparison_mode || 'full';

        let html = '';
        let hasDetails = false;

        // Show differences if mode is 'full' or 'differences-only'
        if ((mode === 'full' || mode === 'differences-only') &&
            report.details && Array.isArray(report.details) && report.details.length > 0) {
            hasDetails = true;
            const columns = report.columns || this.getDefaultColumns(report.details[0]);
            html += `<h4>Différences</h4>`;
            html += utils.createTable(report.details, columns, 'data-table report-details-table');
        }

        if (mode === 'full' &&
            report.duplicates_details && Array.isArray(report.duplicates_details) && report.duplicates_details.length > 0) {
            hasDetails = true;
            const dupColumns = report.duplicates_columns || this.getDefaultColumns(report.duplicates_details[0]);
            html += `<h4>Doublons détectés</h4>`;
            html += utils.createTable(report.duplicates_details, dupColumns, 'data-table report-duplicates-table');
        }

        if (hasDetails) {
            if (detailedSection) detailedSection.style.display = 'block';
            if (summaryTable) summaryTable.innerHTML = '';
            if (tableContent) tableContent.innerHTML = html;
        } else {
            if (detailedSection) detailedSection.style.display = 'none';
            if (summaryTable) summaryTable.innerHTML = this.createSummaryTable(report);
        }
    }
        
    getDefaultColumns(dataRow) {
        if (!dataRow || typeof dataRow !== 'object') {
            return ['Information', 'Valeur'];
        }
        return Object.keys(dataRow);
    }
    
    createSummaryTable(report) {
        let files = report.comparison_files || [];
        let displayFiles = files.slice(0, 2).join(', ');
        if (files.length > 2) {
            displayFiles += ` ... (+${files.length - 2} autres)`;
        }
        const summaryInfo = [
            { 'Information': 'ID du rapport', 'Valeur': report.id },
            { 'Information': 'Fichier de base', 'Valeur': report.base_file || '-' },
            { 'Information': 'Fichier(s) de comparaison', 'Valeur': displayFiles || '-' },
            { 'Information': 'Différences trouvées', 'Valeur': report.differences || '0' },
            { 'Information': 'Doublons détectés', 'Valeur': report.duplicates || '0' },
            { 'Information': 'Taux de correspondance', 'Valeur': report.match_rate || '-' },
            { 'Information': 'Date de génération', 'Valeur': report.date || '-' }
        ];
        return utils.createTable(summaryInfo, ['Information', 'Valeur'], 'data-table summary-table');
    }
    
    formatDate(dateString) {
        if (!dateString) return null;
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return dateString; // Return original if parsing fails
        }
    }
    
    updateFileName() {
        const formatRadios = document.querySelectorAll('input[name="export-format"]');
        const filenameInput = document.getElementById('export-filename');
        
        if (!filenameInput || !this.selectedReport) return;
        
        const selectedFormat = Array.from(formatRadios).find(r => r.checked)?.value || 'excel';
        let extension;
        
        switch(selectedFormat) {
            case 'excel':
                extension = 'xlsx';
                break;
            case 'csv':
                extension = 'csv';
                break;
            case 'pdf':
                extension = 'pdf';
                break;
            default:
                extension = 'xlsx';
        }
        
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
        const filenameInput = document.getElementById('export-filename');
        const desiredFilename = filenameInput ? filenameInput.value : '';
        
        try {
            let loadingMessage = 'Export en cours...';
            switch(selectedFormat) {
                case 'excel':
                    loadingMessage = 'Génération du fichier Excel...';
                    break;
                case 'csv':
                    loadingMessage = 'Génération du fichier CSV...';
                    break;
                case 'pdf':
                    loadingMessage = 'Génération du fichier PDF...';
                    break;
            }
            
            app.showLoading(true, loadingMessage);
            
            await api.exportReport(this.selectedReport.id, selectedFormat, desiredFilename);
            
            let successMessage = 'Rapport exporté avec succès';
            switch(selectedFormat) {
                case 'excel':
                    successMessage = 'Rapport Excel exporté avec succès';
                    break;
                case 'csv':
                    successMessage = 'Rapport CSV exporté avec succès';
                    break;
                case 'pdf':
                    successMessage = 'Rapport PDF exporté avec succès';
                    break;
            }
            
            app.showNotification(successMessage, 'success');
            
        } catch (error) {
            console.error('Error exporting report:', error);
            app.showNotification(`Erreur lors de l'exportation du rapport ${selectedFormat.toUpperCase()}`, 'error');
        } finally {
            app.showLoading(false);
        }
    }
}

// Create global reports manager instance
window.reportsManager = new ReportsManager();