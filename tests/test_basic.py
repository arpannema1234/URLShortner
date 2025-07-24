import pytest
import json
from app.main import app
from app.models import url_store

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear the URL store before each test
        url_store._mappings.clear()
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'URL Shortener API'


def test_api_health_check(client):
    """Test the API health check endpoint."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['message'] == 'URL Shortener API is running'


def test_shorten_url_success(client):
    """Test successful URL shortening."""
    response = client.post('/api/shorten',
                          data=json.dumps({'url': 'https://www.example.com'}),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data
    assert len(data['short_code']) == 6
    assert data['short_url'].endswith(data['short_code'])


def test_shorten_url_without_scheme(client):
    """Test URL shortening for URLs without scheme."""
    response = client.post('/api/shorten',
                          data=json.dumps({'url': 'www.example.com'}),
                          content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data


def test_shorten_url_missing_url(client):
    """Test shortening with missing URL in request body."""
    response = client.post('/api/shorten',
                          data=json.dumps({}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'URL is required' in data['error']


def test_shorten_url_empty_url(client):
    """Test shortening with empty URL."""
    response = client.post('/api/shorten',
                          data=json.dumps({'url': ''}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'cannot be empty' in data['error']


def test_shorten_url_invalid_url(client):
    """Test shortening with invalid URL format."""
    response = client.post('/api/shorten',
                          data=json.dumps({'url': 'not-a-valid-url'}),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Invalid URL format' in data['error']


def test_redirect_success(client):
    """Test successful redirection to original URL."""
    # First create a short URL
    shorten_response = client.post('/api/shorten',
                                  data=json.dumps({'url': 'https://www.example.com'}),
                                  content_type='application/json')
    
    assert shorten_response.status_code == 201
    short_code = shorten_response.get_json()['short_code']
    
    # Test redirection
    response = client.get(f'/{short_code}')
    assert response.status_code == 302
    assert response.location == 'https://www.example.com'


def test_redirect_not_found(client):
    """Test redirection with non-existent short code."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'not found' in data['error']


def test_stats_success(client):
    """Test getting analytics for a short code."""
    # First create a short URL
    shorten_response = client.post('/api/shorten',
                                  data=json.dumps({'url': 'https://www.example.com'}),
                                  content_type='application/json')
    
    assert shorten_response.status_code == 201
    short_code = shorten_response.get_json()['short_code']
    
    # Get initial stats
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    
    data = stats_response.get_json()
    assert data['short_code'] == short_code
    assert data['url'] == 'https://www.example.com'
    assert data['clicks'] == 0
    assert 'created_at' in data
    
    # Click the short URL to increment counter
    client.get(f'/{short_code}')
    
    # Check updated stats
    stats_response = client.get(f'/api/stats/{short_code}')
    assert stats_response.status_code == 200
    data = stats_response.get_json()
    assert data['clicks'] == 1


def test_stats_not_found(client):
    """Test getting analytics for non-existent short code."""
    response = client.get('/api/stats/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data
    assert 'not found' in data['error']


def test_click_counting(client):
    """Test that click counting works correctly with multiple visits."""
    # Create a short URL
    shorten_response = client.post('/api/shorten',
                                  data=json.dumps({'url': 'https://www.example.com'}),
                                  content_type='application/json')
    
    short_code = shorten_response.get_json()['short_code']
    
    # Click multiple times
    for i in range(5):
        response = client.get(f'/{short_code}')
        assert response.status_code == 302
    
    # Check final count
    stats_response = client.get(f'/api/stats/{short_code}')
    data = stats_response.get_json()
    assert data['clicks'] == 5


def test_multiple_urls_different_codes(client):
    """Test that different URLs get different short codes."""
    urls = [
        'https://www.example.com',
        'https://www.google.com',
        'https://www.github.com'
    ]
    
    short_codes = []
    for url in urls:
        response = client.post('/api/shorten',
                              data=json.dumps({'url': url}),
                              content_type='application/json')
        assert response.status_code == 201
        short_codes.append(response.get_json()['short_code'])
    
    # All short codes should be unique
    assert len(set(short_codes)) == len(short_codes)
    
    # Each should redirect to correct URL
    for i, short_code in enumerate(short_codes):
        response = client.get(f'/{short_code}')
        assert response.status_code == 302
        assert response.location == urls[i]


def test_invalid_json_request(client):
    """Test handling of invalid JSON in request."""
    response = client.post('/api/shorten',
                          data='invalid json',
                          content_type='application/json')
    
    assert response.status_code == 400


def test_method_not_allowed(client):
    """Test method not allowed error handling."""
    response = client.get('/api/shorten')
    assert response.status_code == 405
    data = response.get_json()
    assert 'error' in data