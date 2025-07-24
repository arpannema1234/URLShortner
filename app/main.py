from flask import Flask, jsonify, request, redirect, url_for
from .models import url_store
from .utils import generate_short_code, is_valid_url, normalize_url

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })


@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """Shorten a URL and return the short code."""
    try:
        # Get JSON data from request
        try:
            data = request.get_json(force=True)
        except Exception:
            return jsonify({'error': 'Invalid JSON or Content-Type must be application/json'}), 400
            
        if data is None:
            return jsonify({'error': 'Invalid JSON or Content-Type must be application/json'}), 400
        if 'url' not in data:
            return jsonify({'error': 'URL is required in request body'}), 400
        
        original_url = data['url'].strip()
        if not original_url:
            return jsonify({'error': 'URL cannot be empty'}), 400
        
        # Normalize and validate URL
        normalized_url = normalize_url(original_url)
        if not is_valid_url(normalized_url):
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Generate unique short code
        max_attempts = 100
        for _ in range(max_attempts):
            short_code = generate_short_code()
            if not url_store.code_exists(short_code):
                break
        else:
            return jsonify({'error': 'Failed to generate unique short code'}), 500
        
        # Store the mapping
        try:
            url_store.add_mapping(short_code, normalized_url)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # Return response
        short_url = request.host_url.rstrip('/') + '/' + short_code
        return jsonify({
            'short_code': short_code,
            'short_url': short_url
        }), 201
    
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirect to the original URL using the short code."""
    try:
        # Get the mapping
        mapping = url_store.get_mapping(short_code)
        if not mapping:
            return jsonify({'error': 'Short code not found'}), 404
        
        # Increment click count
        url_store.increment_clicks(short_code)
        
        # Redirect to original URL
        return redirect(mapping.original_url, code=302)
    
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/stats/<short_code>')
def get_stats(short_code):
    """Get analytics for a short code."""
    try:
        # Get the mapping
        mapping = url_store.get_mapping(short_code)
        if not mapping:
            return jsonify({'error': 'Short code not found'}), 404
        
        # Return stats
        return jsonify(mapping.to_dict()), 200
    
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({'error': 'Method not allowed'}), 405


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)