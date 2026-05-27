import os
import boto3

ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

_CACHE: dict[str, boto3.client] = {}


def client(service: str) -> boto3.client:
    """Return a cached boto3 client for the given AWS service name."""
    if service not in _CACHE:
        _CACHE[service] = boto3.client(
            service,
            aws_access_key_id="test",
            aws_secret_access_key="test",
            region_name=REGION,
            endpoint_url=ENDPOINT,
        )
    return _CACHE[service]
