import boto3
import logging
from .config import R2_CONFIG

logger = logging.getLogger(__name__)

class R2StorageManager:
    """Class to handle R2 storage operations."""
    
    def __init__(self, config=R2_CONFIG):
        """Initialize with R2 configuration."""
        self.config = config
        self.client = self._create_client()
        
    def _create_client(self):
        """Create and return an S3 client configured for R2."""
        try:
            client = boto3.client(
                's3',
                endpoint_url=self.config['endpoint_url'],
                aws_access_key_id=self.config['aws_access_key_id'],
                aws_secret_access_key=self.config['aws_secret_access_key']
            )
            logger.info("Successfully created R2 client")
            return client
        except Exception as e:
            logger.error(f"Failed to create R2 client: {str(e)}")
            raise

    def upload_file(self, key, file_obj, bucket='tasks'):
        """Upload file-like object to specified bucket"""
        try:
            file_obj.seek(0)  # Reset file position
            self.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=bucket,
                Key=key
            )
            logger.info(f"Uploaded {key} to {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {key} to {bucket}: {str(e)}")
            return False