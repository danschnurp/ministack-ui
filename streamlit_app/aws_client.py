import os
import boto3

ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
REGION = "us-east-1"
CREDENTIALS = dict(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name=REGION,
    endpoint_url=ENDPOINT,
)


def client(service: str):
    return boto3.client(service, **CREDENTIALS)

