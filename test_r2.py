import boto3
import os
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

def test_r2():
    endpoint_url = os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL')
    access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID')
    secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    bucket_name = os.environ.get('CLOUDFLARE_R2_STORAGE_BUCKET_NAME')
    
    print(f"Testing R2 connection to bucket: {bucket_name}")
    print(f"Endpoint: {endpoint_url}")
    print(f"Access Key: {access_key[:8]}... (starts with)")
    
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='auto'
    )
    
    try:
        print("Attempting HeadBucket...")
        s3.head_bucket(Bucket=bucket_name)
        print("HeadBucket successful!")
        
        print("Attempting ListObjectsV2...")
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print("ListObjectsV2 successful!")
        
    except Exception as e:
        print(f"Error during R2 test: {e}")

if __name__ == "__main__":
    test_r2()
