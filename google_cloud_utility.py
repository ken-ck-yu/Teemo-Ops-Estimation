"""
Google Cloud utilities for Secret Manager and other GCP services
"""

import os
from google.cloud import secretmanager


def get_secret(project_id, secret_id, version_id="latest"):
    
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    
    try:
        response = client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode('UTF-8')
        print(f"Successfully retrieved secret: {secret_id}")
        return payload
        
    except Exception as e:
        raise Exception(f"Failed to access secret '{secret_id}': {e}")
