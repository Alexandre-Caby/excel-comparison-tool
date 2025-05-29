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
            case 'help':
                this.loadHelpContent();
                break;
            case 'legal':
                this.loadLegalContent();
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
    
    async loadHelpContent() {
        try {
            const helpContent = document.getElementById('help-content');
            if (!helpContent) return;
            
            // Load content from user guide markdown
            const response = await fetch('/docs/user_guide.md');
            if (!response.ok) {
                throw new Error('Failed to load help content');
            }
            
            const markdown = await response.text();
            // Display markdown content (simple implementation)
            helpContent.innerHTML = `
                <div class="card">
                    <div class="card-header">Guide d'utilisation</div>
                    <div class="card-body markdown-body">
                        ${this.simpleMarkdownToHtml(markdown)}
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading help content:', error);
            this.showNotification('Erreur lors du chargement de l\'aide', 'error');
        }
    }
    
    async loadLegalContent() {
        try {
            const legalContent = document.getElementById('legal-content');
            const tabs = document.querySelectorAll('.legal-tab');
            
            if (!legalContent || !tabs.length) return;
            
            // Fallback content for each document type
            const fallbackContent = {
                'terms_of_use.md': {
                    title: 'Conditions d\'utilisation',
                    content: `
                        <h1>Conditions de service</h1>
                        <h2>1. Acceptation des conditions</h2>
                        <p>En utilisant notre service, vous acceptez ces conditions.</p>
                        
                        <h2>2. Description du service</h2>
                        <p>Notre service vous permet de comparer des fichiers Excel.</p>
                        
                        <h2>3. Obligations de l'utilisateur</h2>
                        <p>L'utilisateur s'engage à :</p>
                        <ul>
                            <li>Utiliser le service conformément à la législation en vigueur.</li>
                            <li>Ne pas utiliser le service à des fins illégales.</li>
                            <li>Respecter les droits des tiers.</li>
                        </ul>
                        
                        <h2>4. Limitation de responsabilité</h2>
                        <p>Notre responsabilité ne saurait être engagée en cas de dommages résultant de l'utilisation du service.</p>
                    `
                },
                'privacy_policy.md': {
                    title: 'Politique de confidentialité',
                    content: `
                        <h1>Politique de confidentialité</h1>
                        <h2>Collecte des données</h2>
                        <p>Cet outil traite uniquement les fichiers Excel que vous téléchargez pour les comparer.</p>
                        
                        <h2>Utilisation des données</h2>
                        <ul>
                            <li>Les fichiers sont traités localement</li>
                            <li>Aucune donnée n'est stockée de manière permanente</li>
                            <li>Les données sont supprimées après la session</li>
                        </ul>
                        
                        <h2>Sécurité</h2>
                        <p>Nous mettons en œuvre des mesures techniques appropriées pour protéger vos données.</p>
                        
                        <h2>Vos droits</h2>
                        <p>Vous pouvez à tout moment :</p>
                        <ul>
                            <li>Supprimer vos fichiers téléchargés</li>
                            <li>Redémarrer une nouvelle session</li>
                            <li>Contacter le support pour toute question</li>
                        </ul>
                    `
                },
                'licence.md': {
                    title: 'Licence',
                    content: `
                        <h1>Licence d'utilisation</h1>
                        <h2>Droits d'utilisation</h2>
                        <p>Ce logiciel est fourni sous licence d'utilisation limitée.</p>
                        
                        <h2>Permissions</h2>
                        <ul>
                            <li>Utilisation à des fins professionnelles</li>
                            <li>Comparaison de fichiers Excel</li>
                            <li>Génération de rapports</li>
                        </ul>
                        
                        <h2>Restrictions</h2>
                        <ul>
                            <li>Pas de redistribution autorisée</li>
                            <li>Pas de modification du code source</li>
                            <li>Utilisation limitée aux besoins de l'organisation</li>
                        </ul>
                        
                        <h2>Support</h2>
                        <p>Le support technique est disponible pendant les heures ouvrables.</p>
                        
                        <h2>Mise à jour</h2>
                        <p>Cette licence peut être mise à jour. Les utilisateurs seront informés des modifications importantes.</p>
                    `
                }
            };
            
            // Function to load a legal document
            const loadLegalDoc = async (docName) => {
                legalContent.innerHTML = `
                    <div class="loading-docs">
                        <div class="loading-spinner"></div>
                        <p>Chargement du document...</p>
                    </div>
                `;
                
                try {
                    const response = await fetch(`../../docs/legal/${docName}`);
                    
                    if (!response.ok) {
                        throw new Error(`Failed to load document: ${docName}`);
                    }
                    
                    const markdown = await response.text();
                    const formattedContent = this.simpleMarkdownToHtml(markdown);
                    
                    let docTitle = 'Document juridique';
                    if (docName === 'terms_of_use.md') docTitle = 'Conditions d\'utilisation';
                    if (docName === 'privacy_policy.md') docTitle = 'Politique de confidentialité';
                    if (docName === 'licence.md') docTitle = 'Licence';
                    
                    legalContent.innerHTML = `
                        <div class="card">
                            <div class="card-header">${docTitle}</div>
                            <div class="card-body markdown-body">${formattedContent}</div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error loading document:', error);
                    
                    // Use fallback content
                    const fallback = fallbackContent[docName];
                    if (fallback) {
                        legalContent.innerHTML = `
                            <div class="card">
                                <div class="card-header">${fallback.title}</div>
                                <div class="card-body markdown-body">${fallback.content}</div>
                            </div>
                        `;
                    } else {
                        legalContent.innerHTML = `
                            <div class="card">
                                <div class="card-header">Erreur de chargement</div>
                                <div class="card-body">
                                    <div class="error-box">
                                        <h3>Document non disponible</h3>
                                        <p>Le document "${docName}" n'est pas disponible pour le moment.</p>
                                        <p>Veuillez contacter le support technique si ce problème persiste.</p>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                }
            };
            
            // Set up tab click events
            tabs.forEach(tab => {
                tab.addEventListener('click', () => {
                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    tab.classList.add('active');
                    
                    // Load document
                    const docName = tab.dataset.doc;
                    loadLegalDoc(docName);
                });
            });
            
            // Load initial document
            loadLegalDoc('terms_of_use.md');
            
        } catch (error) {
            console.error('Error preparing legal content:', error);
        }
    }
    
    // Simple markdown to HTML converter
    simpleMarkdownToHtml(markdown) {
        // This is a very basic implementation - replace with a proper markdown parser for production
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
        window.addEventListener('beforeunload', (event) => {
            // Clean up if needed
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
