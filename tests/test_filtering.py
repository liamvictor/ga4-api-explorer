import unittest
from unittest import mock
from reports import channel_traffic_by_hour_report

class TestChannelTrafficByHourReport(unittest.TestCase):

    def test_run_report_filtering(self):
        """
        Test that categories with zero total sessions are filtered out.
        """
        mock_data_client = mock.Mock()
        mock_response = mock.Mock()

        # Mock dimension headers
        dim_hour = mock.Mock()
        dim_hour.name = "hour"
        dim_channel = mock.Mock()
        dim_channel.name = "sessionDefaultChannelGroup"
        mock_response.dimension_headers = [dim_hour, dim_channel]
        
        # Mock metric headers
        met_sessions = mock.Mock()
        met_sessions.name = "sessions"
        met_users = mock.Mock()
        met_users.name = "activeUsers"
        met_engagement = mock.Mock()
        met_engagement.name = "engagementRate"
        mock_response.metric_headers = [met_sessions, met_users, met_engagement]

        # Mock rows:
        # 1. Organic Search: 10 sessions (Should stay)
        mock_row1 = mock.Mock()
        mock_row1.dimension_values = [mock.Mock(value="08"), mock.Mock(value="Organic Search")]
        mock_row1.metric_values = [mock.Mock(value="10"), mock.Mock(value="10"), mock.Mock(value="0.5")]

        # 2. Canada: 0 sessions, 1 user (Should be filtered out)
        mock_row2 = mock.Mock()
        mock_row2.dimension_values = [mock.Mock(value="08"), mock.Mock(value="Canada")]
        mock_row2.metric_values = [mock.Mock(value="0"), mock.Mock(value="1"), mock.Mock(value="0.0")]
        
        mock_response.rows = [mock_row1, mock_row2]
        mock_data_client.run_report.return_value = mock_response

        report_data = channel_traffic_by_hour_report.run_report("123", mock_data_client, "2023-01-01", "2023-01-01")

        # --- Assertions ---
        self.assertEqual(report_data["channels"], ["Organic Search"])
        self.assertNotIn("Canada", report_data["channels"])
        
        # Check rows only contain Organic Search
        for row in report_data["rows"]:
            self.assertNotEqual(row[1], "Canada")
            self.assertEqual(row[1], "Organic Search")

if __name__ == '__main__':
    unittest.main()
