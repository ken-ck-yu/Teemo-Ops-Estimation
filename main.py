"""
Flask API for ML Training Resource Estimation using Gemini
Designed to run on Google Cloud Run
"""

import os
from flask import Flask, request, jsonify
from file_reader import read_file_content
from file_writer import write_file_content
from gemini_estimation import run_estimation
from google_cloud_utility import get_secret

TEEMO_VERSION = "1.0.0"
# Configuration
GEMINI_MODEL = 'gemini-2.0-flash-exp'
SYSTEM_PROMPT = 'prompts/system_prompt.txt'
USER_PROMPT_TEMPLATE = 'prompts/user_prompt_template.txt'

app = Flask(__name__)

# Get API key from Google Cloud Secret Manager
try:
    GEMINI_API_KEY = get_secret(
        secret_id="gemini_api_key",
        project_id="587897013083"
    )
except Exception as e:
    print(f"Warning: Failed to load API key from Secret Manager: {e}")
    GEMINI_API_KEY = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'service': 'ml-training-estimation',
        'version': TEEMO_VERSION
    }), 200


@app.route('/estimate', methods=['POST'])
def estimate():
    """
    Main estimation endpoint
    
    Request body:
    {
        "params_path": "gs://bucket/params.txt",
        "output_path": "gs://bucket/output.json",
        "debug": false
    }
    
    Returns:
    {
        "status": "success" | "error",
        "message": "...",
        "output_path": "..."
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data provided'
            }), 400
        
        # Get parameters path (required)
        params_path = data.get('params_path')
        if not params_path:
            return jsonify({
                'status': 'error',
                'message': 'params_path is required'
            }), 400
        
        # Read parameters content from GCS
        params_content = read_file_content(params_path)
        
        # Get output path (required)
        output_path = data.get('output_path')
        if not output_path:
            return jsonify({
                'status': 'error',
                'message': 'output_path is required'
            }), 400
        
        # Check API key from Secret Manager
        if not GEMINI_API_KEY:
            return jsonify({
                'status': 'error',
                'message': 'GEMINI_API_KEY not configured in Secret Manager'
            }), 500
        
        # Get debug flag
        debug = data.get('debug', False)
        
        # Run estimation
        success = run_estimation(
            provider='gemini',
            params_content=params_content,
            output_path=output_path,
            debug=debug,
            api_key=GEMINI_API_KEY,
            model=GEMINI_MODEL,
            system_prompt=SYSTEM_PROMPT,
            user_prompt_template=USER_PROMPT_TEMPLATE
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Estimation completed successfully',
                'output_path': output_path
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Estimation failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        'service': 'ML Training Resource Estimation API',
        'version': '1.0.0',
        'endpoints': {
            '/health': 'GET - Health check',
            '/estimate': 'POST - Run estimation',
            '/': 'GET - API documentation'
        },
        'usage': {
            'method': 'POST',
            'url': '/estimate',
            'body': {
                'params_path': 'Path to parameters file (gs://bucket/path)',
                'output_path': 'Output path (gs://bucket/path)',
                'debug': 'Optional debug flag'
            }
        }
    }), 200
