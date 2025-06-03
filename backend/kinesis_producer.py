import boto3
import json
import os

# Make sure your AWS credentials are configured via environment or ~/.aws
REGION_NAME = "ap-south-1"
STREAM_NAME = "Vote_Major_Project"  # Replace with your actual stream name

kinesis = boto3.client("kinesis", region_name=REGION_NAME)

def send_vote_to_kinesis(vote_data):
    kinesis.put_record(
        StreamName=STREAM_NAME,
        Data=json.dumps(vote_data),
        PartitionKey="vote"
    )
    print("Vote sent to Kinesis:", response)
