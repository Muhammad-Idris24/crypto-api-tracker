import pytest
from unittest.mock import patch, mock_open
from services.api_service import APIService
import json
import time
import os

@pytest.fixture
def api_service():
    os.environ["COIN_GECKO_API_URL"] = "https://api.coingecko.com/api/v3"
    return APIService()

def test_cache_handling(api_service, tmp_path):
    api_service.CACHE_DIR = tmp_path
    endpoint = "test_endpoint"
    test_data = {"key": "value"}
    
    # Test saving and loading from cache
    cache_file = api_service._get_cache_path(endpoint)
    api_service._save_to_cache(cache_file, test_data)
    loaded_data = api_service._load_from_cache(cache_file)
    assert loaded_data == test_data
    
    # Test cache validity
    assert api_service._is_cache_valid(cache_file) is True
    
    # Modify cache file time to be expired
    old_time = time.time() - api_service.CACHE_EXPIRY - 1
    os.utime(cache_file, (old_time, old_time))
    assert api_service._is_cache_valid(cache_file) is False

@patch('services.api_service.requests.Session.get')
def test_api_request_success(mock_get, api_service):
    # Mock successful API response
    mock_response = mock_get.return_value
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"data": "test"}
    
    result = api_service.get("test_endpoint")
    assert result == {"data": "test"}

@patch('services.api_service.requests.Session.get')
def test_api_request_failure_with_cache(mock_get, api_service, tmp_path):
    api_service.CACHE_DIR = tmp_path
    endpoint = "test_endpoint"
    test_data = {"cached": "data"}
    
    # Create cache file first
    cache_file = api_service._get_cache_path(endpoint)
    api_service._save_to_cache(cache_file, test_data)
    
    # Mock failed API request
    mock_get.side_effect = Exception("API Error")
    
    # Should fall back to cache
    result = api_service.get(endpoint)
    assert result == test_data