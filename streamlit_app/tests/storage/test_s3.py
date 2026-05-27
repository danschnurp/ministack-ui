"""Unit tests for pages/storage/s3.py — render() logic helpers."""
import sys
from unittest.mock import MagicMock, patch


def _st():
    m = MagicMock()
    m.session_state = MagicMock()
    m.columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))]
    m.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    return m


class TestS3PageClientCalls:
    def setup_method(self):
        self.mock_s3 = MagicMock()
        self.mock_s3.list_buckets.return_value = {
            "Buckets": [
                {"Name": "bucket-a", "CreationDate": "2024-01-01"},
                {"Name": "bucket-b", "CreationDate": "2024-02-01"},
            ]
        }

    def test_list_buckets_called(self):
        with patch("aws_client.client", return_value=self.mock_s3):
            sys.modules.pop("pages.storage.s3", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.storage import s3
                s3.render()
        self.mock_s3.list_buckets.assert_called_once()

    def test_render_handles_client_error(self):
        self.mock_s3.list_buckets.side_effect = Exception("connection refused")
        with patch("aws_client.client", return_value=self.mock_s3):
            sys.modules.pop("pages.storage.s3", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.storage import s3
                s3.render()
        st_mock.error.assert_called()


class TestDynamoPageClientCalls:
    def setup_method(self):
        self.mock_ddb = MagicMock()
        self.mock_ddb.list_tables.return_value = {"TableNames": ["users", "orders"]}

    def test_list_tables_called(self):
        with patch("aws_client.client", return_value=self.mock_ddb):
            sys.modules.pop("pages.storage.dynamo", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.storage import dynamo
                dynamo.render()
        self.mock_ddb.list_tables.assert_called()

    def test_render_handles_client_error(self):
        self.mock_ddb.list_tables.side_effect = Exception("timeout")
        with patch("aws_client.client", return_value=self.mock_ddb):
            sys.modules.pop("pages.storage.dynamo", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.storage import dynamo
                dynamo.render()
        st_mock.error.assert_called()


class TestRDSPageClientCalls:
    def setup_method(self):
        self.mock_rds = MagicMock()
        self.mock_rds.describe_db_instances.return_value = {"DBInstances": []}
        self.mock_rds.describe_db_snapshots.return_value = {"DBSnapshots": []}

    def test_describe_instances_called(self):
        with patch("aws_client.client", return_value=self.mock_rds):
            sys.modules.pop("pages.storage.rds", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.storage import rds
                rds.render()
        self.mock_rds.describe_db_instances.assert_called_once()

    def test_render_handles_client_error(self):
        self.mock_rds.describe_db_instances.side_effect = Exception("not reachable")
        with patch("aws_client.client", return_value=self.mock_rds):
            sys.modules.pop("pages.storage.rds", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.storage import rds
                rds.render()
        st_mock.error.assert_called()


class TestEBSPageClientCalls:
    def setup_method(self):
        self.mock_ec2 = MagicMock()
        self.mock_ec2.describe_volumes.return_value = {"Volumes": []}
        self.mock_ec2.describe_snapshots.return_value = {"Snapshots": []}

    def test_describe_volumes_called(self):
        with patch("aws_client.client", return_value=self.mock_ec2):
            sys.modules.pop("pages.storage.ebs", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.storage import ebs
                ebs.render()
        self.mock_ec2.describe_volumes.assert_called_once()


class TestECRPageClientCalls:
    def setup_method(self):
        self.mock_ecr = MagicMock()
        self.mock_ecr.describe_repositories.return_value = {"repositories": []}

    def test_describe_repos_called(self):
        with patch("aws_client.client", return_value=self.mock_ecr):
            sys.modules.pop("pages.storage.ecr", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.storage import ecr
                ecr.render()
        self.mock_ecr.describe_repositories.assert_called_once()
