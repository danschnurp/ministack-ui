"""Unit tests for pages/compute/ modules."""
import sys
from unittest.mock import MagicMock, patch


def _st():
    m = MagicMock()
    m.session_state = MagicMock()
    m.columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))]
    m.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    return m


class TestEC2Page:
    def setup_method(self):
        self.mock_ec2 = MagicMock()
        self.mock_ec2.describe_instances.return_value = {"Reservations": []}

    def test_describe_instances_called(self):
        with patch("aws_client.client", return_value=self.mock_ec2):
            sys.modules.pop("pages.compute.ec2", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.compute import ec2
                ec2.render()
        self.mock_ec2.describe_instances.assert_called()

    def test_error_handled_gracefully(self):
        self.mock_ec2.describe_instances.side_effect = Exception("unreachable")
        with patch("aws_client.client", return_value=self.mock_ec2):
            sys.modules.pop("pages.compute.ec2", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.compute import ec2
                ec2.render()
        st_mock.error.assert_called()


class TestECSPage:
    def setup_method(self):
        self.mock_ecs = MagicMock()
        self.mock_ecs.list_clusters.return_value = {"clusterArns": []}
        self.mock_ecs.describe_clusters.return_value = {"clusters": []}

    def test_list_clusters_called(self):
        with patch("aws_client.client", return_value=self.mock_ecs):
            sys.modules.pop("pages.compute.ecs", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.compute import ecs
                ecs.render()
        self.mock_ecs.list_clusters.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_ecs.list_clusters.side_effect = Exception("connection error")
        with patch("aws_client.client", return_value=self.mock_ecs):
            sys.modules.pop("pages.compute.ecs", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.compute import ecs
                ecs.render()
        st_mock.error.assert_called()


class TestEKSPage:
    def setup_method(self):
        self.mock_eks = MagicMock()
        self.mock_eks.list_clusters.return_value = {"clusters": []}

    def test_list_clusters_called(self):
        with patch("aws_client.client", return_value=self.mock_eks):
            sys.modules.pop("pages.compute.eks", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.compute import eks
                eks.render()
        self.mock_eks.list_clusters.assert_called_once()


class TestLambdaPage:
    def setup_method(self):
        self.mock_lambda = MagicMock()
        self.mock_lambda.list_functions.return_value = {"Functions": []}

    def test_list_functions_called(self):
        with patch("aws_client.client", return_value=self.mock_lambda):
            sys.modules.pop("pages.compute.lambda_", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.compute import lambda_
                lambda_.render()
        self.mock_lambda.list_functions.assert_called()

    def test_error_handled_gracefully(self):
        self.mock_lambda.list_functions.side_effect = Exception("timeout")
        with patch("aws_client.client", return_value=self.mock_lambda):
            sys.modules.pop("pages.compute.lambda_", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.compute import lambda_
                lambda_.render()
        st_mock.error.assert_called()


class TestBatchPage:
    def setup_method(self):
        self.mock_batch = MagicMock()
        self.mock_batch.describe_compute_environments.return_value = {"computeEnvironments": []}
        self.mock_batch.describe_job_queues.return_value = {"jobQueues": []}
        self.mock_batch.describe_job_definitions.return_value = {"jobDefinitions": []}

    def test_compute_environments_called(self):
        with patch("aws_client.client", return_value=self.mock_batch):
            sys.modules.pop("pages.compute.batch", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.compute import batch
                batch.render()
        self.mock_batch.describe_compute_environments.assert_called_once()


class TestCodeBuildPage:
    def setup_method(self):
        self.mock_cb = MagicMock()
        self.mock_cb.list_projects.return_value = {"projects": []}

    def test_list_projects_called(self):
        with patch("aws_client.client", return_value=self.mock_cb):
            sys.modules.pop("pages.compute.codebuild", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.compute import codebuild
                codebuild.render()
        self.mock_cb.list_projects.assert_called_once()
