const { contextBridge } = require('electron');
const { marked } = require('marked');

contextBridge.exposeInMainWorld('api', {
    loadUserGuide: async () => {
        const backend = window.localStorage.getItem('BACKEND_URL') || window.BACKEND_URL;
        if (!backend) throw new Error('BACKEND_URL not set');
        
        const response = await fetch(`${backend}/docs/user_guide.md`);
        if (!response.ok) {
            throw new Error(`Failed to load user guide: ${response.status} ${response.statusText}`);
        }
        
        return await response.text();
    },

    loadLegalDocument: async (filename) => {
        const backend = window.localStorage.getItem('BACKEND_URL') || window.BACKEND_URL;
        if (!backend) throw new Error('BACKEND_URL not set');
        
        const response = await fetch(`${backend}/docs/legal/${filename}`);
        if (!response.ok) {
            throw new Error(`Failed to load legal document: ${response.status} ${response.statusText}`);
        }
        
        return await response.text();
    },

    markdownToHtml: (markdown) => {
        try {
            return marked.parse(markdown || '');
        } catch (error) {
            console.error('Error parsing markdown:', error);
            return markdown || '';
        }
    }
});
