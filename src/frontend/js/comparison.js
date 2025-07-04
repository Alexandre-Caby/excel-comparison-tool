// Comparison page functionality

const PAGE_SIZE = 25; // Number of rows per page

class ComparisonManager {
    constructor() {
        this.comparisonResults = null;
        this.currentSheet = null;
        this.currentFile = null;
        this.allDifferences = []; // Store all differences for filtering
        this.currentColumns = []; // Track current columns displayed
        this.currentColumnOptions = []; // Track available column options
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

    getComparisonMode() {
        // Check if we have detailed data or just summary
        const firstSheet = Object.keys(this.comparisonResults.results || {})[0];
        if (firstSheet) {
            const firstComparison = this.comparisonResults.results[firstSheet][0];
            if (firstComparison && !firstComparison.differences && firstComparison.summary) {
                return 'summary';
            }
        }
        return 'full';
    }

    displayResults() {
        // Hide info box when results are shown
        const infoBox = document.querySelector('.info-box');
        if (infoBox) infoBox.style.display = 'none';

        document.getElementById('comparison-results').style.display = 'block';
        
        const summary = this.comparisonResults.summary;
        const mode = this.getComparisonMode();
        
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
        
        // Handle different modes
        if (mode === 'summary') {
            this.displaySummaryResults();
        } else {
            this.displayFullResults();
        }
    }
    
    updateMetrics(summary) {
        const sheetsEl = document.getElementById('total-sheets');
        const diffsEl = document.getElementById('total-differences');
        const dupsEl = document.getElementById('total-duplicates');
        const cellsEl = document.getElementById('total-cells');
        const timeEl = document.getElementById('execution-time');
        const matchRateEl = document.getElementById('match-rate');

        if (sheetsEl) sheetsEl.textContent = summary.total_sheets_compared || 0;
        if (diffsEl) diffsEl.textContent = summary.total_differences || 0;
        if (dupsEl) dupsEl.textContent = summary.total_duplicates || 0;
        if (cellsEl) cellsEl.textContent = summary.total_cells_compared || 0;

        const cellsCompared = summary.total_cells_compared || 1;
        const differences = summary.total_differences || 0;
        const duplicates = summary.total_duplicates || 0;
        const matchRate = Math.max(0, 100 - ((differences + duplicates) / cellsCompared) * 100);
        if (matchRateEl) matchRateEl.textContent = `${matchRate.toFixed(2)}%`;

        if (timeEl) timeEl.textContent = `${(summary.execution_time_seconds || 0).toFixed(2)}s`;
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

    displaySummaryResults() {
        // Hide detailed comparison tables
        const detailedSections = ['differences-section', 'duplicates-section'];
        detailedSections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'none';
        });

        // Hide results-navigation
        const resultsNav = document.querySelector('.results-navigation');
        if (resultsNav) resultsNav.style.display = 'none';

        // Show summary-only view
        const summarySection = document.getElementById('summary-section');
        if (summarySection) {
            summarySection.style.display = 'block';
            this.populateSummaryView();
        }
    }

    displayFullResults() {
        // Show detailed comparison tables
        const detailedSections = ['differences-section', 'duplicates-section'];
        detailedSections.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.style.display = 'block';
        });
        
        // Hide summary-only view
        const summarySection = document.getElementById('summary-section');
        if (summarySection) summarySection.style.display = 'none';
        
        // Populate sheet selector and display data
        this.populateSheetSelector();
        const sheets = Object.keys(this.comparisonResults.results);
        if (sheets.length > 0) {
            this.selectSheet(sheets[0]);
        }
    }

    // Add new method to populate summary view
    populateSummaryView() {
        const results = this.comparisonResults.results;
        let summaryHtml = '<div class="summary-cards">';
        
        Object.entries(results).forEach(([sheet, comparisons]) => {
            summaryHtml += `<div class="summary-card">
                <h4>📊 Feuille: ${sheet}</h4>`;
            
            comparisons.forEach(comp => {
                const summary = comp.summary || {};
                summaryHtml += `
                    <div class="file-summary">
                        <div class="file-header">
                            <strong>📄 ${comp.comparison_file}</strong>
                        </div>
                        <div class="summary-stats">
                            <div class="stat-item">
                                <span class="stat-label">Lignes base:</span>
                                <span class="stat-value">${comp.base_rows}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Lignes comparaison:</span>
                                <span class="stat-value">${comp.comp_rows}</span>
                            </div>
                            <div class="stat-item ${summary.total_diffs > 0 ? 'highlight-diff' : ''}">
                                <span class="stat-label">Différences:</span>
                                <span class="stat-value">${summary.total_diffs || 0}</span>
                            </div>
                            <div class="stat-item ${summary.total_dups_base > 0 ? 'highlight-dup' : ''}">
                                <span class="stat-label">Doublons base:</span>
                                <span class="stat-value">${summary.total_dups_base || 0}</span>
                            </div>
                            <div class="stat-item ${summary.total_dups_comp > 0 ? 'highlight-dup' : ''}">
                                <span class="stat-label">Doublons comparaison:</span>
                                <span class="stat-value">${summary.total_dups_comp || 0}</span>
                            </div>
                        </div>
                    </div>`;
            });
            
            summaryHtml += '</div>';
        });
        
        summaryHtml += '</div>';
        
        const summaryContainer = document.getElementById('summary-content');
        if (summaryContainer) {
            summaryContainer.innerHTML = summaryHtml;
        }
    }

    selectSheet(sheetName) {
        const mode = this.getComparisonMode();
        
        if (mode === 'summary') {
            this.updateSummaryForSheet(sheetName);
            return;
        }

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

    updateSummaryForSheet(sheetName) {
        const summaryCards = document.querySelectorAll('.summary-card');
        summaryCards.forEach(card => {
            card.classList.remove('selected');
            if (card.querySelector('h4').textContent.includes(sheetName)) {
                card.classList.add('selected');
            }
        });
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

        // Display duplicates from base file
        this.displayDuplicates(result.duplicates_base, result.duplicates_base_columns, 1, 'Base');
        if (result.duplicates_comp && result.duplicates_comp.length > 0) {
            this.displayDuplicates(result.duplicates_comp, result.duplicates_comp_columns, 1, 'Comparaison');
        }
    }
    
    displayDifferences(differences, columns, page = 1, isFiltering = false) {
        const content = document.getElementById('differences-content');
        const pagination = document.getElementById('differences-pagination');
        if (!differences || differences.length === 0) {
            content.innerHTML = `<p class="success-message">Aucune différence trouvée</p>`;
            pagination.innerHTML = '';
            return;
        }
        // Pagination logic
        const totalPages = Math.ceil(differences.length / PAGE_SIZE);
        const start = (page - 1) * PAGE_SIZE;
        const end = start + PAGE_SIZE;
        const pageData = differences.slice(start, end);

        // Enhanced display - use custom table
        let tableHtml = `<table class="data-table differences-table">
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Clé</th>
                    <th>Champ</th>
                    <th>Valeur d'origine</th>
                    <th>Valeur comparée</th>
                    <th>Action recommandée</th>
                </tr>
            </thead>
            <tbody>`;

        // Apply color coding and formatting to each row
        pageData.forEach(diff => {
            // Status-based styling
            let statusClass = '';
            let statusIcon = '';
            let recommendation = '';
            
            switch (diff.Status) {
                case 'Ajoutée':
                    statusClass = 'added-row';
                    statusIcon = '✚';
                    recommendation = 'Ajouter dans le fichier d\'origine';
                    break;
                case 'Supprimée':
                    statusClass = 'removed-row';
                    statusIcon = '✖';
                    recommendation = 'Vérifier si suppression intentionnelle';
                    break;
                case 'Modifiée':
                    statusClass = 'modified-row';
                    statusIcon = '✎';
                    recommendation = 'Vérifier quelle valeur est correcte';
                    break;
                case 'Similaire':
                    statusClass = 'similar-row';
                    statusIcon = '≈';
                    recommendation = 'Probablement la même entrée avec orthographe différente';
                    break;
                default:
                    statusIcon = '•';
            }
            
            // Format values better
            const baseValue = this.formatCellValue(diff['Base Value']);
            const compValue = this.formatCellValue(diff['Comparison Value']);
            const column = diff.Column || '-';
            
            tableHtml += `<tr class="${statusClass}">
                <td><span class="status-icon" title="${diff.Status}">${statusIcon}</span> ${diff.Status}</td>
                <td>${this.shortenKey(diff.Key)}</td>
                <td>${column}</td>
                <td>${baseValue}</td>
                <td>${compValue}</td>
                <td>${recommendation}</td>
            </tr>`;
        });
        
        tableHtml += `</tbody></table>`;
        content.innerHTML = tableHtml;
        
        // Add explanation above table
        const explanation = document.createElement('div');
        explanation.className = 'table-explanation';
        explanation.innerHTML = `
            <p><strong>Comment lire ce tableau :</strong></p>
            <ul>
                <li><span class="status-icon added">✚</span> <strong>Ajoutée</strong> : Entrée présente uniquement dans le fichier de comparaison</li>
                <li><span class="status-icon removed">✖</span> <strong>Supprimée</strong> : Entrée présente uniquement dans le fichier d'origine</li>
                <li><span class="status-icon modified">✎</span> <strong>Modifiée</strong> : La valeur a été modifiée entre les deux fichiers</li>
            </ul>
        `;
        content.insertBefore(explanation, content.firstChild);
        
        pagination.innerHTML = this.createPaginationControls(page, totalPages, (newPage) => {
            this.displayDifferences(differences, columns, newPage, true);
        });

        if (!isFiltering) {
            this.allDifferences = differences;
            this.currentColumns = columns;
            
            // Extract column options for filtering
            if (columns && columns.includes('Column')) {
                this.currentColumnOptions = [...new Set(differences.map(d => d.Column).filter(Boolean))];
            }
            
            // Setup filters if not already done
            if (!document.getElementById('filters-container').hasChildNodes()) {
                this.setupFilters();
            }
        }
    }
    
    displayDuplicates(duplicates, columns, page = 1, label = '') {
        const content = document.getElementById('duplicates-content');
        const pagination = document.getElementById('duplicates-pagination');
        // Clear previous content
        if (page === 1) content.innerHTML = '';

        if (!duplicates || duplicates.length === 0) {
            content.innerHTML += `<p class="success-message">Aucun doublon trouvé${label ? ' (' + label + ')' : ''}</p>`;
            pagination.innerHTML = '';
            return;
        }

        // Group by key to count duplicate groups
        const groupCounts = {};
        duplicates.forEach(row => {
            const key = row.key || 'clé inconnue';
            groupCounts[key] = (groupCounts[key] || 0) + 1;
        });
        const groups = Object.entries(groupCounts)
            .filter(([_, count]) => count > 1)
            .sort((a, b) => b[1] - a[1]);

        // Show summary
        content.innerHTML += `
            <h5>Doublons ${label ? '(' + label + ')' : ''}</h5>
            <p>${groups.length} groupes de doublons détectés.</p>
            <ul>
                ${groups.slice(0, 10).map(([key, count]) =>
                    `<li><strong>${key}</strong> : ${count} occurrences</li>`
                ).join('')}
            </ul>
            ${groups.length > 10 ? `<p>...et ${groups.length - 10} autres groupes.</p>` : ''}
            <button class="btn secondary-btn" id="show-all-duplicates-${label}">Afficher tous les doublons</button>
        `;
        pagination.innerHTML = '';

        // Show full table on demand
        setTimeout(() => {
            const btn = document.getElementById(`show-all-duplicates-${label}`);
            if (btn) {
                btn.onclick = () => {
                    this.displayDuplicatesTable(duplicates, columns, 1, label);
                };
            }
        }, 0);
    }

    // Helper to show the full paginated table if user clicks
    displayDuplicatesTable(duplicates, columns, page = 1, label = '') {
        const content = document.getElementById('duplicates-content');
        const pagination = document.getElementById('duplicates-pagination');
        // Pagination logic
        const totalPages = Math.ceil(duplicates.length / PAGE_SIZE);
        const start = (page - 1) * PAGE_SIZE;
        const end = start + PAGE_SIZE;
        const pageData = duplicates.slice(start, end);

        content.innerHTML = `<h5>Doublons ${label ? '(' + label + ')' : ''}</h5>`;
        const uiColumns = columns.filter(col => col !== 'Base Row' && col !== 'Comp Row');
        content.innerHTML += utils.createTable(pageData, uiColumns, 'data-table duplicates-table');
        pagination.innerHTML = this.createPaginationControls(page, totalPages, (newPage) => {
            this.displayDuplicatesTable(duplicates, columns, newPage, label);
        });
    }
    
    createPaginationControls(current, total, onPageChange) {
        if (total <= 1) return '';
        let html = `<div class="pagination">`;

        // Previous button
        if (current > 1) {
            html += `<button class="page-btn" data-page="${current - 1}">&lt;</button>`;
        }

        // Calculate page range (max 5)
        let start = Math.max(1, current - 2);
        let end = Math.min(total, current + 2);
        if (end - start < 4) {
            if (start === 1) end = Math.min(total, start + 4);
            if (end === total) start = Math.max(1, end - 4);
        }

        if (start > 1) html += `<span style="padding:0 0.5rem;">...</span>`;
        for (let i = start; i <= end; i++) {
            html += `<button class="page-btn${i === current ? ' active' : ''}" data-page="${i}">${i}</button>`;
        }
        if (end < total) html += `<span style="padding:0 0.5rem;">...</span>`;

        // Next button
        if (current < total) {
            html += `<button class="page-btn" data-page="${current + 1}">&gt;</button>`;
        }
        html += `</div>`;
        setTimeout(() => {
            document.querySelectorAll('.pagination .page-btn').forEach(btn => {
                btn.onclick = () => onPageChange(Number(btn.dataset.page));
            });
        }, 0);
        return html;
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
                const value = e.target.value;
                this.selectSheet(value);
            });
        }

        // File selector
        const fileSelect = document.getElementById('file-select');
        if (fileSelect) {
            fileSelect.addEventListener('change', (e) => {
                this.selectFile(e.target.value);
            });
        }

        const startBtn = document.getElementById('start-comparison-btn');
        if (startBtn) {
            startBtn.addEventListener('click', async () => {
                document.getElementById('comparison-progress').style.display = 'block';
                document.querySelector('.info-box').style.display = 'none';
                try {
                    const result = await api.startComparison();
                    if (result && result.success) {
                        this.comparisonResults = result;
                        this.displayResults();
                    } else {
                        app.showNotification(result.error || 'Erreur lors de la comparaison', 'error');
                    }
                } catch (err) {
                    app.showNotification('Erreur lors de la comparaison', 'error');
                } finally {
                    document.getElementById('comparison-progress').style.display = 'none';
                }
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
    }
    
    async saveReport() {
        try {
            app.showLoading(true);
            const result = await api.saveReport();

            if (result.success) {
                // Get the first sheet/file's details for the report (adjust as needed for your structure)
                const sheetResults = this.comparisonResults?.results;
                let details = [];
                let columns = [];
                let duplicates_details = [];
                let duplicates_columns = [];

                if (sheetResults) {
                    // Flatten all differences and duplicates from all sheets/files
                    Object.values(sheetResults).forEach(fileResults => {
                        fileResults.forEach(fileResult => {
                            if (fileResult.differences && fileResult.differences.length > 0) {
                                details = details.concat(fileResult.differences);
                                columns = fileResult.differences_columns || columns;
                            }
                            if (fileResult.duplicates && fileResult.duplicates.length > 0) {
                                duplicates_details = duplicates_details.concat(fileResult.duplicates);
                                duplicates_columns = fileResult.duplicates_columns || duplicates_columns;
                            }
                        });
                    });
                }

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
                    sheets_compared: this.comparisonResults?.summary?.total_sheets_compared || 0,
                    duplicates: this.comparisonResults?.summary?.total_duplicates || 0,
                    details,
                    columns,
                    duplicates_details,
                    duplicates_columns,
                    comparison_mode: this.comparisonResults?.comparison_mode || 'full'
                };

                // Update session data
                app.sessionData.reports.push(reportData);

                app.showNotification(`Rapport ${reportData.id} sauvegardé avec succès`);

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
        const duplicates = this.comparisonResults.summary.total_duplicates || 0;

        const matchRate = Math.max(0, 100 - ((differences + duplicates) / cellsCompared) * 100);
        return `${matchRate.toFixed(1)}%`;
    }

    // Add helper methods
    formatCellValue(value) {
        if (!value && value !== 0) return '-';
        
        // Format dates nicely
        if (value && typeof value === 'string') {
            // Check if value looks like a date
            if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
                try {
                    const date = new Date(value);
                    if (!isNaN(date)) {
                        return date.toLocaleDateString('fr-FR');
                    }
                } catch(e) {
                    // Not a date, continue
                }
            }
        }
        
        return String(value);
    }

    shortenKey(key) {
        if (!key) return '-';
        // For long composite keys, shorten them for display
        if (key.length > 25) {
            return key.substring(0, 22) + '...';
        }
        return key;
    }

    // Add filtering capabilities
    setupFilters() {
        const filtersContainer = document.getElementById('filters-container');
        if (!filtersContainer) return;
        
        // Create status filter
        const statusFilter = document.createElement('div');
        statusFilter.className = 'filter-group';
        statusFilter.innerHTML = `
            <label for="status-filter">Filtrer par statut:</label>
            <select id="status-filter" class="filter-select">
                <option value="all">Tous les statuts</option>
                <option value="Ajoutée">Ajoutées</option>
                <option value="Supprimée">Supprimées</option>
                <option value="Modifiée">Modifiées</option>
                <option value="Similaire">Similaires</option>
            </select>
        `;
        
        // Create column filter if we have column data
        const columnFilter = document.createElement('div');
        columnFilter.className = 'filter-group';
        
        if (this.currentColumnOptions && this.currentColumnOptions.length) {
            let columnOptions = '<option value="all">Toutes les colonnes</option>';
            this.currentColumnOptions.forEach(col => {
                if (col) columnOptions += `<option value="${col}">${col}</option>`;
            });
            
            columnFilter.innerHTML = `
                <label for="column-filter">Filtrer par colonne:</label>
                <select id="column-filter" class="filter-select">
                    ${columnOptions}
                </select>
            `;
        }
        
        // Add search box
        const searchFilter = document.createElement('div');
        searchFilter.className = 'filter-group search-filter-container';
        searchFilter.innerHTML = `
            <label for="search-filter">
                Recherche avancée: 
                <span class="help-icon" id="search-help-icon">?</span>
            </label>
            <div class="search-input-wrapper">
                <input type="text" id="search-filter" class="filter-input" 
                       placeholder="Rechercher (ex: date:2025-07 valeur:GENE)" 
                       autocomplete="off">
                <button id="clear-search" class="clear-search-btn" title="Effacer la recherche">×</button>
            </div>
            <div class="search-options">
                <label><input type="checkbox" id="case-sensitive"> Sensible à la casse</label>
                <label><input type="checkbox" id="exact-match"> Correspondance exacte</label>
                <select id="search-field" class="search-field-select">
                    <option value="all">Tous les champs</option>
                    <option value="Key">Clé</option>
                    <option value="Column">Colonne</option>
                    <option value="Base Value">Valeur d'origine</option>
                    <option value="Comparison Value">Valeur comparée</option>
                </select>
            </div>
            <div id="search-help" class="search-help-panel">
                <div class="search-help-content">
                    <h4>Comment utiliser la recherche avancée</h4>
                    <p>Vous pouvez rechercher par texte simple ou utiliser des opérateurs :</p>
                    <ul>
                        <li><strong>champ:valeur</strong> - Rechercher dans un champ spécifique</li>
                        <li><strong>*valeur</strong> - Rechercher tous les termes se terminant par "valeur"</li>
                        <li><strong>valeur*</strong> - Rechercher tous les termes commençant par "valeur"</li>
                        <li><strong>"phrase exacte"</strong> - Rechercher une phrase exacte</li>
                    </ul>
                    <p><strong>Exemples :</strong></p>
                    <ul>
                        <li><strong>date:2025-07</strong> - Trouve toutes les dates de juillet 2025</li>
                        <li><strong>clé:BB2600</strong> - Trouve toutes les clés contenant BB2600</li>
                        <li><strong>GENE*</strong> - Trouve tous les termes commençant par GENE</li>
                    </ul>
                    <button id="close-search-help" class="btn secondary-btn">Fermer</button>
                </div>
            </div>
        `;
        
        // Add filters to container
        filtersContainer.innerHTML = '';
        filtersContainer.appendChild(statusFilter);
        filtersContainer.appendChild(columnFilter);
        filtersContainer.appendChild(searchFilter);
        
        // Add event listeners
        document.getElementById('status-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('column-filter')?.addEventListener('change', () => this.applyFilters());
        
        // Add event listeners for enhanced search functionality
        document.getElementById('search-filter').addEventListener('input', () => {
            this._debounceSearch();
            document.getElementById('clear-search').style.display = 
                document.getElementById('search-filter').value ? 'block' : 'none';
        });
        
        document.getElementById('search-filter').addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.applyFilters();
            } else if (e.key === 'Escape') {
                document.getElementById('search-filter').value = '';
                this.applyFilters();
                document.getElementById('clear-search').style.display = 'none';
            }
        });
        
        document.getElementById('clear-search').addEventListener('click', () => {
            document.getElementById('search-filter').value = '';
            this.applyFilters();
            document.getElementById('clear-search').style.display = 'none';
            document.getElementById('search-filter').focus();
        });
        
        document.getElementById('case-sensitive').addEventListener('change', () => this.applyFilters());
        document.getElementById('exact-match').addEventListener('change', () => this.applyFilters());
        document.getElementById('search-field').addEventListener('change', () => this.applyFilters());
        
        // Search help tooltip functionality
        document.getElementById('search-help-icon').addEventListener('click', () => {
            document.getElementById('search-help').classList.toggle('visible');
        });
        
        document.getElementById('close-search-help').addEventListener('click', () => {
            document.getElementById('search-help').classList.remove('visible');
        });
    }

    // Apply filters to the differences data
    applyFilters() {
        if (!this.allDifferences) return;
        
        const statusFilter = document.getElementById('status-filter').value;
        const columnFilter = document.getElementById('column-filter')?.value || 'all';
        const searchTerm = document.getElementById('search-filter').value.trim();
        
        // Get search options
        const caseSensitive = document.getElementById('case-sensitive').checked;
        const exactMatch = document.getElementById('exact-match').checked;
        const searchField = document.getElementById('search-field').value;
        
        // Parse advanced search syntax
        let parsedSearch = this._parseAdvancedSearch(searchTerm, caseSensitive);
        
        // Filter the data
        let filteredData = this.allDifferences.filter(diff => {
            // Status filter
            if (statusFilter !== 'all' && diff.Status !== statusFilter) return false;
            
            // Column filter
            if (columnFilter !== 'all' && diff.Column !== columnFilter) return false;
            
            // Search filter
            if (searchTerm) {
                // If specific field is selected in dropdown, override parsed fields
                if (searchField !== 'all') {
                    return this._matchSearchTerm(diff, searchField, searchTerm, caseSensitive, exactMatch);
                } else if (parsedSearch.fieldSearches.length > 0) {
                    // Use parsed field-specific searches
                    return parsedSearch.fieldSearches.every(fs => 
                        this._matchSearchTerm(diff, fs.field, fs.term, caseSensitive, exactMatch)
                    );
                } else {
                    // Global search across all fields
                    const searchFields = [
                        diff.Key, 
                        diff.Column, 
                        String(diff['Base Value'] || ''), 
                        String(diff['Comparison Value'] || '')
                    ];
                    
                    return searchFields.some(field => 
                        field && this._checkMatch(field, parsedSearch.globalTerm, caseSensitive, exactMatch)
                    );
                }
            }
            
            return true;
        });
        
        // Update filters info
        const filterInfo = document.getElementById('filter-info');
        if (filterInfo) {
            let filterText = `Affichage de ${filteredData.length} sur ${this.allDifferences.length} différences`;
            if (searchTerm) {
                filterText += ` (recherche: "${searchTerm}")`;
            }
            filterInfo.innerHTML = filterText;
            filterInfo.style.display = filteredData.length < this.allDifferences.length ? 'block' : 'none';
        }
        
        // Display filtered data with isFiltering=true flag
        this.displayDifferences(filteredData, this.currentColumns, 1, true);
        
        // Highlight search matches in the displayed results
        if (searchTerm) {
            this._highlightSearchMatches(searchTerm, caseSensitive);
        }
    }

    // Debounce search to avoid too many updates
    _debounceSearch() {
        if (this._searchTimeout) {
            clearTimeout(this._searchTimeout);
        }
        this._searchTimeout = setTimeout(() => {
            this.applyFilters();
        }, 300); // 300ms debounce time
    }

    _parseAdvancedSearch(searchTerm, caseSensitive) {
        // Initialize result structure
        const result = {
            globalTerm: searchTerm,
            fieldSearches: []
        };
        
        if (!searchTerm) return result;
        
        // Look for field-specific searches like "field:value"
        const fieldPattern = /(\w+):([\w\d\s*"-]+)/g;
        let match;
        let hasFieldMatches = false;
        
        // Process any field:value patterns
        while ((match = fieldPattern.exec(searchTerm)) !== null) {
            hasFieldMatches = true;
            const field = this._mapSearchFieldToColumn(match[1].trim());
            const value = match[2].trim();
            
            if (field) {
                result.fieldSearches.push({
                    field: field,
                    term: value
                });
            }
        }
        
        // If there were field-specific searches, remove them from the global term
        if (hasFieldMatches) {
            result.globalTerm = searchTerm.replace(fieldPattern, '').trim();
        }
        
        return result;
    }

    _mapSearchFieldToColumn(fieldName) {
        // Map common search terms to actual column names
        const fieldMap = {
            'clé': 'Key',
            'cle': 'Key',
            'key': 'Key',
            'colonne': 'Column',
            'column': 'Column',
            'valeur': 'Base Value',
            'value': 'Base Value',
            'origine': 'Base Value',
            'base': 'Base Value',
            'comparaison': 'Comparison Value',
            'comparison': 'Comparison Value',
            'nouvelle': 'Comparison Value',
            'new': 'Comparison Value',
            'status': 'Status',
            'statut': 'Status',
            'état': 'Status',
            'etat': 'Status',
            'type': 'Status',
            'date': null  // Special case: will search in both date fields
        };
        
        // Convert to lowercase for case-insensitive matching
        const normalized = fieldName.toLowerCase();
        
        if (normalized === 'date') {
            return ['Base Value', 'Comparison Value']; // Search in both value fields for dates
        }
        
        return fieldMap[normalized] || fieldName; // Return mapped field or original if not found
    }

    _matchSearchTerm(row, field, term, caseSensitive, exactMatch) {
        // Handle special case for multiple fields
        if (Array.isArray(field)) {
            return field.some(f => this._matchSearchTerm(row, f, term, caseSensitive, exactMatch));
        }
        
        const value = row[field];
        if (value === undefined || value === null) return false;
        
        return this._checkMatch(String(value), term, caseSensitive, exactMatch);
    }

    _checkMatch(text, pattern, caseSensitive, exactMatch) {
        if (!text || !pattern) return false;
        
        let normalizedText = caseSensitive ? text : text.toLowerCase();
        let normalizedPattern = caseSensitive ? pattern : pattern.toLowerCase();
        
        // Handle wildcards
        if (normalizedPattern.includes('*')) {
            const regexPattern = normalizedPattern
                .replace(/\*/g, '.*')
                .replace(/\?/g, '.')
                .replace(/\s+/g, '\\s+');
            try {
                const regex = new RegExp('^' + regexPattern + '$', caseSensitive ? '' : 'i');
                return regex.test(normalizedText);
            } catch (e) {
                console.warn('Invalid regex pattern:', e);
                return false;
            }
        }
        
        // Handle quoted phrases
        if (normalizedPattern.startsWith('"') && normalizedPattern.endsWith('"')) {
            const phrase = normalizedPattern.slice(1, -1);
            return exactMatch ? 
                normalizedText === phrase : 
                normalizedText.includes(phrase);
        }
        
        // Default search
        return exactMatch ? 
            normalizedText === normalizedPattern : 
            normalizedText.includes(normalizedPattern);
    }

    _highlightSearchMatches(searchTerm, caseSensitive) {
        const table = document.querySelector('.differences-table');
        if (!table) return;
        
        // Clear any existing highlights
        const highlighted = table.querySelectorAll('.search-highlight');
        highlighted.forEach(el => {
            const parent = el.parentNode;
            parent.textContent = parent.textContent; // This effectively removes the highlight spans
        });
        
        // Skip if search term is empty
        if (!searchTerm.trim()) return;
        
        // Get cells to search in
        const cells = table.querySelectorAll('tbody td:not(:first-child)');
        const parsedSearch = this._parseAdvancedSearch(searchTerm, caseSensitive);
        
        cells.forEach(cell => {
            const originalText = cell.textContent;
            let pattern = parsedSearch.globalTerm;
            
            if (!pattern && parsedSearch.fieldSearches.length > 0) {
                // Use first field search term as highlight pattern if there's no global term
                pattern = parsedSearch.fieldSearches[0].term;
            }
            
            if (pattern && this._checkMatch(originalText, pattern, caseSensitive, false)) {
                // Create a regex for highlighting that preserves case
                const flags = caseSensitive ? 'g' : 'gi';
                try {
                    let regex = new RegExp(pattern, flags);
                    
                    // Handle wildcard patterns
                    if (pattern.includes('*') || pattern.includes('?')) {
                        const escapedPattern = pattern
                            .replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // Escape regex special chars
                            .replace(/\\\*/g, '.*') // Convert * to regex wildcard
                            .replace(/\\\?/g, '.'); // Convert ? to regex single char
                        regex = new RegExp(escapedPattern, flags);
                    }
                    
                    cell.innerHTML = originalText.replace(
                        regex, 
                        match => `<span class="search-highlight">${match}</span>`
                    );
                } catch (e) {
                    console.warn('Error highlighting matches:', e);
                }
            }
        });
    }
}

// Create global comparison manager instance
window.comparisonManager = new ComparisonManager();
