"""
Flexible file reading utility - supports both local files and GCS
"""

import os
from urllib.parse import urlparse
from google.cloud import storage

def read_file_content(file_path):
    """
    Read file content from either local filesystem or GCS.
    
    Args:
        file_path: Path to file. Can be:
                  - Local path: 'prompts/system_prompt.txt' or '/workspace/prompts/system_prompt.txt'
                  - GCS path: 'gs://bucket-name/path/to/file.txt'
    
    Returns:
        str: File content as string
    
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: For other read errors
    """
    try:
        # Check if it's a GCS path
        if file_path.startswith('gs://'):
            print(f"Reading from GCS: {file_path}")
            parsed = urlparse(file_path)
            bucket_name = parsed.netloc
            blob_path = parsed.path.lstrip('/')
            
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            
            if not blob.exists():
                raise FileNotFoundError(f"GCS file not found: {file_path}")
            
            content = blob.download_as_text()
            print(f"✓ Read {len(content)} characters from GCS")
            return content
        
        else:
            # Local file path
            print(f"Reading from local file: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Local file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"✓ Read {len(content)} characters from local file")
            return content
            
    except FileNotFoundError:
        raise
    except Exception as e:
        print(f"✗ Error reading file {file_path}: {e}")
        raise Exception(f"Failed to read file {file_path}: {str(e)}")
