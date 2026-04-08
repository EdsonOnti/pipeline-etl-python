import os
import pandas as pd
import win32com.client as win32

class ExcelManager:
    """
    Class responsible for interacting with Excel files.
    Handles the COM interaction to simulate CTRL+ALT+F5 (Refresh All).
    """

    def __init__(self, file_path: str):
        # We ensure the absolute path since Excel COM requires absolute paths
        self._file_path = os.path.abspath(file_path)

    def refresh_excel_data(self):
        """
        Opens the Excel file in the background, triggers a 'Refresh All'
        to execute any data connections, and saves the file.
        """
        print(f"[*] Refreshing Excel file: {self._file_path}")
        excel_app = None
        workbook = None
        
        try:
            # 1. Open the Excel application via COM
            excel_app = win32.Dispatch("Excel.Application")
            excel_app.Visible = False  # Run in background
            excel_app.DisplayAlerts = False  # Prevent popups asking to save
            
            # 2. Open the workbook
            workbook = excel_app.Workbooks.Open(self._file_path)
            
            # 3. Trigger the refresh
            # To ensure the Python script waits for the query to finish,
            # we temporarily disable BackgroundQuery on the connections.
            for conn in workbook.Connections:
                try:
                    if conn.Type == 1:  # xlConnectionTypeOLEDB
                        conn.OLEDBConnection.BackgroundQuery = False
                    elif conn.Type == 2:  # xlConnectionTypeODBC
                        conn.ODBCConnection.BackgroundQuery = False
                except Exception as e:
                    pass # Ignore if a connection doesn't support the property
                    
            workbook.RefreshAll()
            
            # 4. Save the workbook
            workbook.Save()
            print("[+] Excel data refreshed and saved successfully.")
            
        except Exception as e:
            print(f"[-] Error refreshing Excel data: {e}")
            raise
            
        finally:
            # 5. Clean up COM resources to avoid zombie processes holding the file open
            if workbook:
                workbook.Close(SaveChanges=False)
            if excel_app:
                excel_app.Quit()

    def load_to_dataframe(self, sheet_name=0) -> pd.DataFrame:
        """
        Loads the Excel data into a pandas DataFrame.
        """
        print(f"[*] Loading data from Excel into DataFrame...")
        try:
            # Pandas can safely read the file now that it is refreshed and saved
            df = pd.read_excel(self._file_path, sheet_name=sheet_name)
            print(f"[+] Successfully loaded {len(df)} rows.")
            return df
        except Exception as e:
            print(f"[-] Error loading DataFrame: {e}")
            raise
