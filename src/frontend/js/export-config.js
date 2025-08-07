// Export configuration for different types
const ExportConfig = {
    comparison: {
        formats: ['excel', 'csv', 'pdf'],
        defaultOptions: {
            summary: true,
            differences: true,
            duplicates: true,
            statistics: true
        },
        filenameSuffix: 'comparison_report'
    },
    
    analysis: {
        formats: ['excel', 'csv', 'pdf'],
        defaultOptions: {
            summary: true,
            concatenated: true,
            conflicts: true,
            weekly_planning: true,
            equipment_analysis: true
        },
        filenameSuffix: 'analysis_report'
    },

    generateFilename: function(type, customName) {
        const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
        const baseName = customName || this[type].filenameSuffix;
        return `${baseName}_${timestamp}`;
    },

    validateOptions: function(type, options) {
        const defaultOpts = this[type].defaultOptions;
        return { ...defaultOpts, ...options };
    }
};

window.ExportConfig = ExportConfig;