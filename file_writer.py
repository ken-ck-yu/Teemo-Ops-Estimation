"""
Flexible file writing utility - supports both local files and GCS
"""

import os
import json
from urllib.parse import urlparse
from google.cloud import storage as gcs_storage


def write_file_content(path, content):
    """
    Write content to either local filesystem or GCS.
    
    Args:
        path: Destination path. Must be GCS path: gs://bucket/path/file.json
        content: Content to write (dict, list, or string)
    
    Raises:
        ValueError: If path is invalid
        Exception: For write errors
    """
    # Convert dict/list to JSON string if needed
    if isinstance(content, (dict, list)):
        content_str = json.dumps(content, indent=4, ensure_ascii=False)
        content_type = 'application/json'
    else:
        content_str = str(content)
        content_type = 'text/plain'
    
    try:
        print(f"Writing to: {path}")
        
        # Validate it's a GCS path
        if not path.startswith('gs://'):
            raise ValueError(f"Path must start with gs://, got: {path}")
        
        parsed = urlparse(path)
        bucket_name = parsed.netloc
        blob_path = parsed.path.lstrip('/')
        
        # Validate bucket name
        if not bucket_name:
            raise ValueError(f"Invalid GCS path - no bucket name in: {path}")
        
        # Validate blob path (object name)
        if not blob_path:
            raise ValueError(f"Invalid GCS path - no object name in: {path}. Expected format: gs://bucket/path/file.json")
        
        print(f"  Bucket: {bucket_name}")
        print(f"  Object: {blob_path}")
        print(f"  Content size: {len(content_str)} characters")
        
        client = gcs_storage.Client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.content_type = content_type
        
        blob.upload_from_string(content_str)
        print(f"✓ Successfully wrote to gs://{bucket_name}/{blob_path}")
        
    except ValueError:
        raise
    except Exception as e:
        print(f"✗ Error writing to {path}: {type(e).__name__}: {e}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        raise Exception(f"Failed to write to GCS: {str(e)}")