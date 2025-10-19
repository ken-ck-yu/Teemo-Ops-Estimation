"""
Google Cloud Storage file reading utility
"""

from urllib.parse import urlparse
from google.cloud import storage as gcs_storage


def read_file_content(path):
    parsed = urlparse(path)
    
    client = gcs_storage.Client()
    bucket = client.bucket(parsed.netloc)
    blob = bucket.blob(parsed.path.lstrip('/'))
    
    print(f"Reading from GCS: {parsed.netloc}/{parsed.path.lstrip('/')}")
    try:
        return blob.download_as_text()
    except Exception as e:
        raise Exception(f"Failed to read from GCS: {e}")

