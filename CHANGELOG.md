# Excel Comparison Tool - Changelog

## Version 1.2.0

### New features
- **PHP Analysis Module**: Added comprehensive analysis system for maintenance program files
- **Equipment Analysis**: Track immobilization days, valid/invalid appointments, and operations by equipment
- **Weekly Planning Analysis**: View scheduled maintenance by week with occupancy metrics
- **Data Quality Detection**: Automated identification of date issues, missing values, and format problems
- **Interactive Help System**: Added collapsible information panels explaining all metrics and calculations
- **Enhanced Tooltips**: Added detailed explanations for all summary metrics
- **Concatenated Data View**: View and filter raw maintenance data with consistent calculations
- **Conflict Detection**: Intelligent identification of data issues with severity levels
- **Excel Export**: Export complete analysis results to Excel for further processing

### Technical Improvements
- **Robust Date Processing**: Enhanced date parsing with multiple format support and validation
- **Consistent Time Calculations**: Standardized day/hour calculations across all analysis views
- **Non-destructive Validation**: Data quality issues are flagged rather than removed for better transparency
- **Parallel Operation Handling**: Proper handling of multiple operations on same equipment/date
- **Memory Optimization**: Improved handling of large datasets with reduced memory usage
- **Enhanced Frontend Visualization**: Severity indicators and color-coding for data issues

### Bug Fixes
- Fixed issues with date format detection and parsing
- Corrected calculation of immobilization days for equipment with parallel operations
- Adjusted threshold for excessive immobilization detection to accommodate locomotives
- Resolved warnings from pandas date parsing with proper format specification
- Fixed display of metrics with proper rounding and number formatting

## Version 1.1.2

### Bug Fixes
- Fix comparison with the week number
- Fix the report generation (Excel, CSV, PDF), adding the week number in it
- Correct the launch of the Electron app, use PyInstaller instead of python path

## Version 1.1.1

### Bug Fixes
- Fix not found files when launching the app
- Add logging
- Add verification for production mode

## Version 1.1.0

### New Features
- Added detection and display of duplicates ("doublons détectés") in both summary and detailed report views
- Exported reports (Excel, CSV, PDF) now include only the relevant sections (differences, duplicates, or summary) according to the selected comparison mode
- The export filename can now be set from the frontend and is respected by the backend for downloads
- Enhanced comparison (fuzzing and vectorization of dataframes)
- **Enhanced Excel Reports**: Added color-coded rows for different status types (added/modified/removed)
- **Improved Excel Formatting**: Added emoji icons and better visual organization of data
- **Classic CSV Export**: Implemented optimized CSV format with proper European Excel compatibility
- **Robust Chart Generation**: Added proper chart visualization to PDF reports

### Bug Fixes
- Fixed issue where the number of duplicates was not displayed in the metrics card on the comparison page
- Fixed issue where the detailed data section in reports did not show the correct headers or content for differences and duplicates
- Fixed ambiguous DataFrame truth value error in backend comparison logic
- Improved robustness of frontend event handling for documentation navigation
- Fixed PDF report generation issues with complex HTML content
- Corrected statistics calculations for differences by category
- Resolved temporary file access issues in chart generation
- Fixed CSV column alignment and data formatting
- Corrected calculation of added/modified/removed entries in reports

### Technical Improvements
- Enhanced markdown-to-HTML conversion for the help page, including better handling of links and headings
- Improved backend and frontend synchronization for report data structure (including comparison mode and duplicates)
- Better temporary file management with proper cleanup
- Enhanced error handling for PDF generation process
- Improved data formatting for dates and special characters in exports
- Optimized memory usage during report generation

## Version 1.0.2

### New Features
- Use of Waitress for production environment

## Version 1.0.1

### Bug Fixes
- Fixed issue with frozen imports in the main application
- Resolved workflow errors

## Version 1.0.0

### New Features
- Initial release of Excel Comparison Tool
- Compare Excel files between base files (PREPA PHP) and comparison files
- Site-based comparisons
- Report generation in Excel and CSV formats
- Support for multiple comparison files

### Technical Improvements
- Clean, optimized code structure
- Electron-based desktop application
- Excel processing optimized for performance

### Bug Fixes
- Fixed issue with empty rows in comparisons
- Improved error handling for file loading