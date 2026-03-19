import os
import boto3
from dotenv import load_dotenv

def main():
    load_dotenv()

    endpoint_url = os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL')
    access_key = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID')
    secret_key = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    bucket_name = os.environ.get('CLOUDFLARE_R2_STORAGE_BUCKET_NAME', 'tempest-fileshare')

    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name='auto'
    )

    lifecycle_configuration = {
        'Rules': [
            {
                'ID': 'DeleteFilesOlderThan3Days',
                'Filter': {'Prefix': ''},
                'Status': 'Enabled',
                'Expiration': {
                    'Days': 3
                }
            }
        ]
    }

    try:
        response = s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration=lifecycle_configuration
        )
        print("Successfully applied 72-hour (3-day) deletion policy to R2 bucket!")
        print(f"Response: {response.get('ResponseMetadata', {}).get('HTTPStatusCode')}")
    except Exception as e:
        print(f"Error applying lifecycle policy: {e}")

if __name__ == "__main__":
    main()
