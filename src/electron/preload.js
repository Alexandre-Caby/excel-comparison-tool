const { contextBridge } = require('electron');
const axios = require('axios');
const { marked } = require('marked');

contextBridge.exposeInMainWorld('api', {
    loadUserGuide: async () => {
        const backend = window.localStorage.getItem('BACKEND_URL');
        if (!backend) throw new Error('BACKEND_URL not set');
        const res = await axios.get(`${backend}/docs/user_guide.md`);
        return res.data;
    },

    loadLegalDocument: async (filename) => {
        const backend = window.localStorage.getItem('BACKEND_URL');
        if (!backend) throw new Error('BACKEND_URL not set');
        const res = await axios.get(`${backend}/docs/legal/${filename}`);
        return res.data;
    },

    markdownToHtml: (markdown) => {
        return marked.parse(markdown || '');
    }
});
