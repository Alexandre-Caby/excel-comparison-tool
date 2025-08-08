const { contextBridge } = require('electron');

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
        if (!markdown) return '';
        
        try {
            return markdown
                .replace(/^# (.+)$/gm, '<h1>$1</h1>')
                .replace(/^## (.+)$/gm, '<h2>$1</h2>')
                .replace(/^### (.+)$/gm, '<h3>$1</h3>')
                .replace(/^#### (.+)$/gm, '<h4>$1</h4>')
                .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.+?)\*/g, '<em>$1</em>')
                .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" class="markdown-link">$1</a>')
                .replace(/^- (.+)$/gm, '<li>$1</li>')
                .replace(/^\d+\. (.+)$/gm, '<li class="numbered">$1</li>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/^(?!<[h|l|a])(.+)$/gm, '<p>$1</p>')
                .replace(/<p><h/g, '<h')
                .replace(/<\/h([1-6])><\/p>/g, '</h$1>')
                .replace(/<p><li>/g, '<ul><li>')
                .replace(/<p><li class="numbered">/g, '<ol><li>')
                .replace(/<\/li><\/p>/g, '</li></ul>')
                .replace(/<\/li><\/p>/g, '</li></ol>');
        } catch (error) {
            console.error('Error parsing markdown:', error);
            return markdown;
        }
    }
});
