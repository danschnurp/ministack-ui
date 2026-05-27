"""Unit tests for pages/config_ops/ modules."""
import sys
from unittest.mock import MagicMock, patch


def _st():
    m = MagicMock()
    m.session_state = MagicMock()
    m.columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))]
    m.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    m.text_input.return_value = "/"
    m.checkbox.return_value = True
    return m


class TestSSMPage:
    def setup_method(self):
        self.mock_ssm = MagicMock()
        paginator_mock = MagicMock()
        paginator_mock.paginate.return_value = [{"Parameters": []}]
        self.mock_ssm.get_paginator.return_value = paginator_mock

    def test_get_paginator_called(self):
        with patch("aws_client.client", return_value=self.mock_ssm):
            sys.modules.pop("pages.config_ops.ssm", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.config_ops import ssm
                ssm.render()
        self.mock_ssm.get_paginator.assert_called_with("get_parameters_by_path")

    def test_error_handled_gracefully(self):
        self.mock_ssm.get_paginator.side_effect = Exception("SSM error")
        with patch("aws_client.client", return_value=self.mock_ssm):
            sys.modules.pop("pages.config_ops.ssm", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.config_ops import ssm
                ssm.render()
        st_mock.error.assert_called()


class TestCloudFormationPage:
    def setup_method(self):
        self.mock_cfn = MagicMock()
        self.mock_cfn.describe_stacks.return_value = {"Stacks": []}

    def test_describe_stacks_called(self):
        with patch("aws_client.client", return_value=self.mock_cfn):
            sys.modules.pop("pages.config_ops.cloudformation", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.config_ops import cloudformation
                cloudformation.render()
        self.mock_cfn.describe_stacks.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_cfn.describe_stacks.side_effect = Exception("CFN error")
        with patch("aws_client.client", return_value=self.mock_cfn):
            sys.modules.pop("pages.config_ops.cloudformation", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.config_ops import cloudformation
                cloudformation.render()
        st_mock.error.assert_called()


class TestCloudTrailPage:
    def setup_method(self):
        self.mock_ct = MagicMock()
        self.mock_ct.describe_trails.return_value = {"trailList": []}
        self.mock_ct.lookup_events.return_value = {"Events": []}

    def test_describe_trails_called(self):
        with patch("aws_client.client", return_value=self.mock_ct):
            sys.modules.pop("pages.config_ops.cloudtrail", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.config_ops import cloudtrail
                cloudtrail.render()
        self.mock_ct.describe_trails.assert_called_once()


class TestAutoScalingPage:
    def setup_method(self):
        self.mock_asg = MagicMock()
        self.mock_asg.describe_auto_scaling_groups.return_value = {"AutoScalingGroups": []}

    def test_describe_asgs_called(self):
        with patch("aws_client.client", return_value=self.mock_asg):
            sys.modules.pop("pages.config_ops.autoscaling", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.config_ops import autoscaling
                autoscaling.render()
        self.mock_asg.describe_auto_scaling_groups.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_asg.describe_auto_scaling_groups.side_effect = Exception("ASG error")
        with patch("aws_client.client", return_value=self.mock_asg):
            sys.modules.pop("pages.config_ops.autoscaling", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.config_ops import autoscaling
                autoscaling.render()
        st_mock.error.assert_called()


class TestBackupPage:
    def setup_method(self):
        self.mock_backup = MagicMock()
        self.mock_backup.list_backup_vaults.return_value = {"BackupVaultList": []}
        self.mock_backup.list_backup_plans.return_value = {"BackupPlansList": []}

    def test_list_backup_vaults_called(self):
        with patch("aws_client.client", return_value=self.mock_backup):
            sys.modules.pop("pages.config_ops.backup", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.config_ops import backup
                backup.render()
        self.mock_backup.list_backup_vaults.assert_called()
