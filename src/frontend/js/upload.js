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
        const previewDiv = document.getElementById('base-file-preview');
        
        infoDiv.innerHTML = `
            <h4>✅ Fichier de base chargé</h4>
            <p><strong>Nom:</strong> ${info.filename}</p>
            <p><strong>Feuilles trouvées:</strong> ${info.sheets.length}</p>
            <p><strong>Feuilles:</strong> ${info.sheets.join(', ')}</p>
        `;
        
        // Populate sheet selector
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
        
        utils.toggleElement(infoDiv, true);
        utils.toggleElement(previewDiv, true);
    }
    
    displayComparisonFilesInfo(info) {
        const infoDiv = document.getElementById('comp-files-info');
        
        let html = `<h4>✅ ${info.files.length} fichier(s) de comparaison chargé(s)</h4>`;
        
        info.files.forEach((file, index) => {
            html += `
                <div class="file-item">
                    <p><strong>Fichier ${index + 1}:</strong> ${file.filename}</p>
                    <p><strong>Feuilles:</strong> ${file.sheets.join(', ')}</p>
                </div>
            `;
        });
        
        infoDiv.innerHTML = html;
        utils.toggleElement(infoDiv, true);
    }
    
    updateComparisonConfig() {
        if (this.baseFileInfo && this.compFilesInfo.length > 0) {
            this.populateSheetSelector();
            this.populateSheetMappingSelector();
            utils.toggleElement('comparison-config', true);
        }
    }
    
    populateSheetSelector() {
        const select = document.getElementById('selected-sheets');
        if (!select || !this.baseFileInfo) return;
        
        select.innerHTML = '';
        this.baseFileInfo.sheets.forEach(sheet => {
            const option = document.createElement('option');
            option.value = sheet;
            option.textContent = sheet;
            select.appendChild(option);
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
        const selectedSheets = Array.from(document.getElementById('selected-sheets').selectedOptions)
            .map(option => option.value);
        
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
            const result = await api.startComparison(selectedSheets);
            
            if (result.success) {
                app.showNotification('Comparaison terminée avec succès', 'success');
                app.sessionData.comparisonResults = result.results;
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
    
    async loadBasePreview() {
        const sheetSelect = document.getElementById('base-sheet-select');
        const previewContent = document.getElementById('base-preview-content');
        
        if (!sheetSelect.value || !this.baseFileInfo) return;
        
        try {
            const result = await api.previewSheet(this.baseFileInfo.filename, sheetSelect.value, true);
            
            let html = '<h5>Aperçu brut (lignes d\'en-tête):</h5>';
            html += utils.createTable(result.raw_preview, result.raw_columns, 'data-table preview-table');
            
            html += '<h5>Données traitées (après gestion des en-têtes):</h5>';
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
}

// Create global upload manager instance
window.uploadManager = new UploadManager();
