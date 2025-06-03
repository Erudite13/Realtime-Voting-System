
import json
import boto3
import base64
from datetime import datetime

s3 = boto3.client('s3')
BUCKET_NAME = "votesbucketmajorproject"

def lambda_handler(event, context):
    for record in event['Records']:
        # Decode the base64 encoded Kinesis record
        payload = base64.b64decode(record['kinesis']['data']).decode('utf-8')
        vote_data = json.loads(payload)

        vote_id = vote_data.get("vote_id", f"vote_{datetime.now().timestamp()}")

        # Save vote to S3 with unique name
        object_key = f"votes/{vote_id}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
            Body=json.dumps(vote_data),
            ContentType='application/json'
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Vote processed and saved to S3!')
    }
