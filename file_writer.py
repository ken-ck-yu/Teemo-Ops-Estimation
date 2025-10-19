"""
Google Cloud Storage file writing utility
"""

import json
from urllib.parse import urlparse
from google.cloud import storage as gcs_storage


def write_file_content(path, content):
    parsed = urlparse(path)
    
    # Convert dict/list to JSON string if needed
    if isinstance(content, (dict, list)):
        content_str = json.dumps(content, indent=4, ensure_ascii=False)
        content_type = 'application/json'
    else:
        content_str = str(content)
        content_type = 'text/plain'
    
    client = gcs_storage.Client()
    bucket = client.bucket(parsed.netloc)
    blob = bucket.blob(parsed.path.lstrip('/'))
    blob.content_type = content_type
    
    print(f"Writing to GCS: {parsed.netloc}/{parsed.path.lstrip('/')}")
    try:
        blob.upload_from_string(content_str)
    except Exception as e:
        raise Exception(f"Failed to write to GCS: {e}")

