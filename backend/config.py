import os

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
STREAM_NAME = os.getenv("KINESIS_STREAM_NAME", "Vote_Major_Project")
