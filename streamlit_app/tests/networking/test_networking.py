"""Unit tests for pages/networking/ modules."""
import sys
from unittest.mock import MagicMock, patch


def _st():
    m = MagicMock()
    m.session_state = MagicMock()
    m.columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))]
    m.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    return m


class TestVPCPage:
    def setup_method(self):
        self.mock_ec2 = MagicMock()
        self.mock_ec2.describe_vpcs.return_value = {"Vpcs": []}

    def test_describe_vpcs_called(self):
        with patch("aws_client.client", return_value=self.mock_ec2):
            sys.modules.pop("pages.networking.vpc", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.networking import vpc
                vpc.render()
        self.mock_ec2.describe_vpcs.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_ec2.describe_vpcs.side_effect = Exception("unreachable")
        with patch("aws_client.client", return_value=self.mock_ec2):
            sys.modules.pop("pages.networking.vpc", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.networking import vpc
                vpc.render()
        st_mock.error.assert_called()


class TestAPIGatewayPage:
    def setup_method(self):
        self.mock_apigw = MagicMock()
        self.mock_apigw.get_rest_apis.return_value = {"items": []}

    def test_get_rest_apis_called(self):
        with patch("aws_client.client", return_value=self.mock_apigw):
            sys.modules.pop("pages.networking.apigateway", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.networking import apigateway
                apigateway.render()
        self.mock_apigw.get_rest_apis.assert_called_once()


class TestAPIGatewayV2Page:
    def setup_method(self):
        self.mock_apigwv2 = MagicMock()
        self.mock_apigwv2.get_apis.return_value = {"Items": []}

    def test_get_apis_called(self):
        with patch("aws_client.client", return_value=self.mock_apigwv2):
            sys.modules.pop("pages.networking.apigatewayv2", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.networking import apigatewayv2
                apigatewayv2.render()
        self.mock_apigwv2.get_apis.assert_called_once()


class TestALBPage:
    def setup_method(self):
        self.mock_elb = MagicMock()
        self.mock_elb.describe_load_balancers.return_value = {"LoadBalancers": []}

    def test_describe_load_balancers_called(self):
        with patch("aws_client.client", return_value=self.mock_elb):
            sys.modules.pop("pages.networking.alb", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.networking import alb
                alb.render()
        self.mock_elb.describe_load_balancers.assert_called_once()


class TestRoute53Page:
    def setup_method(self):
        self.mock_r53 = MagicMock()
        self.mock_r53.list_hosted_zones.return_value = {"HostedZones": []}

    def test_list_hosted_zones_called(self):
        with patch("aws_client.client", return_value=self.mock_r53):
            sys.modules.pop("pages.networking.route53", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.networking import route53
                route53.render()
        self.mock_r53.list_hosted_zones.assert_called_once()


class TestCloudFrontPage:
    def setup_method(self):
        self.mock_cf = MagicMock()
        self.mock_cf.list_distributions.return_value = {
            "DistributionList": {"Items": [], "Quantity": 0}
        }

    def test_list_distributions_called(self):
        with patch("aws_client.client", return_value=self.mock_cf):
            sys.modules.pop("pages.networking.cloudfront", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.networking import cloudfront
                cloudfront.render()
        self.mock_cf.list_distributions.assert_called_once()
