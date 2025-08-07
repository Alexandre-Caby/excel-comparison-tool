// Upload page functionality

class UploadManager {
    constructor() {
        this.baseFile = null;
        this.comparisonFiles = [];
        this.siteMappings = { "LE": "Lens", "BGL": "BGL" };
        this.baseFileInfo = null;
        this.compFilesInfo = [];
    }
    
    init() {
        this.setupFileUploads();
        this.setupSiteMappings();
        this.setupComparisonConfig();
        this.loadSiteMappings();
    }
    
    setupFileUploads() {
        // Base file upload
        const baseUploadArea = document.getElementById('base-file-area');
        const baseFileInput = document.getElementById('base-file-input');
        
        if (baseUploadArea && baseFileInput) {
            baseUploadArea.addEventListener('click', () => baseFileInput.click());
            baseUploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            baseUploadArea.addEventListener('drop', (e) => this.handleDrop(e, 'base'));
            
            baseFileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleBaseFileUpload(e.target.files[0]);
                }
            });
        }
        
        // Comparison files upload
        const compUploadArea = document.getElementById('comp-files-area');
        const compFilesInput = document.getElementById('comp-files-input');
        
        if (compUploadArea && compFilesInput) {
            compUploadArea.addEventListener('click', () => compFilesInput.click());
            compUploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            compUploadArea.addEventListener('drop', (e) => this.handleDrop(e, 'comparison'));
            
            compFilesInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    this.handleComparisonFilesUpload(Array.from(e.target.files));
                }
            });
        }
        
        // Configuration buttons
        const addMappingBtn = document.getElementById('add-mapping-btn');
        const startComparisonBtn = document.getElementById('start-comparison-btn');
        const resetConfigBtn = document.getElementById('reset-config-btn');
        
        if (addMappingBtn) {
            addMappingBtn.addEventListener('click', this.handleAddMapping.bind(this));
        }
        
        if (startComparisonBtn) {
            startComparisonBtn.addEventListener('click', this.startComparison.bind(this));
        }
        
        if (resetConfigBtn) {
            resetConfigBtn.addEventListener('click', this.resetConfiguration.bind(this));
        }
    }
    
    handleAddMapping() {
        const siteCodeInput = document.getElementById('site-code');
        const sheetNameSelect = document.getElementById('sheet-name');
        
        if (siteCodeInput && sheetNameSelect) {
            const code = siteCodeInput.value.trim().toUpperCase();
            const sheet = sheetNameSelect.value;
            
            if (code && sheet) {
                this.addSiteMapping(code, sheet);
                siteCodeInput.value = '';
            } else {
                if (typeof app !== 'undefined') {
                    app.showNotification('Veuillez saisir un code de site et sélectionner une feuille', 'warning');
                }
            }
        }
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }
    
    handleDrop(e, type) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        const validFiles = files.filter(file => utils.isValidExcelFile(file));
        
        if (validFiles.length === 0) {
            app.showNotification('Veuillez sélectionner des fichiers Excel valides', 'warning');
            return;
        }
        
        if (type === 'base') {
            this.handleBaseFileUpload(validFiles[0]);
        } else {
            this.handleComparisonFilesUpload(validFiles);
        }
    }
    
    async handleBaseFileUpload(file) {
        if (!utils.isValidExcelFile(file)) {
            app.showNotification('Format de fichier non valide. Veuillez sélectionner un fichier Excel.', 'error');
            return;
        }
        
        app.showLoading(true);
        
        try {
            this.baseFile = file;
            const result = await api.uploadBaseFile(file);
            
            if (result.success) {
                this.baseFileInfo = result;
                this.displayBaseFileInfo(result);
                this.updateComparisonConfig();
                app.showNotification(result.message, 'success');
            } else {
                app.showNotification(result.error || 'Erreur lors du téléchargement', 'error');
            }
        } catch (error) {
            console.error('Base file upload error:', error);
            app.showNotification('Erreur lors du téléchargement du fichier de base', 'error');
        } finally {
            app.showLoading(false);
        }
    }
    
    async handleComparisonFilesUpload(files) {
        const invalidFiles = files.filter(file => !utils.isValidExcelFile(file));
        if (invalidFiles.length > 0) {
            app.showNotification(`${invalidFiles.length} fichier(s) ignoré(s) - format non valide`, 'warning');
        }
        
        const validFiles = files.filter(file => utils.isValidExcelFile(file));
        if (validFiles.length === 0) {
            app.showNotification('Aucun fichier Excel valide sélectionné', 'error');
            return;
        }
        
        app.showLoading(true);
        
        try {
            this.comparisonFiles = validFiles;
            const result = await api.uploadComparisonFiles(validFiles);
            
            if (result.success) {
                this.compFilesInfo = result.files;
                this.displayComparisonFilesInfo(result);
                this.updateComparisonConfig();
                app.showNotification(result.message, 'success');
            } else {
                app.showNotification(result.error || 'Erreur lors du téléchargement', 'error');
            }
        } catch (error) {
            console.error('Comparison files upload error:', error);
            app.showNotification('Erreur lors du téléchargement des fichiers de comparaison', 'error');
        } finally {
            app.showLoading(false);
        }
    }
    
    displayBaseFileInfo(info) {
        const infoDiv = document.getElementById('base-file-info');
        
        // Update only the base-file-info content, not the preview controls
        infoDiv.innerHTML = `
            <h4>✅ Fichier de base chargé</h4>
            <div class="file-item">
                <p><strong>Nom:</strong> ${info.filename}</p>
                <p><strong>Feuilles trouvées:</strong> ${info.sheets.length}</p>
                <p><strong>Feuilles:</strong> ${info.sheets.join(', ')}</p>
            </div>
        `;
        
        // Update the sheet select options in the existing HTML structure
        const sheetSelect = document.getElementById('base-sheet-select');
        if (sheetSelect) {
            sheetSelect.innerHTML = '';
            info.sheets.forEach(sheet => {
                const option = document.createElement('option');
                option.value = sheet;
                option.textContent = sheet;
                sheetSelect.appendChild(option);
            });
        }
        
        // Show the info and preview sections
        utils.toggleElement(infoDiv, true);
        utils.toggleElement(document.getElementById('base-file-preview'), true);
    }
    
    displayComparisonFilesInfo(info) {
        const infoDiv = document.getElementById('comp-files-info');
        const previewDiv = document.getElementById('comp-files-preview');

        // Info section
        let infoHtml = `<h4>✅ ${info.files.length} fichier(s) de comparaison chargé(s)</h4>`;
        info.files.forEach((file, idx) => {
            infoHtml += `
                <div class="file-item">
                    <p><strong>Nom:</strong> ${file.filename}</p>
                    <p><strong>Feuilles trouvées:</strong> ${file.sheets.length}</p>
                    <p><strong>Feuilles:</strong> ${file.sheets.join(', ')}</p>
                    <div class="preview-controls">
                        <label for="comp-sheet-select-${file.id}">Sélectionner une feuille :</label>
                        <select id="comp-sheet-select-${file.id}">
                            ${file.sheets.map(sheet => `<option value="${sheet}">${sheet}</option>`).join('')}
                        </select>
                        <button id="toggle-comp-preview-${file.id}" class="btn secondary-btn">Afficher l'aperçu</button>
                    </div>
                </div>
            `;
        });
        infoDiv.innerHTML = infoHtml;
        utils.toggleElement(infoDiv, true);

        // Preview section
        let previewHtml = '';
        info.files.forEach((file, idx) => {
            previewHtml += `
                <div id="comp-preview-content-${file.id}" class="comp-preview-content" style="display:none; margin-bottom: 20px;"></div>
            `;
        });
        previewDiv.innerHTML = previewHtml;
        utils.toggleElement(previewDiv, true);

        // Add event listeners for preview buttons and sheet selects
        info.files.forEach((file, idx) => {
            const previewBtn = document.getElementById(`toggle-comp-preview-${file.id}`);
            const sheetSelect = document.getElementById(`comp-sheet-select-${file.id}`);
            const previewContent = document.getElementById(`comp-preview-content-${file.id}`);

            if (previewBtn && sheetSelect && previewContent) {
                previewBtn.addEventListener('click', async () => {
                    if (previewContent.style.display === 'none') {
                        await this.loadCompareFilePreviewSingle(file, sheetSelect.value, previewContent);
                        utils.toggleElement(previewContent, true);
                        previewBtn.textContent = "Masquer l'aperçu";
                    } else {
                        utils.toggleElement(previewContent, false);
                        previewBtn.textContent = "Afficher l'aperçu";
                    }
                });
                sheetSelect.addEventListener('change', async () => {
                    if (previewContent.style.display !== 'none') {
                        await this.loadCompareFilePreviewSingle(file, sheetSelect.value, previewContent);
                    }
                });
            }
        });
    }

    // Helper for previewing a single comparison file/sheet
    async loadCompareFilePreviewSingle(file, sheet, previewContent) {
        if (!sheet || !file) return;
        try {
            const result = await api.previewSheet(file.filename, sheet, false, 'comparison');
            let html = '<h5>Données traitées (après gestion des en-têtes):</h5>';
            html += utils.createTable(result.processed_preview, result.processed_columns, 'data-table preview-table');
            previewContent.innerHTML = html;
        } catch (error) {
            console.error('Preview error:', error);
            previewContent.innerHTML = '<p class="error">Erreur lors du chargement de l\'aperçu</p>';
        }
    }
    
    updateComparisonConfig() {
        if (this.baseFileInfo && this.compFilesInfo.length > 0) {
            this.populateSheetSelector();
            this.populateSheetMappingSelector();
            utils.toggleElement('comparison-config', true);
        }
    }
    
    populateSheetSelector() {
        const container = document.getElementById('selected-sheets-checkboxes');
        if (!container || !this.baseFileInfo) return;

        container.innerHTML = '';
        this.baseFileInfo.sheets.forEach(sheet => {
            const id = `sheet-checkbox-${sheet.replace(/\W/g, '_')}`;
            const wrapper = document.createElement('div');
            wrapper.className = 'checkbox-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = id;
            checkbox.value = sheet;
            checkbox.name = 'selected-sheets';

            const label = document.createElement('label');
            label.htmlFor = id;
            label.textContent = sheet;

            wrapper.appendChild(checkbox);
            wrapper.appendChild(label);
            container.appendChild(wrapper);
        });
    }
    
    populateSheetMappingSelector() {
        const select = document.getElementById('new-sheet-mapping');
        if (!select || !this.baseFileInfo) return;
        
        select.innerHTML = '';
        this.baseFileInfo.sheets.forEach(sheet => {
            const option = document.createElement('option');
            option.value = sheet;
            option.textContent = sheet;
            select.appendChild(option);
        });
    }
    
    setupSiteMappings() {
        const addButton = document.getElementById('add-mapping');
        const codeInput = document.getElementById('new-site-code');
        const sheetSelect = document.getElementById('new-sheet-mapping');
        
        if (addButton) {
            addButton.addEventListener('click', () => {
                const code = codeInput.value.trim().toUpperCase();
                const sheet = sheetSelect.value;
                
                if (code && sheet) {
                    this.addSiteMapping(code, sheet);
                    codeInput.value = '';
                } else {
                    app.showNotification('Veuillez saisir un code de site et sélectionner une feuille', 'warning');
                }
            });
        }
        
        // Allow Enter key to add mapping
        if (codeInput) {
            codeInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    addButton.click();
                }
            });
        }
    }
    
    async addSiteMapping(code, sheet) {
        this.siteMappings[code] = sheet;
        await this.saveSiteMappings();
        this.displaySiteMappings();
        app.showNotification(`Correspondance ajoutée: ${code} → ${sheet}`, 'success');
    }
    
    async removeSiteMapping(code) {
        delete this.siteMappings[code];
        await this.saveSiteMappings();
        this.displaySiteMappings();
        app.showNotification(`Correspondance supprimée: ${code}`, 'info');
    }
    
    displaySiteMappings() {
        const display = document.getElementById('mappings-list');
        if (!display) return;
        
        if (Object.keys(this.siteMappings).length === 0) {
            display.innerHTML = '<p class="no-mappings">Aucune correspondance définie</p>';
            return;
        }
        
        let html = '';
        Object.entries(this.siteMappings).forEach(([code, sheet]) => {
            html += `
                <div class="mapping-item">
                    <span><strong>${code}</strong> → ${sheet}</span>
                    <button class="btn-remove" onclick="uploadManager.removeSiteMapping('${code}')">
                        Supprimer
                    </button>
                </div>
            `;
        });
        
        display.innerHTML = html;
    }
    
    async loadSiteMappings() {
        try {
            const result = await api.getSiteMappings();
            if (result.mappings) {
                this.siteMappings = result.mappings;
                this.displaySiteMappings();
            }
        } catch (error) {
            console.error('Error loading site mappings:', error);
        }
    }
    
    async saveSiteMappings() {
        try {
            await api.setSiteMappings(this.siteMappings);
        } catch (error) {
            console.error('Error saving site mappings:', error);
            app.showNotification('Erreur lors de la sauvegarde des correspondances', 'error');
        }
    }
    
    setupComparisonConfig() {
        const startButton = document.getElementById('start-comparison');
        const resetButton = document.getElementById('reset-config');
        
        if (startButton) {
            startButton.addEventListener('click', this.startComparison.bind(this));
        }
        
        if (resetButton) {
            resetButton.addEventListener('click', this.resetConfiguration.bind(this));
        }
    }
    
    async startComparison() {
        const selectedSheets = Array.from(document.querySelectorAll('input[name="selected-sheets"]:checked'))
            .map(cb => cb.value);

        const modeSelect = document.getElementById('comparison-mode');
        const comparisonMode = modeSelect ? modeSelect.value : 'full';        
        if (window.app && window.app.sessionData) {
            window.app.sessionData.comparisonMode = comparisonMode;
        }
        // Get header detection preference
        const useDynamicDetection = document.getElementById('dynamic-header-detection')?.checked ?? true;

        if (selectedSheets.length === 0) {
            app.showNotification('Veuillez sélectionner au moins une feuille à comparer', 'warning');
            return;
        }

        if (Object.keys(this.siteMappings).length === 0) {
            app.showNotification('Veuillez définir au moins une correspondance de code de site', 'warning');
            return;
        }

        app.showLoading(true);

        try {
            const result = await api.startComparison(
                selectedSheets, 
                comparisonMode,
                useDynamicDetection
            );
            
            if (result.success) {
                app.showNotification('Comparaison terminée avec succès', 'success');
                app.sessionData.comparisonResults = result.results;
                app.sessionData.comparisonResults.mode = comparisonMode;
                app.navigateToPage('comparison');
            } else {
                app.showNotification(result.error || 'Erreur lors de la comparaison', 'error');
            }
        } catch (error) {
            console.error('Comparison error:', error);
            app.showNotification('Erreur lors de la comparaison', 'error');
        } finally {
            app.showLoading(false);
        }
    }
    
    resetConfiguration() {
        // Reset file inputs
        document.getElementById('base-file-input').value = '';
        document.getElementById('comp-files-input').value = '';
        
        // Hide info sections
        utils.toggleElement('base-file-info', false);
        utils.toggleElement('base-file-preview', false);
        utils.toggleElement('comp-files-info', false);
        utils.toggleElement('comp-files-preview', false);
        utils.toggleElement('comparison-config', false);
        
        // Reset data
        this.baseFile = null;
        this.comparisonFiles = [];
        this.baseFileInfo = null;
        this.compFilesInfo = [];
        
        app.showNotification('Configuration réinitialisée', 'info');
    }
    
    async toggleBasePreview() {
        const previewContent = document.getElementById('base-preview-content');
        const toggleButton = document.getElementById('toggle-base-preview');
        
        if (previewContent.style.display === 'none') {
            await this.loadBasePreview();
            utils.toggleElement(previewContent, true);
            toggleButton.textContent = 'Masquer l\'aperçu';
        } else {
            utils.toggleElement(previewContent, false);
            toggleButton.textContent = 'Afficher l\'aperçu';
        }
    }

    async toggleCompareFilePreview(){
        const previewContent = document.getElementById('comp-preview-content');
        const toggleButton = document.getElementById('toggle-comp-preview');

        if (previewContent.style.display === 'none') {
            await this.loadCompareFilePreview();
            utils.toggleElement(previewContent, true);
            toggleButton.textContent = 'Masquer l\'aperçu';
        } else {
            utils.toggleElement(previewContent, false);
            toggleButton.textContent = 'Afficher l\'aperçu';
        }
    }
    
    async loadBasePreview() {
        const sheetSelect = document.getElementById('base-sheet-select');
        const previewContent = document.getElementById('base-preview-content');
        
        if (!sheetSelect.value || !this.baseFileInfo) return;
        
        try {
            const result = await api.previewSheet(this.baseFileInfo.filename, sheetSelect.value, true, 'base');
            
            let html = '<h5>Données traitées (après gestion des en-têtes):</h5>';
            html += utils.createTable(result.processed_preview, result.processed_columns, 'data-table preview-table');
            
            previewContent.innerHTML = html;
        } catch (error) {
            console.error('Preview error:', error);
            previewContent.innerHTML = '<p class="error">Erreur lors du chargement de l\'aperçu</p>';
        }
    }

    async loadCompareFilePreview(){
        const sheetSelect = document.getElementById('comp-sheet-select');
        const previewContent = document.getElementById('comp-preview-content');

        if (!sheetSelect.value || !this.compFilesInfo[sheetSelect.value]) return;

        try {
            const result = await api.previewSheet(
                this.compFilesInfo[sheetSelect.value].filename, 
                sheetSelect.value, 
                false, 
                'comparison'
            );
            
            let html = '<h5>Données traitées (après gestion des en-têtes):</h5>';
            html += utils.createTable(result.processed_preview, result.processed_columns, 'data-table preview-table');

            previewContent.innerHTML = html;
        } catch (error) {
            console.error('Preview error:', error);
            previewContent.innerHTML = '<p class="error">Erreur lors du chargement de l\'aperçu</p>';
        }
    }
    
    async onBaseSheetChange() {
        const previewContent = document.getElementById('base-preview-content');
        if (previewContent.style.display !== 'none') {
            await this.loadBasePreview();
        }
    }

    async onCompSheetChange() {
        const previewContent = document.getElementById('comp-preview-content');
        if (previewContent.style.display !== 'none') {
            await this.loadCompareFilePreview();
        }
    }
}

// Create global upload manager instance
window.uploadManager = new UploadManager();
