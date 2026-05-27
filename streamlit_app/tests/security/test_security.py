"""Unit tests for pages/security/ modules."""
import sys
from unittest.mock import MagicMock, patch


def _st():
    m = MagicMock()
    m.session_state = MagicMock()
    m.columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))]
    m.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    return m


class TestIAMPage:
    def setup_method(self):
        self.mock_iam = MagicMock()
        self.mock_iam.list_users.return_value = {"Users": []}
        self.mock_iam.list_roles.return_value = {"Roles": []}
        self.mock_iam.list_policies.return_value = {"Policies": []}

    def test_list_users_called(self):
        with patch("aws_client.client", return_value=self.mock_iam):
            sys.modules.pop("pages.security.iam", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.security import iam
                iam.render()
        self.mock_iam.list_users.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_iam.list_users.side_effect = Exception("auth error")
        with patch("aws_client.client", return_value=self.mock_iam):
            sys.modules.pop("pages.security.iam", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.security import iam
                iam.render()
        st_mock.error.assert_called()


class TestKMSPage:
    def setup_method(self):
        self.mock_kms = MagicMock()
        self.mock_kms.list_keys.return_value = {"Keys": []}

    def test_list_keys_called(self):
        with patch("aws_client.client", return_value=self.mock_kms):
            sys.modules.pop("pages.security.kms", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.security import kms
                kms.render()
        self.mock_kms.list_keys.assert_called_once()


class TestSTSPage:
    def setup_method(self):
        self.mock_sts = MagicMock()
        self.mock_sts.get_caller_identity.return_value = {
            "Account": "000000000000",
            "UserId": "AKIAIOSFODNN7EXAMPLE",
            "Arn": "arn:aws:iam::000000000000:root",
        }

    def test_get_caller_identity_called(self):
        with patch("aws_client.client", return_value=self.mock_sts):
            sys.modules.pop("pages.security.sts", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.security import sts
                sts.render()
        self.mock_sts.get_caller_identity.assert_called()

    def test_error_handled_gracefully(self):
        self.mock_sts.get_caller_identity.side_effect = Exception("STS error")
        with patch("aws_client.client", return_value=self.mock_sts):
            sys.modules.pop("pages.security.sts", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.security import sts
                sts.render()
        st_mock.error.assert_called()


class TestSecretsManagerPage:
    def setup_method(self):
        self.mock_sm = MagicMock()
        self.mock_sm.list_secrets.return_value = {"SecretList": []}

    def test_list_secrets_called(self):
        with patch("aws_client.client", return_value=self.mock_sm):
            sys.modules.pop("pages.security.secretsmanager", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.security import secretsmanager
                secretsmanager.render()
        self.mock_sm.list_secrets.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_sm.list_secrets.side_effect = Exception("permission denied")
        with patch("aws_client.client", return_value=self.mock_sm):
            sys.modules.pop("pages.security.secretsmanager", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.security import secretsmanager
                secretsmanager.render()
        st_mock.error.assert_called()


class TestCognitoPage:
    def setup_method(self):
        self.mock_cognito = MagicMock()
        self.mock_cognito.list_user_pools.return_value = {"UserPools": []}
        self.mock_cognito.list_identity_pools.return_value = {"IdentityPools": []}

    def test_list_user_pools_called(self):
        with patch("aws_client.client", return_value=self.mock_cognito):
            sys.modules.pop("pages.security.cognito", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.security import cognito
                cognito.render()
        self.mock_cognito.list_user_pools.assert_called()


class TestACMPage:
    def setup_method(self):
        self.mock_acm = MagicMock()
        self.mock_acm.list_certificates.return_value = {"CertificateSummaryList": []}

    def test_list_certificates_called(self):
        with patch("aws_client.client", return_value=self.mock_acm):
            sys.modules.pop("pages.security.acm", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.security import acm
                acm.render()
        self.mock_acm.list_certificates.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_acm.list_certificates.side_effect = Exception("ACM error")
        with patch("aws_client.client", return_value=self.mock_acm):
            sys.modules.pop("pages.security.acm", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.security import acm
                acm.render()
        st_mock.error.assert_called()
