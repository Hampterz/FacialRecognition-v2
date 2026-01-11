# Setting Up Google Sheets Credentials for Smart Attendance

To use the Smart Attendance feature, you need to configure your Google Sheets credentials.

## Steps:

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable APIs**
   - Navigate to "APIs & Services" → "Library"
   - Enable "Google Sheets API"
   - Enable "Google Drive API"

3. **Create Service Account**
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Give it a name (e.g., "attendance-service")
   - Click "Create and Continue"
   - Skip role assignment, click "Done"

4. **Create and Download Credentials**
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Choose "JSON" format
   - Download the JSON file
   - Save it in your project directory (e.g., `service-account-credentials.json`)

5. **Create Google Spreadsheet**
   - Create a new Google Sheet
   - Set up headers: Column A = "Student", Column B = "Status", Column C = "DATE"
   - Copy the Spreadsheet ID from the URL (the long string between `/d/` and `/edit`)
   - Share the spreadsheet with the service account email (found in the JSON file, field `client_email`)
   - Give it "Editor" permissions

6. **Configure attendance_sheet.py**
   - Open `attendance_sheet.py`
   - Replace `YOUR_SPREADSHEET_ID_HERE` with your actual Spreadsheet ID
   - Replace `path\to\your\service-account-credentials.json` with the actual path to your JSON file

**Important:** Never commit your credentials JSON file or Spreadsheet ID to version control!

