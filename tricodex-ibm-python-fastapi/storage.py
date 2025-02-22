# storage.py
import os
from typing import Optional
import ibm_boto3
from ibm_boto3.s3.transfer import TransferConfig
from ibm_botocore.client import Config
import logging

logger = logging.getLogger(__name__)

class IBMCloudStorage:
    def __init__(self):
        # IBM COS credentials from environment
        self.cos_endpoint = os.getenv('IBM_COS_ENDPOINT')
        self.cos_api_key = os.getenv('IBM_COS_API_KEY')
        self.cos_instance_crn = os.getenv('IBM_COS_INSTANCE_CRN')
        self.cos_bucket_name = os.getenv('IBM_COS_BUCKET_NAME')
        
        # Initialize IBM COS client
        self.cos_client = ibm_boto3.client(
            's3',
            ibm_api_key_id=self.cos_api_key,
            ibm_service_instance_id=self.cos_instance_crn,
            config=Config(signature_version='oauth'),
            endpoint_url=self.cos_endpoint
        )
        
        # Configure transfer settings for large files
        self.transfer_config = TransferConfig(
            multipart_threshold=1024 * 1024 * 5,  # 5MB
            max_concurrency=10,
            multipart_chunksize=1024 * 1024 * 5,  # 5MB
            use_threads=True
        )

    async def upload_file(self, file_content: bytes, file_name: str, metadata: dict = None) -> str:
        """Upload file to IBM Cloud Object Storage and return the key"""
        try:
            # Generate a unique key based on timestamp and filename
            from datetime import datetime
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            key = f"processlens/uploads/{timestamp}_{file_name}"
            
            # Prepare extra args for upload
            extra_args = {
                'Metadata': metadata if metadata else {},
                'ContentType': self._get_content_type(file_name)
            }
            
            # Upload to IBM COS
            self.cos_client.put_object(
                Bucket=self.cos_bucket_name,
                Key=key,
                Body=file_content,
                **extra_args
            )
            
            logger.info(f"Successfully uploaded file to IBM COS: {key}")
            return key
            
        except Exception as e:
            logger.error(f"Error uploading file to IBM COS: {e}")
            raise

    async def get_file(self, key: str) -> Optional[bytes]:
        """Retrieve file from IBM Cloud Object Storage"""
        try:
            response = self.cos_client.get_object(
                Bucket=self.cos_bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except Exception as e:
            logger.error(f"Error retrieving file from IBM COS: {e}")
            raise

    async def delete_file(self, key: str) -> bool:
        """Delete file from IBM Cloud Object Storage"""
        try:
            self.cos_client.delete_object(
                Bucket=self.cos_bucket_name,
                Key=key
            )
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from IBM COS: {e}")
            return False

    async def get_file_metadata(self, key: str) -> dict:
        """Get file metadata from IBM Cloud Object Storage"""
        try:
            response = self.cos_client.head_object(
                Bucket=self.cos_bucket_name,
                Key=key
            )
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            logger.error(f"Error getting file metadata from IBM COS: {e}")
            raise

    def _get_content_type(self, filename: str) -> str:
        """Determine content type based on file extension"""
        extension = filename.lower().split('.')[-1]
        content_types = {
            'csv': 'text/csv',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'json': 'application/json',
            'xml': 'text/xml',
            'txt': 'text/plain'
        }
        return content_types.get(extension, 'application/octet-stream')