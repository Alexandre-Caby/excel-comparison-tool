# Excel Comparison Tool

A powerful tool for comparing and analyzing Excel files to identify differences, duplicates, and inconsistencies.

## Features

- Compare two Excel files to identify differences
- Match data by site or sheet names
- Flexible column matching options
- Generate detailed comparison reports
- Export results in various formats
- Interactive web-based interface

## Usage Options

### Option 1: Standalone Executable (Recommended for Users)

1. Download the latest release from the [Releases page](https://github.com/alexandre-caby/excel-comparison-tool/releases)
2. Run the executable - no installation required
3. The application will open in your default web browser

### Option 2: Run from Source (For Developers)

#### Prerequisites

- Python 3.9 or higher
- Required Python packages:
  - streamlit
  - pandas
  - openpyxl
  - xlsxwriter

#### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/alexandre-caby/excel-comparison-tool.git
   cd excel-comparison-tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run main.py
   ```
   if it doesn't work, run the build script:
   ```bash
   run_app.bat
   ```

## Building the Executable

To build your own standalone executable:

### Method 1: Using the build script

```bash
# On Windows
build.bat
```

### Method 2: Manual build with PyInstaller

```bash
# Install required build tools
pip install pyinstaller

# Build the executable
pyinstaller --onefile --noconsole --add-data "src;src" --add-data "static;static" --name "Excel_Comparison_Tool" run.py
```

## How to Use

1. **Upload Files**: 
   - Upload your base PREPA PHP file
   - Upload one or more comparison files

2. **Configure Comparison**:
   - Select sheets to compare
   - Configure site mappings (e.g., "LE" → "lens")

3. **View Results**:
   - Browse differences between files 
   - Identify modified entries
   - Check for duplicate records

4. **Export Reports**:
   - Generate Excel or CSV reports
   - Save for future reference

## Security

The standalone executable includes code obfuscation to protect intellectual property. When building from source, the GitHub Actions workflow automatically handles obfuscation using PyArmor.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Streamlit for the web interface framework
- Pandas for the data processing capabilities