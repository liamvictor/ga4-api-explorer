import unittest
from unittest import mock
from reports import channel_traffic_by_hour_report

class TestChannelTrafficByHourReport(unittest.TestCase):

    def test_run_report_success(self):
        """
        Test that the run_report function correctly processes API response rows.
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

        # Mock rows of data
        # Row 1: Hour 08, Organic Search
        mock_row1 = mock.Mock()
        mock_row1.dimension_values = [mock.Mock(value="08"), mock.Mock(value="Organic Search")]
        mock_row1.metric_values = [
            mock.Mock(value="150"),  # sessions
            mock.Mock(value="120"),  # activeUsers
            mock.Mock(value="0.75")  # engagementRate
        ]

        # Row 2: Hour 08, Direct
        mock_row2 = mock.Mock()
        mock_row2.dimension_values = [mock.Mock(value="08"), mock.Mock(value="Direct")]
        mock_row2.metric_values = [
            mock.Mock(value="50"),
            mock.Mock(value="40"),
            mock.Mock(value="0.6")
        ]
        
        mock_response.rows = [mock_row1, mock_row2]
        mock_data_client.run_report.return_value = mock_response

        property_id = "12345"
        start_date = "2023-01-01"
        end_date = "2023-01-31"

        report_data = channel_traffic_by_hour_report.run_report(property_id, mock_data_client, start_date, end_date)

        # --- Assertions ---
        self.assertIsNotNone(report_data)
        self.assertEqual(report_data["title"], "Channel Traffic by Hour of Day")
        self.assertEqual(report_data["special_type"], "channel_traffic_by_hour")
        self.assertEqual(len(report_data["rows"]), 2)
        
        # Check first row data in table format
        self.assertEqual(report_data["rows"][0][0], "08")
        self.assertEqual(report_data["rows"][0][1], "Organic Search")
        self.assertEqual(report_data["rows"][0][2], "150")
        
        # Check matrix data for chart
        self.assertIn("08", report_data["json_data"])
        self.assertIn("Organic Search", report_data["json_data"]["08"])
        self.assertEqual(report_data["json_data"]["08"]["Organic Search"]["sessions"], 150)
        
        # Check hours and channels
        self.assertEqual(len(report_data["hours"]), 24)
        self.assertIn("08", report_data["hours"])
        self.assertEqual(report_data["channels"], ["Direct", "Organic Search"])

    def test_run_report_no_rows(self):
        """
        Test that the report handles cases with no data rows gracefully.
        """
        mock_data_client = mock.Mock()
        mock_response = mock.Mock()
        mock_response.rows = []
        mock_data_client.run_report.return_value = mock_response

        report_data = channel_traffic_by_hour_report.run_report("123", mock_data_client, "2023-01-01", "2023-01-01")

        self.assertIsNotNone(report_data)
        self.assertEqual(len(report_data["rows"]), 0)
        self.assertEqual(len(report_data["hours"]), 24)

if __name__ == '__main__':
    unittest.main()
