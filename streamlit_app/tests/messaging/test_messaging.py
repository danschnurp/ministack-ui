"""Unit tests for pages/messaging/ modules."""
import sys
from unittest.mock import MagicMock, patch


def _st():
    m = MagicMock()
    m.session_state = MagicMock()
    m.columns.side_effect = lambda spec: [MagicMock() for _ in (spec if isinstance(spec, (list, tuple)) else range(spec))]
    m.tabs.side_effect = lambda labels: [MagicMock() for _ in labels]
    return m


class TestSQSPage:
    def setup_method(self):
        self.mock_sqs = MagicMock()
        self.mock_sqs.list_queues.return_value = {"QueueUrls": []}

    def test_list_queues_called(self):
        with patch("aws_client.client", return_value=self.mock_sqs):
            sys.modules.pop("pages.messaging.sqs", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.messaging import sqs
                sqs.render()
        self.mock_sqs.list_queues.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_sqs.list_queues.side_effect = Exception("SQS error")
        with patch("aws_client.client", return_value=self.mock_sqs):
            sys.modules.pop("pages.messaging.sqs", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.messaging import sqs
                sqs.render()
        st_mock.error.assert_called()


class TestSNSPage:
    def setup_method(self):
        self.mock_sns = MagicMock()
        self.mock_sns.list_topics.return_value = {"Topics": []}

    def test_list_topics_called(self):
        with patch("aws_client.client", return_value=self.mock_sns):
            sys.modules.pop("pages.messaging.sns", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.messaging import sns
                sns.render()
        self.mock_sns.list_topics.assert_called_once()


class TestSESPage:
    def setup_method(self):
        self.mock_ses = MagicMock()
        self.mock_ses.list_identities.return_value = {"Identities": []}

    def test_list_identities_called(self):
        with patch("aws_client.client", return_value=self.mock_ses):
            sys.modules.pop("pages.messaging.ses", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.messaging import ses
                ses.render()
        self.mock_ses.list_identities.assert_called_once()

    def test_error_handled_gracefully(self):
        self.mock_ses.list_identities.side_effect = Exception("SES error")
        with patch("aws_client.client", return_value=self.mock_ses):
            sys.modules.pop("pages.messaging.ses", None)
            st_mock = _st()
            with patch.dict("sys.modules", {"streamlit": st_mock}):
                from pages.messaging import ses
                ses.render()
        st_mock.error.assert_called()


class TestEventBridgePage:
    def setup_method(self):
        self.mock_eb = MagicMock()
        self.mock_eb.list_event_buses.return_value = {"EventBuses": []}

    def test_list_event_buses_called(self):
        with patch("aws_client.client", return_value=self.mock_eb):
            sys.modules.pop("pages.messaging.eventbridge", None)
            with patch.dict("sys.modules", {"streamlit": _st()}):
                from pages.messaging import eventbridge
                eventbridge.render()
        self.mock_eb.list_event_buses.assert_called()
