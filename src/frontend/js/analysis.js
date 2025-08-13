class AnalysisManager {
    constructor() {
        this.currentFile = null;
        this.currentSheet = null;
        this.analysisResults = null;
        this.concatenatedData = [];
        this.conflicts = [];
    }

    init() {
        this.setupEventListeners();
        this.setupInfoToggle();
        this.resetForm();
    }

    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('analysis-file-input');
        const fileArea = document.getElementById('analysis-file-area');

        if (fileInput && fileArea) {
            fileArea.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e.target.files[0]));
            
            // Drag and drop
            fileArea.addEventListener('dragover', this.handleDragOver.bind(this));
            fileArea.addEventListener('drop', this.handleDrop.bind(this));
        }

        // Sheet selection
        const sheetSelect = document.getElementById('analysis-sheet-select');
        if (sheetSelect) {
            sheetSelect.addEventListener('change', () => this.onSheetChange());
        }

        // Analysis buttons
        const startBtn = document.getElementById('start-analysis-btn');
        const resetBtn = document.getElementById('reset-analysis-btn');
        const exportBtn = document.getElementById('export-analysis-btn');

        if (startBtn) startBtn.addEventListener('click', () => this.startPHPAnalysis());
        if (resetBtn) resetBtn.addEventListener('click', () => this.resetForm());
        if (exportBtn) exportBtn.addEventListener('click', () => this.exportPHPAnalysis());

        // Filter controls
        const applyFilterBtn = document.getElementById('apply-concat-filter');
        const clearFilterBtn = document.getElementById('clear-concat-filter');

        if (applyFilterBtn) applyFilterBtn.addEventListener('click', () => this.applyConcatFilter());
        if (clearFilterBtn) clearFilterBtn.addEventListener('click', () => this.clearConcatFilter());
    }

    // Event handlers and utility methods omitted for brevity
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileUpload(files[0]);
        }
    }

    async handleFileUpload(file) {
        if (!file) return;

        if (!this.isValidExcelFile(file)) {
            alert('Veuillez sélectionner un fichier Excel valide (.xlsx ou .xls)');
            return;
        }

        try {
            const response = await api.uploadBaseFile(file);

            if (response.success) {
                this.currentFile = {
                    filename: response.filename,
                    sheets: response.sheets
                };
                
                this.displayFileInfo(response);
                this.populateSheetSelector(response.sheets);
                this.enableAnalysisControls();
                
                app.showNotification('Fichier chargé avec succès', 'success');
            }
        } catch (error) {
            console.error('Upload error:', error);
            app.showNotification('Erreur lors du téléchargement du fichier', 'error');
        }
    }

    isValidExcelFile(file) {
        const validTypes = ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        const validExtensions = ['.xlsx', '.xls'];
        
        // Check MIME type
        if (validTypes.includes(file.type)) return true;
        
        // Check file extension as fallback
        const fileName = file.name.toLowerCase();
        return validExtensions.some(ext => fileName.endsWith(ext));
    }

    displayFileInfo(info) {
        const infoDiv = document.getElementById('analysis-file-info');
        const detailsDiv = document.getElementById('analysis-file-details');
        
        detailsDiv.innerHTML = `
            <div class="file-item">
                <p><strong>Fichier:</strong> ${info.filename}</p>
                <p><strong>Feuilles trouvées:</strong> ${info.sheets.length}</p>
                <p><strong>Feuilles:</strong> ${info.sheets.join(', ')}</p>
            </div>
        `;
        
        infoDiv.style.display = 'block';
    }

    populateSheetSelector(sheets) {
        const select = document.getElementById('analysis-sheet-select');
        const container = document.getElementById('analysis-sheet-selection');
        
        if (select && sheets) {
            select.innerHTML = '<option value="">Sélectionner une feuille...</option>';
            sheets.forEach(sheet => {
                const option = document.createElement('option');
                option.value = sheet;
                option.textContent = sheet;
                select.appendChild(option);
            });
            
            container.style.display = 'block';
        }
    }

    onSheetChange() {
        const select = document.getElementById('analysis-sheet-select');
        this.currentSheet = select.value;
        this.updateAnalysisButtonState();
        
        if (this.currentSheet) {
            this.loadSheetPreview();
        }
    }

     async loadSheetPreview() {
        try {
            if (this.currentFile.filename && this.currentSheet) {
                this.enableAnalysisControls();
                
                const previewData = await api.previewSheet(
                    this.currentFile.filename,
                    this.currentSheet,
                    true,
                    'analysis'
                );
                
                this.populateWeekSelectionFromColumn(previewData);
            }
        } catch (error) {
            console.error('Error preparing analysis:', error);
        }
    }

    populateWeekSelectionFromColumn(data) {
        const weekSelect = document.getElementById('analysis-week');
        const weekDetectionInfo = document.getElementById('week-detection-info');
        
        if (!weekSelect || !data) return;
        
        try {
            let weeks = new Set();
            
            if (data.unique_weeks && Array.isArray(data.unique_weeks)) {
                data.unique_weeks.forEach(week => {
                    if (week && week.trim() !== '') {
                        weeks.add(week.trim());
                    }
                });
            } else {
                const weekColumn = 'N° Semaine Ou Reliquat';
                
                if (!data.processed_columns.includes(weekColumn)) {
                    weekSelect.innerHTML = '<option value="all">Toutes les semaines</option>';
                    if (weekDetectionInfo) {
                        weekDetectionInfo.innerHTML = '<span class="text-warning">⚠️ Colonne de semaines non trouvée</span>';
                        Utils.toggleElement(weekDetectionInfo, true);
                    }
                    return;
                }
                
                const previewData = data.extended_preview || data.processed_preview || [];
                
                previewData.forEach(row => {
                    const weekValue = row[weekColumn];
                    if (weekValue && String(weekValue).trim() !== '') {
                        let weekStr = String(weekValue).trim();
                        
                        if (weekStr.toUpperCase() === 'RELIQUAT') {
                            weeks.add('RELIQUAT');
                        } else if (weekStr.toUpperCase().startsWith('S')) {
                            weeks.add(weekStr.toUpperCase());
                        } else {
                            const weekNum = parseInt(weekStr, 10);
                            if (!isNaN(weekNum)) {
                                weeks.add(`S${weekNum}`);
                            } else {
                                weeks.add(weekStr);
                            }
                        }
                    }
                });
            }
            
            weekSelect.innerHTML = '<option value="all">Toutes les semaines</option>';
            
            const sortedWeeks = Array.from(weeks).sort((a, b) => {
                if (a === 'RELIQUAT') return 1;
                if (b === 'RELIQUAT') return -1;
                
                const numA = parseInt(a.replace(/\D/g, ''), 10) || 0;
                const numB = parseInt(b.replace(/\D/g, ''), 10) || 0;
                
                return numA - numB;
            });
            
            sortedWeeks.forEach(week => {
                const option = document.createElement('option');
                option.value = week;
                option.textContent = week;
                weekSelect.appendChild(option);
            });
            
            if (weekDetectionInfo) {
                if (weeks.size > 0) {
                    weekDetectionInfo.innerHTML = `<span class="text-success">✓ ${weeks.size} semaine(s) détectée(s): ${Array.from(weeks).join(', ')}</span>`;
                } else {
                    weekDetectionInfo.innerHTML = '<span class="text-warning">⚠️ Aucune semaine détectée</span>';
                }
                Utils.toggleElement(weekDetectionInfo, true);
            }
            
        } catch (error) {
            weekSelect.innerHTML = '<option value="all">Toutes les semaines</option>';
            if (weekDetectionInfo) {
                weekDetectionInfo.innerHTML = '<span class="text-warning">⚠️ Erreur lors de la détection des semaines</span>';
                Utils.toggleElement(weekDetectionInfo, true);
            }
        }
    }

    enableAnalysisControls() {
        const container = document.getElementById('analysis-sheet-selection');
        if (container) container.style.display = 'block';
        this.updateAnalysisButtonState();
    }

    updateAnalysisButtonState() {
        const startBtn = document.getElementById('start-analysis-btn');
        if (startBtn) {
            startBtn.disabled = !this.currentFile || !this.currentSheet;
        }
    }

    async startPHPAnalysis() {
        if (!this.currentFile || !this.currentSheet) {
            app.showNotification('Veuillez sélectionner un fichier et une feuille', 'warning');
            return;
        }

        try {
            this.showProgress();
            
            const analysisOptions = {
                weekly_planning: document.getElementById('weekly-planning')?.checked || false,
                equipment_analysis: document.getElementById('equipment-analysis')?.checked || false,
                concatenation_analysis: document.getElementById('concatenation-analysis')?.checked || false,
                conflict_detection: document.getElementById('conflict-detection')?.checked || false,
                week_filter: document.getElementById('analysis-week')?.value || 'all'
            };
            
            this.updateProgress(10, 'Démarrage de l\'analyse...');

            const response = await api.startPHPAnalysis(
                this.currentFile.filename, 
                this.currentSheet,
                analysisOptions
            );

            if (!response.success) {
                throw new Error(response.error || 'Analyse échouée');
            }

            this.updateProgress(90, 'Traitement des résultats...');
            
            this.analysisResults = response.results;
            
            if (this.analysisResults.concatenated_data) {
                this.concatenatedData = this.analysisResults.concatenated_data;
            }
            
            if (this.analysisResults.conflicts) {
                this.conflicts = this.analysisResults.conflicts;
            }
            
            this.updateProgress(100, 'Analyse terminée');
            this.displayPHPResults();
            
            setTimeout(() => {
                this.hideProgress();
                document.getElementById('analysis-results').style.display = 'block';
            }, 500);
            
            app.showNotification('Analyse terminée avec succès', 'success');
            
        } catch (error) {
            console.error('Analysis error:', error);
            app.showNotification(`Erreur lors de l'analyse: ${error.message}`, 'error');
            this.hideProgress();
        }
    }

    displayPHPResults() {
        this.displaySummaryMetrics();
        this.displayWeeklyPlanning();
        this.displayEquipmentAnalysis();
        this.displayConcatenatedData();
        this.displayConflicts();
        
        const exportBtn = document.getElementById('export-analysis-btn');
        if (exportBtn) exportBtn.disabled = false;
    }

    displaySummaryMetrics() {
        const summary = this.analysisResults.summary;
        if (!summary) return;

        const setElementText = (id, value, suffix = '') => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value + suffix;
            }
        };

        const formatNumber = (num) => {
            return typeof num === 'number' ? Math.round(num).toLocaleString('fr-FR') : '0';
        };

        // Set summary metrics with improved formatting
        setElementText('total-rdv', formatNumber(summary.total_rdv));
        setElementText('total-clients', formatNumber(summary.total_clients));
        setElementText('total-equipment', formatNumber(summary.total_series));
        setElementText('weekly-hours', formatNumber(summary.total_hours), 'h');
        setElementText('occupancy-rate', formatNumber(summary.total_days_with_rdv), ' jours');
        
        // Enhanced conflict count with severity indication
        const conflictElement = document.getElementById('conflict-count');
        if (conflictElement) {
            const conflictCount = summary.conflict_count || 0;
            if (conflictCount > 0) {
                conflictElement.innerHTML = `<span class="conflict-warning">${formatNumber(conflictCount)}</span>`;
                conflictElement.parentElement.classList.add('has-conflicts');
            } else {
                conflictElement.textContent = '0';
                conflictElement.parentElement.classList.remove('has-conflicts');
            }
        }
    }

    displayWeeklyPlanning() {
        const container = document.getElementById('weekly-content');
        const weeklyData = this.analysisResults.weekly_planning;
        
        if (!weeklyData || Object.keys(weeklyData).length === 0) {
            container.innerHTML = '<p class="no-data">Aucune donnée de planning hebdomadaire</p>';
            return;
        }

        let html = '<div class="weekly-planning">';
        
        Object.entries(weeklyData).forEach(([week, data]) => {
            const totalHours = Math.round(data.total_hours || 0);
            const avgDuration = data.avg_rdv_duration_hours || 0;
            
            html += `
                <div class="week-card">
                    <h5>${week}</h5>
                    <div class="week-stats">
                        <div class="stat-item">
                            <span class="stat-label">RDV :</span>
                            <span class="stat-value">${data.rdv_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Clients :</span>
                            <span class="stat-value">${data.client_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Engins :</span>
                            <span class="stat-value">${data.equipment_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Durée moy. RDV :</span>
                            <span class="stat-value">${avgDuration.toFixed(1)}h</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }

    displayEquipmentAnalysis() {
        const container = document.getElementById('equipment-content');
        const equipmentData = this.analysisResults.equipment_analysis;
        
        if (!equipmentData || Object.keys(equipmentData).length === 0) {
            container.innerHTML = '<p class="no-data">Aucune donnée d\'engins</p>';
            return;
        }

        let html = `
            <table class="equipment-table">
                <thead>
                    <tr>
                        <th>Site</th>
                        <th>Série</th>
                        <th>RDV Total</th>
                        <th>RDV Valides</th>
                        <th>RDV Invalides</th>
                        <th>Jours d'immobilisation</th>
                        <th>Heures d'immobilisation</th>
                        <th>Durée moyenne</th>
                        <th>Opérations</th>
                        <th>Clients</th>
                    </tr>
                </thead>
                <tbody>
        `;

        Object.entries(equipmentData).forEach(([key, data]) => {
            const immobilizationDays = data.total_immobilization_days || 0;
            const immobilizationHours = Math.round(data.total_immobilization_hours || 0);
            const avgDurationDays = data.average_duration_days || 0;
            const avgDurationHours = data.average_duration_hours || 0;
            
            const validRdv = data.valid_rdv_count || 0;
            const invalidRdv = data.invalid_rdv_count || 0;
            const totalRdv = data.rdv_count || 0;
            
            const hasInvalidData = invalidRdv > 0;
            const rowClass = hasInvalidData ? 'has-invalid-data' : '';
            
            html += `
                <tr class="${rowClass}">
                    <td>${data.site}</td>
                    <td><strong>${data.equipment}</strong></td>
                    <td>${totalRdv}</td>
                    <td class="valid-count">${validRdv}</td>
                    <td class="invalid-count">${invalidRdv > 0 ? `<span class="warning">${invalidRdv}</span>` : '0'}</td>
                    <td><strong>${immobilizationDays} jours</strong></td>
                    <td>${immobilizationHours}h</td>
                    <td>${avgDurationDays > 0 ? `${avgDurationDays}j (${avgDurationHours}h)` : 'N/A'}</td>
                    <td>${data.operations_count}</td>
                    <td>${data.clients_count}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        
        // Add legend for invalid data
        html += `
            <div class="equipment-legend">
                <p><span class="legend-item valid">RDV Valides:</span> Utilisés pour les calculs de durée et d'immobilisation</p>
                <p><span class="legend-item invalid">RDV Invalides:</span> Dates manquantes ou incorrectes - exclus des calculs</p>
            </div>
        `;
        
        container.innerHTML = html;
    }

    displayConcatenatedData() {
        const container = document.getElementById('concatenation-content');
        
        if (!this.concatenatedData || this.concatenatedData.length === 0) {
            container.innerHTML = '<p class="no-data">Aucune donnée concaténée</p>';
            return;
        }

        this.populateConcatenatedFilters();
        this.renderConcatenatedTable(this.concatenatedData);
    }

    populateConcatenatedFilters() {
        const clientSelect = document.getElementById('concat-filter-client');
        const enginSelect = document.getElementById('concat-filter-engin');
        
        if (!clientSelect || !this.concatenatedData) return;
        
        try {
            clientSelect.innerHTML = '<option value="">Tous les clients</option>';
            if (enginSelect) {
                enginSelect.innerHTML = '<option value="">Tous les engins</option>';
            }
            
            const clients = new Set();
            const equipment = new Set();
            
            this.concatenatedData.forEach(item => {
                if (item.client && item.client.trim()) {
                    // Handle multiple clients in one entry
                    item.client.split(',').forEach(client => {
                        const trimmedClient = client.trim();
                        if (trimmedClient) clients.add(trimmedClient);
                    });
                }
                if (item.material_number && item.material_number.trim()) {
                    equipment.add(item.material_number.trim());
                }
            });
            
            Array.from(clients).sort().forEach(client => {
                const option = document.createElement('option');
                option.value = client;
                option.textContent = client;
                clientSelect.appendChild(option);
            });
            
            if (enginSelect) {
                Array.from(equipment).sort().forEach(engin => {
                    const option = document.createElement('option');
                    option.value = engin;
                    option.textContent = engin;
                    enginSelect.appendChild(option);
                });
            }
            
        } catch (error) {
            console.error('Error populating filters:', error);
        }
    }

    renderConcatenatedTable(data = null) {
        const container = document.getElementById('concatenation-content');
        const displayData = data || this.concatenatedData;
        const rows = displayData.slice(0, 100);

        let html = `
            <div class="concat-summary">
                <p><strong>Total:</strong> ${displayData.length} entrées concaténées</p>
                ${displayData.length > 100 ? '<p><em>Affichage des 100 premières entrées</em></p>' : ''}
            </div>
            <div class="concat-table-container">
                <table class="concat-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Site</th>
                            <th>Numéro engin</th>
                            <th>Date début</th>
                            <th>Date fin</th>
                            <th>Client</th>
                            <th>Opérations</th>
                            <th>Jours</th>
                            <th>Heures</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        rows.forEach(item => {
            const durationDays = item.duration_days || 0;
            const durationHours = Math.round(item.duration_hours || 0);
            html += `
                <tr>
                    <td>${item.index}</td>
                    <td>${item.site}</td>
                    <td><strong>${item.material_number || 'N/A'}</strong></td>
                    <td>${this.formatConcatDate(item.date_debut)}</td>
                    <td>${this.formatConcatDate(item.date_fin)}</td>
                    <td>${this.truncateText(item.client, 20)}</td>
                    <td>${this.truncateText(item.operations_summary || item.operation, 25)}</td>
                    <td><strong>${durationDays}j</strong></td>
                    <td>${durationHours}h</td>
                </tr>
            `;
        });

        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    displayConflicts() {
        const container = document.getElementById('conflicts-content');
        
        if (!this.conflicts || this.conflicts.length === 0) {
            container.innerHTML = '<div class="no-conflicts"><p>✅ Aucun conflit détecté</p></div>';
            return;
        }
        
        let html = `
            <div class="conflicts-summary">
                <p class="warning">⚠️ ${this.conflicts.length} problèmes détectés</p>
                <p>Les anomalies suivantes ont été identifiées:</p>
            </div>
            <div class="conflicts-table-container">
                <table class="conflicts-table">
                    <thead>
                        <tr>
                            <th>Sévérité</th>
                            <th>Type</th>
                            <th>Engin</th>
                            <th>Opération</th>
                            <th>Description</th>
                            <th>Détails</th>
                            <th>Occurrences</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        this.conflicts.forEach((conflict, index) => {
            const equipment = conflict.equipment ? conflict.equipment.split('_')[1] : 'Non spécifié';
            const occurrenceCount = conflict.occurrence_count || 1;
            let conflictTypeLabel = '';
            let conflictDetails = '';
            let severityClass = `severity-${conflict.severity}`;
            let severityIcon = '';
            
            // Severity icons
            switch(conflict.severity) {
                case 'high':
                    severityIcon = '🔴';
                    break;
                case 'medium':
                    severityIcon = '🟡';
                    break;
                default:
                    severityIcon = '🔵';
            }
            
            switch(conflict.type) {
                case 'missing_start_date':
                    conflictTypeLabel = 'Date début manquante';
                    conflictDetails = `Date originale: "${conflict.sample_original_dates?.start || 'N/A'}"<br>L'engin n'est peut-être pas encore sur site`;
                    break;
                    
                case 'missing_end_date':
                    conflictTypeLabel = 'Date fin manquante';
                    conflictDetails = `Date originale: "${conflict.sample_original_dates?.end || 'N/A'}"<br>L'entretien n'est peut-être pas encore défini`;
                    break;
                    
                case 'date_inversion':
                    conflictTypeLabel = 'Inversion de dates';
                    const startDate = this.formatDateFromIso(conflict.rdv_info?.start);
                    const endDate = this.formatDateFromIso(conflict.rdv_info?.end);
                    conflictDetails = `Début: ${startDate}<br>Fin: ${endDate}`;
                    break;
                    
                case 'excessive_immobilization':
                    conflictTypeLabel = 'Immobilisation excessive';
                    const durationDays = conflict.days || 0;
                    const durationHours = conflict.hours || 0;
                    const startDateEx = this.formatDateFromIso(conflict.rdv_info?.start);
                    const endDateEx = this.formatDateFromIso(conflict.rdv_info?.end);
                    conflictDetails = `Durée: ${durationDays} jours (${durationHours}h)<br>Période: ${startDateEx} - ${endDateEx}`;
                    break;
                    
                default:
                    conflictTypeLabel = conflict.type || 'Anomalie';
                    conflictDetails = conflict.description || 'Non spécifié';
            }
            
            html += `
                <tr class="${severityClass}">
                    <td class="severity-cell">${severityIcon} ${conflict.severity.toUpperCase()}</td>
                    <td><strong>${conflictTypeLabel}</strong></td>
                    <td>${equipment}</td>
                    <td>${conflict.operation || 'N/A'}</td>
                    <td>${conflict.description || conflict.libelle || 'N/A'}</td>
                    <td class="details-cell">${conflictDetails}</td>
                    <td class="occurrence-cell">
                        <span class="badge">${occurrenceCount}x</span>
                        ${occurrenceCount > 1 ? '<br><em>Groupées</em>' : ''}
                    </td>
                </tr>
            `;
        });
        
        html += '</tbody></table></div>';
        container.innerHTML = html;
    }

    async exportPHPAnalysis() {
        if (!this.analysisResults) {
            app.showNotification('Aucune analyse à exporter', 'warning');
            return;
        }

        try {
            const format = document.querySelector('input[name="analysis-export-format"]:checked').value;
            const filename = document.getElementById('analysis-export-filename').value || 'analyse_maintenance';
            
            const exportOptions = {
                summary: document.getElementById('export-summary')?.checked || false,
                concatenated: document.getElementById('export-concatenated')?.checked || false,
                conflicts: document.getElementById('export-conflicts')?.checked || false,
                weekly_planning: true, // Always include weekly planning
                equipment_analysis: true // Always include equipment analysis
            };

            app.showLoading('Génération du fichier d\'export en cours...');
            
            try {
                // Use the new unified export API
                const blob = await api.exportAnalysis(format, filename, exportOptions);
                
                // Determine file extension
                const extensionMap = {
                    'excel': 'xlsx',
                    'csv': 'csv',
                    'pdf': 'pdf'
                };
                
                const extension = extensionMap[format] || 'xlsx';
                const finalFilename = filename.endsWith(`.${extension}`) ? filename : `${filename}.${extension}`;
                
                // Download the file
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = finalFilename;
                document.body.appendChild(a);
                a.click();
                
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                }, 100);
                
                app.showNotification('Analyse exportée avec succès', 'success');
            } finally {
                app.showLoading(false);
            }
            
        } catch (error) {
            console.error('Export error:', error);
            app.showNotification(`Erreur lors de l'export: ${error.message}`, 'error');
        }
    }

    applyConcatFilter() {
        const clientFilter = document.getElementById('concat-filter-client')?.value || '';
        const enginFilter = document.getElementById('concat-filter-engin')?.value || '';
        const dateFilter = document.getElementById('concat-filter-date')?.value || '';
        
        if (!clientFilter && !enginFilter && !dateFilter) {
            this.renderConcatenatedTable(this.concatenatedData);
            return;
        }
        
        const filteredData = this.concatenatedData.filter(item => {
            // Handle multiple clients in one entry
            const matchesClient = !clientFilter || 
                (item.client && item.client.includes(clientFilter));
            
            const matchesEngin = !enginFilter || 
                (item.material_number === enginFilter);
            
            let matchesDate = true;
            if (dateFilter) {
                const dateFormatted = dateFilter.replace(/-/g, '');
                matchesDate = 
                    (item.date_debut && item.date_debut.includes(dateFormatted)) || 
                    (item.date_fin && item.date_fin.includes(dateFormatted));
            }
            
            return matchesClient && matchesEngin && matchesDate;
        });
        
        this.renderConcatenatedTable(filteredData);
    }

    clearConcatFilter() {
        const clientSelect = document.getElementById('concat-filter-client');
        const enginSelect = document.getElementById('concat-filter-engin');
        const dateInput = document.getElementById('concat-filter-date');
        
        if (clientSelect) clientSelect.value = '';
        if (enginSelect) enginSelect.value = '';
        if (dateInput) dateInput.value = '';
        
        this.renderConcatenatedTable(this.concatenatedData);
    }

    // Utility methods
    formatDateFromIso(isoString) {
        if (!isoString) return 'Non défini';
        try {
            const date = new Date(isoString);
            return date.toLocaleDateString('fr-FR') + ' ' + date.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
        } catch (e) {
            return isoString;
        }
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    formatConcatDate(dateStr) {
        if (!dateStr || dateStr === 'NODATE') return 'Non défini';
        
        try {
            // Handle the format from concatenation data (YYYYMMDD_HHMM)
            if (dateStr.includes('_')) {
                const [datePart, timePart] = dateStr.split('_');
                
                // Format: YYYYMMDD to DD/MM/YYYY
                if (datePart.length === 8) {
                    const year = datePart.substring(0, 4);
                    const month = datePart.substring(4, 6);
                    const day = datePart.substring(6, 8);
                    
                    // Format time if available
                    let timeFormatted = '';
                    if (timePart && timePart.length >= 4) {
                        const hour = timePart.substring(0, 2);
                        const minute = timePart.substring(2, 4);
                        timeFormatted = ` ${hour}:${minute}`;
                    }
                    
                    return `${day}/${month}/${year}${timeFormatted}`;
                }
            }
            
            // Handle ISO format dates
            if (dateStr.includes('T')) {
                const date = new Date(dateStr);
                return date.toLocaleDateString('fr-FR') + ' ' + date.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
            }
            
            // Try to parse as regular date
            const date = new Date(dateStr);
            if (!isNaN(date.getTime())) {
                return date.toLocaleDateString('fr-FR') + ' ' + date.toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'});
            }
            
            return dateStr;
        } catch (e) {
            return dateStr;
        }
    }

    showProgress() {
        const progressSection = document.getElementById('analysis-progress');
        if (progressSection) progressSection.style.display = 'block';
        this.updateProgress(0, 'Initialisation...');
    }

    hideProgress() {
        const progressSection = document.getElementById('analysis-progress');
        if (progressSection) progressSection.style.display = 'none';
    }

    updateProgress(percentage, text) {
        const progressBar = document.getElementById('analysis-progress-bar');
        const progressText = document.getElementById('analysis-progress-text');
        
        if (progressBar) progressBar.style.width = `${percentage}%`;
        if (progressText) progressText.textContent = text;
    }

    resetForm() {
        this.currentFile = null;
        this.currentSheet = null;
        this.analysisResults = null;
        this.concatenatedData = [];
        this.conflicts = [];
        
        const fileInfo = document.getElementById('analysis-file-info');
        if (fileInfo) fileInfo.style.display = 'none';
        
        const sheetSelection = document.getElementById('analysis-sheet-selection');
        if (sheetSelection) sheetSelection.style.display = 'none';
        
        const progressSection = document.getElementById('analysis-progress');
        if (progressSection) progressSection.style.display = 'none';
        
        const resultsSection = document.getElementById('analysis-results');
        if (resultsSection) resultsSection.style.display = 'none';

        const fileInput = document.getElementById('analysis-file-input');
        if (fileInput) fileInput.value = '';
        
        const sheetSelect = document.getElementById('analysis-sheet-select');
        if (sheetSelect) sheetSelect.innerHTML = '<option value="">Sélectionner une feuille...</option>';
        
        const startBtn = document.getElementById('start-analysis-btn');
        if (startBtn) startBtn.disabled = true;
        
        const exportBtn = document.getElementById('export-analysis-btn');
        if (exportBtn) exportBtn.disabled = true;
        
        ['weekly-planning', 'equipment-analysis', 'concatenation-analysis', 'conflict-detection'].forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) checkbox.checked = true;
        });
    }

    setupInfoToggle() {
        document.querySelectorAll('.info-toggle').forEach(button => {
            button.addEventListener('click', () => {
                const targetId = button.getAttribute('data-target');
                const infoPanel = document.getElementById(targetId);
                
                if (infoPanel) {
                    infoPanel.classList.toggle('show');
                    
                    // Store state in local storage to remember user preference
                    const isVisible = infoPanel.classList.contains('show');
                    localStorage.setItem(`info_${targetId}`, isVisible ? 'shown' : 'hidden');
                    
                    // Update button text
                    button.textContent = isVisible ? '🔼' : 'ℹ️';
                }
            });
        });
        
        // Check localStorage to restore previous state
        document.querySelectorAll('.card-info').forEach(panel => {
            const panelId = panel.getAttribute('id');
            const savedState = localStorage.getItem(`info_${panelId}`);
            
            if (savedState === 'shown') {
                panel.classList.add('show');
                const button = document.querySelector(`.info-toggle[data-target="${panelId}"]`);
                if (button) button.textContent = '🔼';
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.analysisManager = new AnalysisManager();
    window.analysisManager.init();
});