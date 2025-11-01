"""
Flask API for ML Training Resource Estimation using Gemini
Designed to run on Google Cloud Run
"""

import os
from flask import Flask, request, jsonify
from urllib.parse import urlparse
from file_reader import read_file_content
from file_writer import write_file_content
from gemini_estimation import run_estimation
from google_cloud_utility import get_secret

TEEMO_VERSION = "1.0.1"

# Configuration - Use absolute paths for Cloud Run reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEMINI_MODEL = 'gemini-2.0-flash-exp'
SYSTEM_PROMPT = os.path.join(BASE_DIR, 'prompts', 'system_prompt.txt')
USER_PROMPT_TEMPLATE = os.path.join(BASE_DIR, 'prompts', 'user_prompt_template.txt')

app = Flask(__name__)

# Get API key from Google Cloud Secret Manager
try:
    GEMINI_API_KEY = get_secret(
        secret_id="gemini_api_key",
        project_id="587897013083"
    )
    print("✓ Successfully loaded Gemini API key from Secret Manager")
except Exception as e:
    print(f"✗ Warning: Failed to load API key from Secret Manager: {e}")
    GEMINI_API_KEY = None

# Verify prompt files exist at startup
print(f"Teemo version: {TEEMO_VERSION}")
print(f"Checking prompt files...")
print(f"  System prompt: {SYSTEM_PROMPT}")
print(f"  Exists: {os.path.exists(SYSTEM_PROMPT)}")
print(f"  User prompt template: {USER_PROMPT_TEMPLATE}")
print(f"  Exists: {os.path.exists(USER_PROMPT_TEMPLATE)}")


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
        "output_path": "gs://bucket/path/output.json",
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
        
        print(f"Received request: {data}")
        
        # Get parameters path (required)
        params_path = data.get('params_path')
        if not params_path:
            return jsonify({
                'status': 'error',
                'message': 'params_path is required'
            }), 400
        
        print(f"Parameters path: {params_path}")
        
        # Read parameters content from GCS
        params_content = read_file_content(params_path)
        print(f"✓ Read {len(params_content)} characters from params file")
        
        # Get output path (required)
        output_path = data.get('output_path')
        if not output_path:
            return jsonify({
                'status': 'error',
                'message': 'output_path is required'
            }), 400
        
        # Validate output path format
        print(f"Validating output path: {output_path}")
        
        if not output_path.startswith('gs://'):
            return jsonify({
                'status': 'error',
                'message': f'output_path must start with gs://, got: {output_path}'
            }), 400
        
        # Parse and validate
        parsed = urlparse(output_path)
        bucket_name = parsed.netloc
        blob_path = parsed.path.lstrip('/')
        
        if not bucket_name:
            return jsonify({
                'status': 'error',
                'message': f'Invalid output_path - missing bucket name. Format: gs://bucket/path/file.json'
            }), 400
        
        if not blob_path:
            return jsonify({
                'status': 'error',
                'message': f'Invalid output_path - missing file name. Got: {output_path}. Expected: gs://{bucket_name}/path/file.json'
            }), 400
        
        print(f"✓ Output path validated:")
        print(f"  Bucket: {bucket_name}")
        print(f"  Object: {blob_path}")
        print(f"  Full path: {output_path}")
        
        # Check API key from Secret Manager
        if not GEMINI_API_KEY:
            return jsonify({
                'status': 'error',
                'message': 'GEMINI_API_KEY not configured in Secret Manager'
            }), 500
        
        # Get debug flag
        debug = data.get('debug', False)
        print(f"Debug mode: {debug}")
        
        # Run estimation
        print("Starting estimation...")
        success = run_estimation(
            provider='gemini',
            params_content=params_content,
            output_path=output_path,
            debug=debug,
            api_key=GEMINI_API_KEY,
            model=GEMINI_MODEL,
            system_prompt_path=SYSTEM_PROMPT,
            user_prompt_template_path=USER_PROMPT_TEMPLATE
        )
        
        if success:
            print(f"✅ Estimation completed successfully!")
            return jsonify({
                'status': 'success',
                'message': 'Estimation completed successfully',
                'output_path': output_path
            }), 200
        else:
            print(f"❌ Estimation failed")
            return jsonify({
                'status': 'error',
                'message': 'Estimation failed - check logs for details'
            }), 500
            
    except Exception as e:
        print(f"Error in estimate endpoint: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        'service': 'ML Training Resource Estimation API',
        'version': TEEMO_VERSION,
        'endpoints': {
            '/health': 'GET - Health check',
            '/estimate': 'POST - Run estimation',
            '/': 'GET - API documentation'
        },
        'usage': {
            'method': 'POST',
            'url': '/estimate',
            'body': {
                'params_path': 'gs://bucket/path/to/script.txt',
                'output_path': 'gs://bucket/path/to/output.json',
                'debug': 'true or false (optional)'
            },
            'example': {
                'params_path': 'gs://teemo-ops-extract-output/sample-input-script.txt',
                'output_path': 'gs://teemo-ops-estimate-output/results/output.json',
                'debug': False
            }
        }
    }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)