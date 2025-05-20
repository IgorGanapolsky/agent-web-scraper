"""Google Sheets integration for exporting job listings."""
import os
from typing import List, Dict, Any, Optional, Union

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetsError(Exception):
    """Exception raised for Google Sheets API errors."""
    pass


class GoogleSheetsExporter:
    """Exports data to Google Sheets."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, credentials_json: dict):
        """Initialize with Google API credentials.
        
        Args:
            credentials_json: Dictionary containing Google API credentials.
        """
        self.credentials = service_account.Credentials.from_service_account_info(
            credentials_json, scopes=self.SCOPES
        )
        self.service = build('sheets', 'v4', credentials=self.credentials)
    
    async def export_to_sheets(
        self,
        jobs: List[Dict[str, Any]],
        spreadsheet_name: str,
        worksheet_name: str,
        create_new: bool = False
    ) -> Dict[str, str]:
        """Export jobs to a Google Sheet.
        
        Args:
            jobs: List of job dictionaries to export.
            spreadsheet_name: Name of the spreadsheet.
            worksheet_name: Name of the worksheet.
            create_new: Whether to create a new spreadsheet.
            
        Returns:
            Dictionary containing spreadsheet_id and spreadsheet_url.
            
        Raises:
            GoogleSheetsError: If there's an error exporting to Google Sheets.
        """
        try:
            if not jobs:
                raise ValueError("No jobs provided for export")
                
            if create_new:
                # Create a new spreadsheet
                spreadsheet = {
                    'properties': {'title': spreadsheet_name},
                    'sheets': [{'properties': {'title': worksheet_name}}]
                }
                
                spreadsheet = self.service.spreadsheets().create(
                    body=spreadsheet,
                    fields='spreadsheetId,spreadsheetUrl,sheets(properties(sheetId,title))'
                ).execute()
                
                spreadsheet_id = spreadsheet['spreadsheetId']
                spreadsheet_url = spreadsheet['spreadsheetUrl']
            else:
                # Find existing spreadsheet by name
                # Note: This requires the Drive API to be enabled
                drive_service = build('drive', 'v3', credentials=self.credentials)
                results = drive_service.files().list(
                    q=f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet'",
                    spaces='drive',
                    fields='files(id, name, webViewLink)'
                ).execute()
                
                files = results.get('files', [])
                if not files:
                    raise GoogleSheetsError(f"Spreadsheet '{spreadsheet_name}' not found")
                
                spreadsheet_id = files[0]['id']
                spreadsheet_url = files[0].get('webViewLink', '')
            
            # Prepare data for update
            headers = list(jobs[0].keys())
            values = [headers] + [[str(job.get(header, '')) for header in headers] for job in jobs]
            
            # Update the sheet with the new data
            body = {
                'values': values
            }
            
            range_name = f"{worksheet_name}!A1"
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'updated_cells': result.get('updatedCells', 0)
            }
            
        except HttpError as e:
            error_details = e.content.decode() if hasattr(e, 'content') else str(e)
            raise GoogleSheetsError(f"Google Sheets API error: {error_details}") from e
        except Exception as e:
            raise GoogleSheetsError(f"Error exporting to Google Sheets: {str(e)}") from e
    
    async def append_to_sheet(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        rows: List[List[Any]]
    ) -> Dict:
        """Append rows to a worksheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet.
            worksheet_name: Name of the worksheet.
            rows: Rows to append.
            
        Returns:
            Result of the append operation.
        """
        range_name = f"{worksheet_name}!A1"
        
        body = {
            'values': rows
        }
        
        result = self.service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        return result
    
    async def create_worksheet_if_not_exists(
        self,
        spreadsheet_id: str,
        worksheet_name: str
    ) -> Dict:
        """Create a new worksheet if it doesn't exist.
        
        Args:
            spreadsheet_id: ID of the spreadsheet.
            worksheet_name: Name of the worksheet to create.
            
        Returns:
            Information about the created or existing worksheet.
        """
        try:
            # Try to get the worksheet
            result = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id,
                fields='sheets(properties(sheetId,title))'
            ).execute()
            
            # Check if worksheet exists
            for sheet in result.get('sheets', []):
                if sheet['properties']['title'] == worksheet_name:
                    return sheet['properties']
            
            # Worksheet doesn't exist, create it
            body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': worksheet_name
                        }
                    }
                }]
            }
            
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return result['replies'][0]['addSheet']['properties']
            
        except HttpError as e:
            error_details = e.content.decode() if hasattr(e, 'content') else str(e)
            raise GoogleSheetsError(f"Error creating worksheet: {error_details}") from e
    
    async def clear_worksheet(
        self,
        spreadsheet_id: str,
        worksheet_name: str
    ) -> Dict:
        """Clear all content from a worksheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet.
            worksheet_name: Name of the worksheet to clear.
            
        Returns:
            Result of the clear operation.
        """
        range_name = f"{worksheet_name}!A:Z"
        
        result = self.service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            body={}
        ).execute()
        
        return result
    
    async def update_cells(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        updates: List[Dict]
    ) -> Dict:
        """Update specific cells in a worksheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet.
            worksheet_name: Name of the worksheet.
            updates: List of update dictionaries, each containing:
                - range: Range in A1 notation (e.g., 'A1:B2')
                - values: 2D array of values to write
                
        Returns:
            Result of the batch update.
        """
        data = []
        
        for update in updates:
            range_name = f"{worksheet_name}!{update['range']}"
            data.append({
                'range': range_name,
                'values': update['values']
            })
        
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }
        
        result = self.service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        return result
