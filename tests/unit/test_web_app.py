"""Unit tests for the web application."""
import pytest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock the GoogleSearch class
class MockGoogleSearch:
    def __init__(self, *args, **kwargs):
        self.json = lambda: {}

# Mock the necessary modules before importing the app
with patch('streamlit.set_page_config'), \
     patch('streamlit.sidebar'), \
     patch('streamlit.title'), \
     patch('streamlit.markdown'), \
     patch('streamlit.progress'), \
     patch('streamlit.empty'), \
     patch('streamlit.spinner'), \
     patch('streamlit.error'), \
     patch('streamlit.warning'), \
     patch('streamlit.info'), \
     patch('streamlit.expander'), \
     patch('streamlit.text_input'), \
     patch('streamlit.slider'), \
     patch('streamlit.checkbox'), \
     patch('streamlit.button'), \
     patch('streamlit.download_button'), \
     patch('pandas.DataFrame'), \
     patch('serpapi.google_search.GoogleSearch', new=MockGoogleSearch), \
     patch('builtins.open', mock_open(read_data='mocked')), \
     patch('logging.basicConfig'):
    
    from app.web.app import (
        is_blocked_url,
        extract_headers_with_soup,
        extract_headers_with_undetected_chrome,
        search_and_scrape,
        initialize_session_state,
        handle_enter_key
    )

# Test data
TEST_URL = "https://example.com"
TEST_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="Test meta description">
</head>
<body>
    <h1>Test H1</h1>
    <h2>Test H2</h2>
    <h3>Test H3</h3>
</body>
</html>
"""

class TestWebApp:
    """Test suite for the web application."""
    
    def test_is_blocked_url_positive(self):
        """Test that blocked URLs are correctly identified."""
        blocked_url = "https://www.linkedin.com/jobs"
        assert is_blocked_url(blocked_url) is True
    
    def test_is_blocked_url_negative(self):
        """Test that non-blocked URLs are correctly identified."""
        assert is_blocked_url(TEST_URL) is False
    
    @patch('requests.get')
    def test_extract_headers_with_soup_success(self, mock_get):
        """Test successful header extraction with BeautifulSoup."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = TEST_HTML
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the function
        result = extract_headers_with_soup(
            TEST_URL, 
            ['Title', 'H1', 'H2', 'H3', 'Meta Description']
        )
        
        # Assert the results
        assert result['Title'] == 'Test Page'
        assert result['H1'] == 'Test H1'
        assert result['H2'] == 'Test H2'
        assert result['H3'] == 'Test H3'
        assert 'Test meta description' in result['Meta Description']
    
    @patch('app.web.app.extract_headers_with_undetected_chrome')
    def test_extract_headers_with_soup_fallback(self, mock_undetected):
        """Test fallback to undetected scraper when BeautifulSoup fails."""
        # Mock the undetected scraper
        mock_undetected.return_value = {
            'Title': 'Test Page',
            'H1': 'Test H1',
            'H2': 'Test H2',
            'H3': 'Test H3',
            'Meta Description': 'Test meta description'
        }
        
        # Mock requests to raise an exception
        with patch('requests.get', side_effect=Exception("Test error")):
            result = extract_headers_with_soup(
                TEST_URL,
                ['Title', 'H1', 'H2', 'H3', 'Meta Description'],
                retry_count=0  # Don't retry for test
            )
            
            # Verify the undetected scraper was called
            mock_undetected.assert_called_once()
            assert result['Title'] == 'Test Page'
    
    @patch('app.web.app.UndetectedScraper')
    def test_extract_headers_with_undetected_chrome_success(self, mock_scraper):
        """Test successful header extraction with undetected Chrome."""
        # Mock the scraper
        mock_instance = MagicMock()
        mock_instance.scrape.return_value = TEST_HTML
        mock_scraper.return_value = mock_instance
        
        # Call the function
        result = extract_headers_with_undetected_chrome(
            TEST_URL,
            ['Title', 'H1', 'H2', 'H3', 'Meta Description']
        )
        
        # Assert the results
        assert result['Title'] == 'Test Page'
        assert result['H1'] == 'Test H1'
        assert result['H2'] == 'Test H2'
        assert result['H3'] == 'Test H3'
        assert 'Test meta description' in result['Meta Description']
    
    @patch('app.web.app.st')
    def test_initialize_session_state(self, mock_st):
        """Test session state initialization."""
        # Mock session state
        mock_session_state = {}
        mock_st.session_state = mock_session_state
        
        # Call the function
        initialize_session_state()
        
        # Assert the session state was initialized correctly
        assert 'search_term' in mock_session_state
        assert 'num_results' in mock_session_state
        assert 'selected_headers' in mock_session_state
        assert 'additional_headers' in mock_session_state
        assert 'results_df' in mock_session_state
    
    @patch('app.web.app.st')
    def test_handle_enter_key_with_search_term(self, mock_st):
        """Test handling of Enter key with search term."""
        # Mock session state and input
        mock_session_state = {'search_term_input': 'test search'}
        mock_st.session_state = mock_session_state
        
        # Call the function
        handle_enter_key()
        
        # Assert the search term was set
        assert mock_session_state['search_term'] == 'test search'
        assert 'results_df' not in mock_session_state  # Should be deleted
    
    @patch('app.web.app.st')
    @patch('app.web.app.GoogleSearch')
    def test_search_and_scrape_success(self, mock_google_search, mock_st):
        """Test successful search and scrape flow."""
        # Mock the session state
        mock_session_state = {
            'search_term': 'test search',
            'num_results': 5,
            'selected_headers': ['Title', 'H1', 'H2'],
            'additional_headers': ''
        }
        mock_st.session_state = mock_session_state
        
        # Mock the Google search results
        mock_results = {
            'organic_results': [
                {
                    'link': 'https://example.com',
                    'title': 'Example',
                    'snippet': 'Example snippet'
                }
            ]
        }
        mock_google_search.return_value.get_dict.return_value = mock_results
        
        # Mock the progress bar and status text
        mock_progress = MagicMock()
        mock_status = MagicMock()
        mock_st.progress.return_value = mock_progress
        mock_st.empty.return_value = mock_status
        
        # Mock the results placeholder
        mock_placeholder = MagicMock()
        mock_st.empty.return_value = mock_placeholder
        
        # Mock the extract_headers function
        with patch('app.web.app.extract_headers_with_soup') as mock_extract:
            mock_extract.return_value = {
                'Title': 'Example',
                'H1': 'Example H1',
                'H2': 'Example H2'
            }
            
            # Call the function
            search_and_scrape()
            
            # Verify the results
            assert 'results_df' in mock_session_state
            assert not mock_session_state['results_df'].empty
            assert mock_session_state['results_df'].iloc[0]['Title'] == 'Example'
            assert mock_session_state['results_df'].iloc[0]['H1'] == 'Example H1'
            assert mock_session_state['results_df'].iloc[0]['H2'] == 'Example H2'
