import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Spreadsheet ID - Replace with your Google Spreadsheet ID
# Get this from the URL: https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
SPREADSHEET_ID = "1Oi46a1DOYaqfjsYZm17S5QFyMyBr3CFvKJIBnNn4UL8"

# Credentials file path - Replace with path to your service account JSON file
# Download from Google Cloud Console → IAM & Admin → Service Accounts
CREDENTIALS_PATH = r"smart-attendence-483504-fca241494077.json"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Initialize client
_client = None
_sheet = None

def _get_client():
    """Get or create the gspread client."""
    global _client, _sheet
    if _client is None:
        if not os.path.exists(CREDENTIALS_PATH):
            print(f"Error: Credentials file not found at {CREDENTIALS_PATH}")
            return None, None
        
        try:
            print(f"Loading credentials from: {CREDENTIALS_PATH}")
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
            print("Authorizing with Google Sheets API...")
            _client = gspread.authorize(creds)
            print(f"Opening spreadsheet with ID: {SPREADSHEET_ID}")
            _sheet = _client.open_by_key(SPREADSHEET_ID).sheet1
            print("Connected to Google Sheet successfully!")
        except FileNotFoundError as e:
            print(f"ERROR: Credentials file not found: {e}")
            return None, None
        except PermissionError as e:
            error_msg = (
                "PERMISSION ERROR: Google Sheets API is not enabled for this project.\n"
                "Please enable it by visiting:\n"
                "https://console.developers.google.com/apis/api/sheets.googleapis.com/overview\n"
                "Then wait a few minutes and try again."
            )
            print(f"ERROR: {error_msg}")
            return None, None
        except Exception as e:
            import traceback
            error_str = str(e)
            if "API has not been used" in error_str or "is disabled" in error_str:
                error_msg = (
                    "ERROR: Google Sheets API is not enabled.\n"
                    "Please enable it in Google Cloud Console:\n"
                    "https://console.developers.google.com/apis/api/sheets.googleapis.com/overview\n"
                    f"Original error: {error_str}"
                )
                print(error_msg)
            else:
                print(f"ERROR connecting to Google Sheet: {e}")
                print(f"Error type: {type(e).__name__}")
                print(f"Traceback:\n{traceback.format_exc()}")
            return None, None
    return _client, _sheet

def get_today_column():
    """
    Find which column contains today's date.
    Returns the column number (1-indexed) or None if not found.
    """
    from datetime import datetime
    
    client, sheet = _get_client()
    if sheet is None:
        return None
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        all_values = sheet.get_all_values()
        
        # Check Column C (column index 2) for today's date
        # Look through all rows in Column C
        for row_idx, row in enumerate(all_values, 1):
            if len(row) > 2:
                cell_value = row[2].strip() if len(row) > 2 else ""  # Column C
                if cell_value == today:
                    print(f"Found today's date ({today}) in Column C at row {row_idx}")
                    return 3  # Column C is column 3
        
        print(f"WARNING: Today's date ({today}) not found in Column C")
        return 3  # Default to Column C if not found
    except Exception as e:
        print(f"ERROR finding today's column: {e}")
        return 3  # Default to Column C on error

def mark_present(name: str):
    """
    Find the student name in column A within today's archived section.
    Write 'Present' into Column B (Status) on the same row as the student name in today's section.
    The date should be in Column C (DATE).
    Do nothing if the name is not found.
    """
    from datetime import datetime
    
    client, sheet = _get_client()
    if sheet is None:
        print(f"ERROR: Could not connect to Google Sheet. Check credentials at: {CREDENTIALS_PATH}")
        return
    
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get all data to find today's section
        all_values = sheet.get_all_values()
        
        # Find the row where today's date is in Column C
        today_date_row = None
        for row_idx, row in enumerate(all_values, 1):
            if len(row) > 2:
                cell_value = row[2].strip() if len(row) > 2 else ""  # Column C
                if cell_value == today:
                    today_date_row = row_idx
                    break
        
        if today_date_row is None:
            print(f"WARNING: Today's date ({today}) not found in Column C.")
            print(f"   This might be the first time running today. Trying to find student in original section...")
            # Fallback to original section if today's date not found
            all_names = sheet.col_values(1)
            names = [n.strip() if n else "" for n in all_names]
            name_clean = name.strip()
            if name_clean in names:
                student_row = names.index(name_clean) + 1
                current_value = sheet.cell(student_row, 2).value
                current_value = current_value.strip() if current_value else ""
                if current_value != "Present":
                    sheet.update_cell(student_row, 2, "Present")
                    print(f"SUCCESS: {name_clean} marked present in original section (Row {student_row}, Column B)")
                else:
                    print(f"INFO: {name_clean} is already marked present (Row {student_row}, Column B)")
            else:
                print(f"WARNING: '{name_clean}' not found in Google Sheet")
            return
        
        # Find the student name in Column A, starting from today's date row
        # The student names should be in the rows immediately following the date row
        name_clean = name.strip()
        student_row = None
        
        # Look for the name in Column A, starting from the date row (same row or rows below)
        # Check up to 50 rows below the date (should be enough for all students)
        for offset in range(0, 50):
            row_idx = today_date_row + offset
            if row_idx <= len(all_values):
                row = all_values[row_idx - 1] if row_idx > 0 else []
                if len(row) > 0:
                    cell_name = row[0].strip()  # Column A
                    if cell_name == name_clean:
                        student_row = row_idx
                        break
        
        if student_row is None:
            print(f"WARNING: '{name_clean}' not found in today's section (starting from row {today_date_row})")
            print(f"   Looking in rows {today_date_row} to {today_date_row + 50}")
            return
        
        # Check current value in Column B (Status) for today's section
        current_value = sheet.cell(student_row, 2).value  # Column B (Status)
        current_value = current_value.strip() if current_value else ""

        if current_value != "Present":
            sheet.update_cell(student_row, 2, "Present")
            print(f"SUCCESS: {name_clean} marked present in today's section (Row {student_row}, Column B - Status)")
        else:
            print(f"INFO: {name_clean} is already marked present in today's section (Row {student_row}, Column B - Status)")
            
    except Exception as e:
        import traceback
        print(f"ERROR updating Google Sheet: {e}")
        print(f"Traceback: {traceback.format_exc()}")

def get_present_students():
    """
    Get all students marked as 'Present' from the spreadsheet.
    Returns a set of student names.
    """
    client, sheet = _get_client()
    if sheet is None:
        return set()
    
    try:
        # Get all data from columns A and B
        all_values = sheet.get_all_values()
        
        present_students = set()
        for row in all_values:
            if len(row) >= 2:
                name = row[0].strip()  # Column A
                status = row[1].strip() if len(row) > 1 else ""  # Column B
                
                if name and status == "Present":
                    present_students.add(name)
        
        return present_students
    except Exception as e:
        print(f"Error reading Google Sheet: {e}")
        return set()

def get_all_students():
    """
    Get all student names from column A.
    Returns a list of student names.
    """
    client, sheet = _get_client()
    if sheet is None:
        return []
    
    try:
        names = sheet.col_values(1)  # column A
        # Filter out empty strings
        return [name.strip() for name in names if name.strip()]
    except Exception as e:
        print(f"Error reading student names from Google Sheet: {e}")
        return []

def archive_students_for_today(trained_names=None):
    """
    Set up spreadsheet headers if needed, then archive trained student names 2 rows below the previous day's data.
    Structure: Column A = Student, Column B = Status, Column C = DATE
    Add the current date in Column C on the same row as the first student name.
    
    Args:
        trained_names: List of trained person names. If None, gets from Column A (legacy behavior).
    
    Returns:
        The column number where today's date was written (for mark_present to use), or None if failed.
    """
    from datetime import datetime
    
    client, sheet = _get_client()
    if sheet is None:
        print("ERROR: Could not connect to Google Sheet for archiving")
        return None
    
    try:
        # Get all data to check if headers exist
        all_values = sheet.get_all_values()
        
        # Check if headers exist in Row 1, if not, set them up
        if len(all_values) == 0 or len(all_values[0]) == 0 or all_values[0][0].strip().upper() != "STUDENT":
            # Set up headers in Row 1
            sheet.update_cell(1, 1, "Student")  # Column A
            sheet.update_cell(1, 2, "Status")   # Column B
            sheet.update_cell(1, 3, "DATE")     # Column C
            print("Set up spreadsheet headers: Column A = Student, Column B = Status, Column C = DATE")
            # Reload data after setting headers
            all_values = sheet.get_all_values()
        
        # Check if today's date already exists
        today = datetime.now().strftime("%Y-%m-%d")
        today_exists = False
        for row_idx, row in enumerate(all_values, 1):
            if len(row) > 2 and row[2].strip() == today:  # Check Column C
                today_exists = True
                print(f"Today's date ({today}) already exists in Column C at row {row_idx}, skipping archiving")
                break
        
        if today_exists:
            return 3  # Return column C (date already exists)
        
        # Use provided trained names, or fallback to Column A if not provided
        if trained_names is None:
            student_names = get_all_students()
            print("WARNING: No trained names provided, using Column A names (legacy behavior)")
        else:
            student_names = trained_names
        
        if not student_names:
            print("WARNING: No student names found to archive")
            return None
        
        # Find the last row with data in Column A (skip header row)
        last_row_with_data = 1  # Start from row 1 (header row)
        for row_idx, row in enumerate(all_values, 1):
            if len(row) > 0 and row[0].strip():  # Check if Column A has data
                last_row_with_data = row_idx
        
        # Archive starts 2 rows below the last row with data in Column A
        archive_start_row = last_row_with_data + 2
        
        # Write the date in Column C (DATE) at the archive start row
        sheet.update_cell(archive_start_row, 3, today)
        print(f"Archived date: {today} at row {archive_start_row}, column C (DATE)")
        
        # Write student names starting at archive_start_row (same row as date), all in Column A
        for idx, name in enumerate(student_names):
            row_num = archive_start_row + idx
            # Write name in Column A (Student)
            sheet.update_cell(row_num, 1, name)
        
        print(f"Archived {len(student_names)} student names in Column A (Student) starting at row {archive_start_row}")
        print(f"Today's date is in Column C (DATE) at row {archive_start_row}")
        return 3  # Return column C (where date is written)
        
    except Exception as e:
        import traceback
        print(f"ERROR archiving students: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None

def test_connection():
    """Test the Google Sheets connection and print debug info."""
    print("=" * 50)
    print("Testing Google Sheets Connection...")
    print(f"Credentials path: {CREDENTIALS_PATH}")
    print(f"Credentials file exists: {os.path.exists(CREDENTIALS_PATH)}")
    print(f"Spreadsheet ID: {SPREADSHEET_ID}")
    print("=" * 50)
    
    client, sheet = _get_client()
    if sheet is None:
        print("FAILED: Could not connect to Google Sheet")
        return False
    
    try:
        # Get first few rows to verify connection
        all_values = sheet.get_all_values()
        print(f"Connected successfully!")
        print(f"Found {len(all_values)} rows in the sheet")
        print(f"\nFirst 5 rows:")
        for i, row in enumerate(all_values[:5], 1):
            print(f"  Row {i}: {row}")
        
        # Get all student names
        names = get_all_students()
        print(f"\nFound {len(names)} student names:")
        for name in names:
            print(f"  - '{name}'")
        
        return True
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Test the connection
    test_connection()
    print("\n" + "=" * 50)
    print("Testing mark_present with 'Sreyas'...")
    mark_present("Sreyas")



