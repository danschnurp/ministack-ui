"""Unit tests for aws_client module."""
import importlib
import os
from unittest.mock import patch, MagicMock

import pytest


def _reload():
    """Reload aws_client, which also resets its module-level _CACHE."""
    import aws_client
    importlib.reload(aws_client)
    return aws_client


class TestClientFactory:
    def test_returns_boto3_client(self):
        mock_boto_client = MagicMock()
        with patch("boto3.client", return_value=mock_boto_client):
            ac = _reload()
            result = ac.client("s3")
            assert result is mock_boto_client

    def test_uses_default_endpoint(self):
        env = {k: v for k, v in os.environ.items() if k != "LOCALSTACK_ENDPOINT"}
        with patch.dict(os.environ, env, clear=True):
            with patch("boto3.client") as mock_boto:
                ac = _reload()
                ac.client("s3")
                assert mock_boto.call_args[1]["endpoint_url"] == "http://localhost:4566"

    def test_uses_env_endpoint_override(self):
        custom_url = "http://custom-host:9999"
        with patch.dict(os.environ, {"LOCALSTACK_ENDPOINT": custom_url}):
            with patch("boto3.client") as mock_boto:
                ac = _reload()
                ac.client("dynamodb")
                assert mock_boto.call_args[1]["endpoint_url"] == custom_url

    def test_uses_test_credentials(self):
        with patch("boto3.client") as mock_boto:
            ac = _reload()
            ac.client("sqs")
            kw = mock_boto.call_args[1]
            assert kw["aws_access_key_id"] == "test"
            assert kw["aws_secret_access_key"] == "test"

    def test_uses_us_east_1_region_by_default(self):
        env = {k: v for k, v in os.environ.items() if k != "AWS_DEFAULT_REGION"}
        with patch.dict(os.environ, env, clear=True):
            with patch("boto3.client") as mock_boto:
                ac = _reload()
                ac.client("sns")
                assert mock_boto.call_args[1]["region_name"] == "us-east-1"

    def test_uses_env_region_override(self):
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "eu-west-1"}):
            with patch("boto3.client") as mock_boto:
                ac = _reload()
                ac.client("sns")
                assert mock_boto.call_args[1]["region_name"] == "eu-west-1"

    def test_passes_service_name(self):
        with patch("boto3.client") as mock_boto:
            ac = _reload()
            ac.client("kinesis")
            assert mock_boto.call_args[0][0] == "kinesis"

    def test_client_is_cached(self):
        """Calling client() twice for the same service returns the same object."""
        mock_boto_client = MagicMock()
        with patch("boto3.client", return_value=mock_boto_client) as mock_boto:
            ac = _reload()
            first = ac.client("s3")
            second = ac.client("s3")
            assert first is second
            mock_boto.assert_called_once()
