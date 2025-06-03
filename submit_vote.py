import boto3
import json
import time

# Replace this with your desired candidate name
CANDIDATE_NAME = "Alice"  # or Bob, Charlie, etc.

# AWS Configuration
AWS_REGION = "ap-south-1"
KINESIS_STREAM_NAME = "Vote_Major_Project"

# Create Kinesis client
kinesis_client = boto3.client("kinesis", region_name=AWS_REGION)

# Vote payload
vote_payload = {
    "candidate": CANDIDATE_NAME,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
}

# Send vote to Kinesis stream
try:
    response = kinesis_client.put_record(
        StreamName=KINESIS_STREAM_NAME,
        Data=json.dumps(vote_payload),
        PartitionKey="vote-partition"
    )
    print(f"✅ Vote for '{CANDIDATE_NAME}' submitted successfully!")
    print("Response:", response)

except Exception as e:
    print("❌ Error submitting vote:", str(e))
