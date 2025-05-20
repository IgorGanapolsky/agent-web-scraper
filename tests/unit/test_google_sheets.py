"""Unit tests for Google Sheets integration."""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
import json
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

from app.core.google_sheets.sheets import GoogleSheetsExporter, GoogleSheetsError


class TestGoogleSheetsExporter:
    """Tests for GoogleSheetsExporter class."""
    
    @pytest.fixture
    def mock_google_sheets_exporter(self):
        """Create a mocked GoogleSheetsExporter instance."""
        with patch('app.core.google_sheets.sheets.GoogleSheetsExporter.__init__', return_value=None) as mock_init:
            # Create a mock for the update response
            mock_update_response = {'updatedCells': 10}
            
            # Create a mock for the create response
            mock_create_response = {
                'spreadsheetId': 'test_spreadsheet_id',
                'spreadsheetUrl': 'https://example.com',
                'sheets': [{'properties': {'title': 'Jobs', 'sheetId': 123}}]
            }
            
            # Create a mock for the update request
            mock_update = MagicMock()
            mock_update.execute.return_value = mock_update_response
            
            # Create a mock for the values request
            mock_values = MagicMock()
            mock_values.update.return_value = mock_update
            
            # Create a mock for the create request
            mock_create = MagicMock()
            mock_create.execute.return_value = mock_create_response
            
            # Create a mock for the spreadsheets request
            mock_spreadsheets = MagicMock()
            mock_spreadsheets.create.return_value = mock_create
            mock_spreadsheets.values.return_value = mock_values
            
            # Create a mock for the service
            mock_service = MagicMock()
            mock_service.spreadsheets.return_value = mock_spreadsheets
            
            # Create a mock for the build function
            mock_build = MagicMock(return_value=mock_service)
            
            # Create a mock for the credentials
            mock_credentials = MagicMock()
            mock_credentials.universe_domain = 'googleapis.com'
            
            # Create the exporter and set the service and credentials manually
            exporter = GoogleSheetsExporter.__new__(GoogleSheetsExporter)
            exporter.service = mock_service
            exporter.credentials = mock_credentials
            
            # Patch the build function in the module
            with patch('app.core.google_sheets.sheets.build', mock_build):
                # Return the exporter and the mocks for assertions
                yield {
                    'exporter': exporter,
                    'mock_service': mock_service,
                    'mock_spreadsheets': mock_spreadsheets,
                    'mock_create': mock_create,
                    'mock_values': mock_values,
                    'mock_update': mock_update,
                    'mock_build': mock_build,
                    'mock_credentials': mock_credentials
                }

    @pytest.mark.asyncio
    async def test_export_to_sheets_new_spreadsheet(self, mock_google_sheets_exporter):
        """Test exporting jobs to a new Google Spreadsheet."""
        # Get the exporter and mocks from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        mock_service = mock_google_sheets_exporter['mock_service']
        mock_spreadsheets = mock_google_sheets_exporter['mock_spreadsheets']
        mock_create = mock_google_sheets_exporter['mock_create']
        mock_values = mock_google_sheets_exporter['mock_values']
        mock_update = mock_google_sheets_exporter['mock_update']
        
        # Test data
        jobs = [
            {
                'title': 'Software Engineer',
                'company': 'Test Company',
                'location': 'Remote',
                'salary': '$100,000',
                'posted_date': '2025-01-01',
                'job_url': 'https://example.com/job/1',
                'description': 'Test job description',
            },
            {
                'title': 'Data Scientist',
                'company': 'Another Company',
                'location': 'New York, NY',
                'salary': '$120,000',
                'posted_date': '2025-01-02',
                'job_url': 'https://example.com/job/2',
                'description': 'Another test job',
            }
        ]

        # Call the method
        result = await exporter.export_to_sheets(
            jobs=jobs,
            spreadsheet_name='Test Spreadsheet',
            worksheet_name='Jobs',
            create_new=True
        )

        # Verify the result contains the expected values
        assert result['spreadsheet_id'] == 'test_spreadsheet_id'
        assert result['spreadsheet_url'] == 'https://example.com'
        assert result['updated_cells'] == 10
        
        # Verify the spreadsheet was created with the correct title
        mock_spreadsheets.create.assert_called_once()
        
        # Verify the data was updated with the correct values
        mock_values.update.assert_called_once()
        
        # Verify the correct spreadsheet name was used
        call_args = mock_spreadsheets.create.call_args[1]
        assert call_args['body']['properties']['title'] == 'Test Spreadsheet'
        
        # Verify the correct worksheet name was used
        assert call_args['body']['sheets'][0]['properties']['title'] == 'Jobs'

    @pytest.mark.asyncio
    async def test_export_to_sheets_existing_spreadsheet(self, mock_google_sheets_exporter):
        """Test exporting jobs to an existing Google Spreadsheet."""
        from googleapiclient.http import HttpMock, HttpMockSequence
        import json
        
        # Get the exporter from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        
        # Create a mock response for the Drive API files.list call
        drive_response = {
            'files': [{
                'id': 'existing_spreadsheet_id',
                'name': 'Existing Spreadsheet',
                'webViewLink': 'https://example.com/existing_spreadsheet'
            }]
        }
        
        # Create a mock response for the Sheets API values.update call
        sheets_response = {'updatedCells': 10}
        
        # Create a mock for the build function that will return our mock services
        def mock_build(service_name, version, credentials=None, **kwargs):
            if service_name == 'drive':
                # Create a mock drive service
                mock_drive = MagicMock()
                mock_files = MagicMock()
                mock_list = MagicMock()
                
                # Configure the list method to return our mock response
                mock_list.execute.return_value = drive_response
                mock_files.list.return_value = mock_list
                mock_drive.files.return_value = mock_files
                return mock_drive
            else:
                # For sheets service, use the one from the fixture
                return mock_google_sheets_exporter['mock_service']
        
        # Patch the build function
        with patch('app.core.google_sheets.sheets.build', side_effect=mock_build):
            # Mock the update response
            mock_update = MagicMock()
            mock_update.execute.return_value = sheets_response
            mock_values = MagicMock()
            mock_values.update.return_value = mock_update
            
            # Patch the values method to return our mock
            with patch.object(exporter.service.spreadsheets.return_value, 'values', return_value=mock_values):
                # Test data
                jobs = [
                    {
                        'title': 'Software Engineer',
                        'company': 'Test Company',
                        'location': 'Remote'
                    }
                ]
                
                # Call the method with an existing spreadsheet name
                result = await exporter.export_to_sheets(
                    jobs=jobs,
                    spreadsheet_name='Existing Spreadsheet',
                    worksheet_name='Jobs',
                    create_new=False
                )
                
                # Verify the result contains the expected values
                assert result['spreadsheet_id'] == 'existing_spreadsheet_id'
                assert result['spreadsheet_url'] == 'https://example.com/existing_spreadsheet'
                assert result['updated_cells'] == 10
                
                # Verify the update call was made with the correct parameters
                mock_values.update.assert_called_once()
                update_call = mock_values.update.call_args[1]
                assert update_call['spreadsheetId'] == 'existing_spreadsheet_id'
                assert update_call['range'] == 'Jobs!A1'

    @pytest.mark.asyncio
    async def test_export_to_sheets_with_error(self, mock_google_sheets_exporter):
        """Test error handling during export."""
        # Get the exporter from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        
        # Mock an HTTP error
        error_content = {
            'error': {
                'code': 403,
                'message': 'API rate limit exceeded',
                'status': 'PERMISSION_DENIED'
            }
        }
        
        # Configure the mock to raise an HTTP error
        mock_service = mock_google_sheets_exporter['mock_service']
        mock_service.spreadsheets.return_value.create.side_effect = HttpError(
            resp=MagicMock(status=403),
            content=json.dumps(error_content).encode()
        )

        with pytest.raises(GoogleSheetsError) as exc_info:
            await exporter.export_to_sheets(
                jobs=[{'title': 'Test Job'}],
                spreadsheet_name='Test Spreadsheet',
                worksheet_name='Jobs',
                create_new=True
            )

        assert 'API rate limit exceeded' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_append_to_sheet(self, mock_google_sheets_exporter):
        """Test appending rows to an existing sheet."""
        # Get the exporter from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        
        # Get the mock service from the fixture
        mock_service = mock_google_sheets_exporter['mock_service']
        
        # Create a mock for the values object
        mock_values = MagicMock()
        mock_service.spreadsheets.return_value.values.return_value = mock_values
        
        # Mock the append response
        mock_append = MagicMock()
        mock_append.execute.return_value = {'updates': {}}
        mock_values.append.return_value = mock_append
        
        # New job to append
        new_job = {
            'title': 'Job 2',
            'company': 'Company B',
            'location': 'New York, NY'
        }
        
        # Convert the job to a list of values
        job_values = list(new_job.values())
        
        # Call the method
        result = await exporter.append_to_sheet(
            spreadsheet_id='test_id',
            worksheet_name='Jobs',
            rows=[job_values]
        )
        
        # Verify append was called with the correct parameters
        mock_values.append.assert_called_once()
        append_call = mock_values.append.call_args[1]
        
        # Verify the call was made with the correct arguments
        assert append_call['spreadsheetId'] == 'test_id'
        assert append_call['range'] == 'Jobs!A1'
        assert append_call['valueInputOption'] == 'USER_ENTERED'
        assert append_call['insertDataOption'] == 'INSERT_ROWS'
        assert append_call['body'] == {'values': [job_values]}
        
        # Verify the result is as expected
        assert result == {'updates': {}}

    @pytest.mark.asyncio
    async def test_create_worksheet_if_not_exists_new(self, mock_google_sheets_exporter):
        """Test creating a new worksheet if it doesn't exist."""
        # Get the exporter from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        
        # Get the mock service from the fixture
        mock_service = mock_google_sheets_exporter['mock_service']
        
        # Create a mock for the batch update response
        mock_batch_update = MagicMock()
        mock_batch_update.execute.return_value = {
            'replies': [{
                'addSheet': {
                    'properties': {
                        'title': 'NewSheet',
                        'sheetId': 2
                    }
                }
            }]
        }
        mock_service.spreadsheets.return_value.batchUpdate.return_value = mock_batch_update
        
        # Mock response with existing sheets
        mock_get = MagicMock()
        mock_get.execute.return_value = {
            'sheets': [{'properties': {'title': 'Sheet1', 'sheetId': 1}}]
        }
        mock_service.spreadsheets.return_value.get.return_value = mock_get
        
        # Mock the values update response
        mock_values = MagicMock()
        mock_values.update.return_value.execute.return_value = {}
        mock_service.spreadsheets.return_value.values.return_value = mock_values
        
        # Call the method
        result = await exporter.create_worksheet_if_not_exists(
            spreadsheet_id='test_id',
            worksheet_name='NewSheet'
        )
        
        # Verify the batch update was called to add a new sheet
        mock_service.spreadsheets.return_value.batchUpdate.assert_called_once()
        
        # Verify the batch update was called with the correct parameters
        batch_update_call = mock_service.spreadsheets.return_value.batchUpdate.call_args[1]
        assert batch_update_call['spreadsheetId'] == 'test_id'
        assert batch_update_call['body'] == {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': 'NewSheet'
                    }
                }
            }]
        }
        
        # Verify values were updated with headers
        mock_values.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_clear_worksheet(self, mock_google_sheets_exporter):
        """Test clearing a worksheet."""
        # Get the exporter from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        
        # Get the mock service from the fixture
        mock_service = mock_google_sheets_exporter['mock_service']
        
        # Create a mock for the clear response
        mock_clear = MagicMock()
        mock_clear.execute.return_value = {}
        mock_values = MagicMock()
        mock_values.clear.return_value = mock_clear
        mock_service.spreadsheets.return_value.values.return_value = mock_values
        
        # Call the method
        result = await exporter.clear_worksheet(
            spreadsheet_id='test_id',
            worksheet_name='Sheet1'
        )
        
        # Verify clear was called with the correct parameters
        mock_values.clear.assert_called_once_with(
            spreadsheetId='test_id',
            range='Sheet1!A:Z',
            body={}
        )
        
        # Verify the result is as expected
        assert result == {}
    
    @pytest.mark.asyncio
    async def test_update_cells(self, mock_google_sheets_exporter):
        """Test updating specific cells in a worksheet."""
        # Get the exporter from the fixture
        exporter = mock_google_sheets_exporter['exporter']
        
        # Get the mock service from the fixture
        mock_service = mock_google_sheets_exporter['mock_service']
        
        # Create a mock for the batch update response
        mock_batch_update = MagicMock()
        mock_batch_update.execute.return_value = {'responses': [{}], 'totalUpdatedCells': 4}
        mock_values = MagicMock()
        mock_values.batchUpdate.return_value = mock_batch_update
        mock_service.spreadsheets.return_value.values.return_value = mock_values
        
        # Test data
        updates = [
            {
                'range': 'A1:B2',
                'values': [
                    ['Header1', 'Header2'],
                    ['Value1', 'Value2']
                ]
            }
        ]
        
        # Call the method
        result = await exporter.update_cells(
            spreadsheet_id='test_id',
            worksheet_name='Sheet1',
            updates=updates
        )
        
        # Verify batchUpdate was called with the correct parameters
        mock_values.batchUpdate.assert_called_once()
        
        batch_update_call = mock_values.batchUpdate.call_args[1]
        assert batch_update_call['spreadsheetId'] == 'test_id'
        assert batch_update_call['body'] == {
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': 'Sheet1!A1:B2',
                    'values': [
                        ['Header1', 'Header2'],
                        ['Value1', 'Value2']
                    ]
                }
            ]
        }
        
        # Verify the result is as expected
        assert result == {'responses': [{}], 'totalUpdatedCells': 4}
