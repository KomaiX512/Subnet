"""Module for retrieving data from R2 storage."""

import json
import logging
import boto3
from tenacity import retry, stop_after_attempt, wait_exponential
from .config import R2_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class R2DataRetriever:
    """Class to handle data retrieval from R2 storage."""
    
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
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def list_objects(self):
        """List objects in the R2 bucket."""
        try:
            response = self.client.list_objects_v2(Bucket=self.config['bucket_name'])
            objects = response.get('Contents', [])
            logger.info(f"Found {len(objects)} objects in bucket")
            return objects
        except Exception as e:
            logger.error(f"Error listing objects: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_object(self, key):
        """Get an object from the R2 bucket."""
        try:
            logger.info(f"Retrieving object: {key}")
            response = self.client.get_object(
                Bucket=self.config['bucket_name'],
                Key=key
            )
            return response
        except Exception as e:
            logger.error(f"Error retrieving object {key}: {str(e)}")
            raise
    
    def get_json_data(self, key):
        """Get and parse JSON data from an object."""
        try:
            response = self.get_object(key)
            content = response['Body'].read()
            data = json.loads(content)
            logger.info(f"Successfully retrieved and parsed JSON data from {key}")
            return data
        except Exception as e:
            logger.error(f"Error parsing JSON from {key}: {str(e)}")
            return None  # Return None instead of {}
    
    def get_social_media_data(self, key='humansofny/humansofny_20250404_112030.json'):
        """Get social media data specifically."""
        return self.get_json_data(key)

    def upload_file(self, key, file_obj):
        """
        Upload a file to R2 storage.
        
        Args:
            key: The key (filename) to use in R2
            file_obj: File object to upload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.upload_fileobj(file_obj, self.config['bucket_name'], key)
            logger.info(f"Successfully uploaded file to {key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading file to {key}: {str(e)}")
            return False


# Function to test the data retrieval
def test_connection():
    """Test connection to R2 and basic retrieval."""
    try:
        retriever = R2DataRetriever()
        objects = retriever.list_objects()
        
        if objects:
            sample_key = objects[0]['Key']
            logger.info(f"Testing retrieval with object: {sample_key}")
            response = retriever.get_object(sample_key)
            size = response['ContentLength']
            logger.info(f"Successfully retrieved {sample_key} ({size} bytes)")
            return True
        else:
            logger.warning("No objects found in bucket")
            return False
            
    except Exception as e:
        logger.error(f"Test connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the connection and data retrieval
    success = test_connection()
    print(f"Connection test {'successful' if success else 'failed'}")