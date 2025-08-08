// Main application logic

class ECTApp {
    constructor() {
        this.currentPage = 'home';
        this.sessionData = {
            baseFileInfo: null,
            compFilesInfo: [],
            siteMappings: { "LE": "Lens", "BGL": "BGL" },
            comparisonResults: null,
            reports: []
        };
        
        this.init();
    }
    
    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.loadInitialData();
        this.loadHomePage(); // Load home page by default
    }
    
    setupNavigation() {
        const navButtons = document.querySelectorAll('.nav-button');
        navButtons.forEach(button => {
            button.addEventListener('click', () => {
                const page = button.dataset.page;
                this.navigateToPage(page);
            });
        });
    }
    
    async navigateToPage(page) {
        // Update navigation
        document.querySelectorAll('.nav-button').forEach(button => {
            button.classList.remove('active');
        });
        
        const activeButton = document.querySelector(`.nav-button[data-page="${page}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
        
        this.currentPage = page;
        
        // Load page content
        await this.loadPageContent(page);
    }
    
    async loadPageContent(page) {
        const pageContainer = document.getElementById('page-container');
        
        try {
            // Load the HTML for the page
            const response = await fetch(`pages/${page}.html`);
            if (!response.ok) {
                throw new Error(`Failed to load page: ${page}`);
            }
            
            const html = await response.text();
            pageContainer.innerHTML = html;
            
            // Initialize page-specific functionality
            this.initPageLogic(page);
            
        } catch (error) {
            console.error('Error loading page:', error);
            pageContainer.innerHTML = `
                <div class="error-box">
                    <h2>Erreur de chargement</h2>
                    <p>Impossible de charger la page "${page}". Veuillez réessayer.</p>
                    <button class="btn primary-btn" onclick="app.navigateToPage('home')">
                        Retour à l'accueil
                    </button>
                </div>
            `;
        }
    }
    
    initPageLogic(page) {
        switch (page) {
            case 'home':
                this.initHomePage();
                break;
            case 'upload':
                this.initUploadPage();
                break;
            case 'comparison':
                this.initComparisonPage();
                break;
            case 'reports':
                this.initReportsPage();
                break;
            case 'analysis':
                this.initAnalysisPage();
                break;
            case 'help':
                this.initHelpPage();
                break;
            case 'legal':
                this.initLegalPage();
                break;
        }
    }
    
    initHomePage() {
        // Set up quick start buttons
        const quickStartButtons = document.querySelectorAll('.quick-start-button');
        quickStartButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetPage = button.dataset.page;
                this.navigateToPage(targetPage);
            });
        });
    }
    
    initUploadPage() {
        // Initialize upload functionality with a small delay to ensure DOM is ready
        setTimeout(() => {
            try {
                if (typeof UploadManager !== 'undefined') {
                    if (!window.uploadManager) {
                        window.uploadManager = new UploadManager();
                    }
                    window.uploadManager.init();
                } else {
                    console.error('UploadManager class not found. Make sure upload.js is loaded.');
                    this.showNotification('Erreur: Module de téléchargement non disponible', 'error');
                }
            } catch (error) {
                console.error('Error initializing upload page:', error);
                this.showNotification('Erreur lors de l\'initialisation de la page de téléchargement', 'error');
            }
        }, 100);
    }
    
    initComparisonPage() {
        // Initialize comparison functionality with a small delay to ensure DOM is ready
        setTimeout(() => {
            try {
                if (typeof ComparisonManager !== 'undefined') {
                    if (!window.comparisonManager) {
                        window.comparisonManager = new ComparisonManager();
                    }
                    window.comparisonManager.init();
                } else {
                    console.warn('ComparisonManager class not found.');
                }
            } catch (error) {
                console.error('Error initializing comparison page:', error);
            }
        }, 100);
    }
    
    initReportsPage() {
        // Initialize reports functionality with a small delay to ensure DOM is ready
        setTimeout(() => {
            try {
                if (typeof ReportsManager !== 'undefined') {
                    if (!window.reportsManager) {
                        window.reportsManager = new ReportsManager();
                    }
                    window.reportsManager.init();
                } else {
                    console.warn('ReportsManager class not found.');
                }
            } catch (error) {
                console.error('Error initializing reports page:', error);
            }
        }, 100);
    }

    initAnalysisPage() {
        // Initialize analysis functionality with a small delay to ensure DOM is ready
        setTimeout(() => {
            try {
                if (typeof AnalysisManager !== 'undefined') {
                    if (!window.analysisManager) {
                        window.analysisManager = new AnalysisManager();
                    }
                    window.analysisManager.init();
                } else {
                    console.warn('AnalysisManager class not found.');
                }
            } catch (error) {
                console.error('Error initializing analysis page:', error);
            }
        }, 100);
    }
    
    async initHelpPage() {
        // console.log('Initializing help page...');
        const helpContent = document.getElementById('help-content');
        if (!helpContent) return;
        
        // Show loading state
        helpContent.innerHTML = `
            <div class="loading-docs">
                <div class="loading-spinner"></div>
                <p>Chargement de la documentation...</p>
            </div>
        `;
        
        try {
            // Directly fetch the markdown file
            const response = await fetch(`${window.BACKEND_URL || 'http://localhost:5000'}/api/docs/user_guide.md`);
            
            if (response.ok) {
                const markdown = await response.text();
                const html = this.simpleMarkdownToHtml(markdown);
                
                // Display the content
                helpContent.innerHTML = `
                    <div class="help-card">
                        <div class="card-body help-body">
                            ${html}
                        </div>
                    </div>
                `;
                console.log('Help content loaded successfully');
            } else {
                throw new Error(`Failed to load help: ${response.status}`);
            }
        } catch (error) {
            console.error('Error loading help content:', error);
            // Show fallback content
            helpContent.innerHTML = `
                <div class="help-card">
                    <div class="card-body help-body">
                        <!-- Your fallback help content -->
                        <h1>Guide d'utilisation - ECT Technis</h1>
                        <h2>Démarrage rapide</h2>
                        <!-- Rest of your fallback content -->
                    </div>
                </div>
            `;
        }
    }
    
    async initLegalPage() {
        // console.log('Initializing legal page...');
        const legalContent = document.getElementById('legal-content');
        if (!legalContent) return;
        
        // Set up tab handling
        const tabs = document.querySelectorAll('.legal-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Update active state
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Load the selected document
                const docType = tab.getAttribute('data-doc');
                this.loadLegalDocument(docType);
            });
        });
        
        // Load initial document
        const activeTab = document.querySelector('.legal-tab.active');
        if (activeTab) {
            const docType = activeTab.getAttribute('data-doc');
            this.loadLegalDocument(docType);
        }
    }

    async loadLegalDocument(docType) {
        const legalContent = document.getElementById('legal-content');
        if (!legalContent) return;
        
        // Map doc type to filename
        const fileMap = {
            'terms': 'terms_of_use.md',
            'privacy': 'privacy_policy.md', 
            'license': 'licence.md'
        };
        
        const filename = fileMap[docType];
        if (!filename) return;
        
        // Show loading state
        legalContent.innerHTML = `
            <div class="loading-docs">
                <div class="loading-spinner"></div>
                <p>Chargement des mentions légales...</p>
            </div>
        `;
        
        try {
            // Directly fetch the markdown file
            const response = await fetch(`${window.BACKEND_URL || 'http://localhost:5000'}/api/docs/legal/${filename}`);
            
            if (response.ok) {
                const markdown = await response.text();
                const html = this.simpleMarkdownToHtml(markdown);
                
                // Display the content
                legalContent.innerHTML = `
                    <div class="legal-card">
                        <div class="card-body legal-body">
                            ${html}
                        </div>
                    </div>
                `;
                console.log(`Legal document ${docType} loaded successfully`);
            } else {
                throw new Error(`Failed to load legal document: ${response.status}`);
            }
        } catch (error) {
            console.error(`Error loading legal document ${docType}:`, error);
            // Show fallback content - use your existing fallback content
            legalContent.innerHTML = `
                <div class="legal-card">
                    <div class="card-body legal-body">
                        <h1>Mentions Légales - ${docType.toUpperCase()}</h1>
                        <p>Impossible de charger le document. Veuillez réessayer plus tard.</p>
                    </div>
                </div>
            `;
        }
    }
    
    // Simple markdown to HTML converter
    simpleMarkdownToHtml(markdown) {
        return markdown
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^#### (.*$)/gm, '<h4>$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="markdown-link">$1</a>')
            .replace(/^- (.*$)/gm, '<li>$1</li>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/^(?!<[h|l|p|a])(.+)$/gm, '<p>$1</p>')
            .replace(/<p><li>/g, '<ul><li>')
            .replace(/<\/li><\/p>/g, '</li></ul>')
            .replace(/\n/g, '<br>')
            .replace(/https?:\/\/[^\s]+/g, (url) => `<a href="${url}" target="_blank" class="markdown-link">${url}</a>`);
    }
    
    async loadHomePage() {
        await this.loadPageContent('home');
    }
    
    setupEventListeners() {
        // Global event listeners
        window.addEventListener('error', (event) => {
            console.error('Application error:', event.error);
            this.showNotification('Une erreur est survenue', 'error');
        });
        
        // Handle window beforeunload
        window.addEventListener('beforeunload', function(event) {
            navigator.sendBeacon('/shutdown');
        });
        
        // Handle help button click
        document.addEventListener('click', (event) => {
            if (event.target.closest('#help-button')) {
                this.navigateToPage('help');
            }
            
            // Handle legal link in footer
            if (event.target.id === 'legal-link') {
                event.preventDefault();
                this.navigateToPage('legal');
            }
        });
    }
    
    async loadInitialData() {
        try {
            // Check if backend is available
            await api.healthCheck();
            
            // Load site mappings
            const mappings = await api.getSiteMappings();
            if (mappings.mappings) {
                this.sessionData.siteMappings = mappings.mappings;
            }
            
            // Load reports
            const reports = await api.getReports();
            if (reports.reports) {
                this.sessionData.reports = reports.reports;
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Connexion au serveur impossible', 'warning');
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '1rem 2rem',
            borderRadius: '4px',
            color: 'white',
            fontWeight: '500',
            zIndex: '10000',
            opacity: '0',
            transform: 'translateY(-20px)',
            transition: 'all 0.3s ease'
        });
        
        // Set background color based on type
        const colors = {
            'info': '#007147',
            'success': '#2CA02C',
            'warning': '#FFD250',
            'error': '#D62728'
        };
        notification.style.backgroundColor = colors[type] || colors.info;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        });
        
        // Remove after delay
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
    
    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = show ? 'flex' : 'none';
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new ECTApp();
});
