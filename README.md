# ECT Technis - Excel Comparison Tool

A powerful tool for comparing and analyzing Excel files with other Excel sources to identify differences and inconsistencies.

## Features

- **File Comparison**: Compare PREPA PHP files with other Excel sources
- **Site Matching**: Intelligent mapping using site codes (LE, BGL, etc.)
- **Difference Detection**: Identify modifications between files
- **Duplicate Detection**: Find duplicate entries across datasets (now using composite keys: Serie, Locomotive, CodeOp)
- **Enhanced Report Generation**: 
  - **Excel Reports**: Visually rich Excel reports with color-coded differences and formatted worksheets
  - **CSV Export**: Optimized classic CSV format with proper encoding for European Excel compatibility
  - **PDF Reports**: Professional PDF reports with data visualization charts and robust formatting
- **Data Visualization**: Charts and graphs in reports for better data interpretation
- **User-Friendly Interface**: Modern and intuitive web application
- **Custom Export Filenames**: Set the export filename from the frontend, respected by the backend
- **Fuzzy Matching**: Enhanced comparison using fuzzy logic for string differences
- **Smooth Documentation Navigation**: In-app help with smooth scrolling and robust anchor navigation
- **Robust Error Handling**: Improved stability for PDF generation and temporary file operations

## Architecture

### Frontend
- **HTML/CSS**: Modular structure and component system
- **JavaScript**: Modular application logic with state management
- **Responsive Interface**: Compatible with various devices and screen resolutions

### Backend
- **REST API**: Endpoints for file processing
- **Comparison Engine**: Advanced logic for analyzing Excel files
- **Data Management**: Structured data processing
- **Reporting System**: Flexible output formats with optimized data handling

## User Guide

Check our [complete user guide](./docs/user_guide.md) for detailed instructions on:
- File uploads
- Configuring comparisons
- Interpreting results
- Generating reports
- Exporting data in different formats

## Installation and Deployment

### Prerequisites
- Modern web browser (Chrome, Firefox, Edge)
- Web server with Python support
- Python 3.9+ with the following packages:
  - pandas
  - reportlab
  - xlsxwriter
  - flask

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alexandre-Caby/excel-comparison-tool
   cd excel-comparison-tool
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend**
   ```bash
   python src/backend/app.py
   ```

4. **Open the interface in a browser**
   ```
   http://localhost:5000
   ```

## Project Structure

```
excel-comparison-tool/
├── docs/                   # Documentation
│   ├── legal/              # Legal documents
│   └── user_guide.md       # User guide
├── src/
│   ├── backend/            # Python server and API
│   │   ├── app.py          # Application entry point
│   ├── core/               # Business logic and Excel processing
│   ├── electron/           # Electron app
│   │   └── main.js         # Electron main process
│   ├── models/             # Data models and schemas
│   ├── utils/              # Utility functions
│   └── frontend/           # User interface
│       ├── css/            # CSS styles
│       ├── js/             # JavaScript scripts
│       ├── pages/          # HTML components
│       ├── images/          # Images and icons
│       └── index.html      # Main page
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies
├── CHANGELOG.md            # Change log
└── README.md
```

## Legal Information

- [Terms of Use](./docs/legal/terms_of_use.md)
- [Privacy Policy](./docs/legal/privacy_policy.md)
- [License](./docs/legal/licence.md)

## Support

For questions or support, please contact the owner.