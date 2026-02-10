import unittest
from unittest import mock
from reports import channel_overview_report

class TestChannelOverviewReport(unittest.TestCase):

    def test_run_report_with_totals(self):
        """
        Test that the run_report function correctly calculates and appends totals
        for New Users and Engaged Sessions.
        """
        mock_data_client = mock.Mock()
        
        # Mock the response from the Google Analytics Data API
        # This structure mimics the actual response object
        mock_response = mock.Mock()
        
        # First row: Channel A, 100 new users, 50 engaged sessions
        mock_row1 = mock.Mock()
        mock_row1.dimension_values = [mock.Mock(value="Channel A")]
        mock_row1.metric_values = [mock.Mock(value="100"), mock.Mock(value="50")]

        # Second row: Channel B, 200 new users, 150 engaged sessions
        mock_row2 = mock.Mock()
        mock_row2.dimension_values = [mock.Mock(value="Channel B")]
        mock_row2.metric_values = [mock.Mock(value="200"), mock.Mock(value="150")]

        # Third row: Channel C, 50 new users, 25 engaged sessions
        mock_row3 = mock.Mock()
        mock_row3.dimension_values = [mock.Mock(value="Channel C")]
        mock_row3.metric_values = [mock.Mock(value="50"), mock.Mock(value="25")]
        
        mock_response.rows = [mock_row1, mock_row2, mock_row3]
        mock_data_client.run_report.return_value = mock_response

        property_id = "12345"
        start_date = "2023-01-01"
        end_date = "2023-01-07"

        report_data = channel_overview_report.run_report(property_id, mock_data_client, start_date, end_date)

        self.assertIsNotNone(report_data)
        self.assertEqual(report_data["title"], "Channel Overview Report")
        self.assertEqual(report_data["headers"], ["Channel", "New Users", "Engaged Sessions"])
        
        # Check that there are 4 rows (3 data rows + 1 total row)
        self.assertEqual(len(report_data["rows"]), 4)

        # Verify the data rows
        self.assertEqual(report_data["rows"][0], ["Channel A", 100, 50])
        self.assertEqual(report_data["rows"][1], ["Channel B", 200, 150])
        self.assertEqual(report_data["rows"][2], ["Channel C", 50, 25])

        # Verify the total row
        total_row = report_data["rows"][3]
        self.assertEqual(total_row[0], "Total")
        self.assertEqual(total_row[1], 350)  # 100 + 200 + 50
        self.assertEqual(total_row[2], 225)  # 50 + 150 + 25

    def test_run_report_no_rows(self):
        """
        Test that the run_report function handles cases with no data rows gracefully.
        """
        mock_data_client = mock.Mock()
        mock_response = mock.Mock()
        mock_response.rows = []
        mock_data_client.run_report.return_value = mock_response

        property_id = "12345"
        start_date = "2023-01-01"
        end_date = "2023-01-07"

        report_data = channel_overview_report.run_report(property_id, mock_data_client, start_date, end_date)

        self.assertIsNotNone(report_data)
        self.assertEqual(report_data["title"], "Channel Overview Report")
        self.assertEqual(report_data["headers"], ["Channel", "New Users", "Engaged Sessions"])
        self.assertEqual(len(report_data["rows"]), 0) # No data rows, so no total row either

    def test_run_report_with_none_values(self):
        """
        Test that the run_report function handles cases where metric values might be None or empty strings.
        This test assumes that the GA4 API returns string values for metrics.
        """
        mock_data_client = mock.Mock()
        mock_response = mock.Mock()
        
        mock_row1 = mock.Mock()
        mock_row1.dimension_values = [mock.Mock(value="Channel X")]
        mock_row1.metric_values = [mock.Mock(value="10"), mock.Mock(value="5")]

        mock_row2 = mock.Mock()
        mock_row2.dimension_values = [mock.Mock(value="Channel Y")]
        mock_row2.metric_values = [mock.Mock(value="0"), mock.Mock(value="0")] # Zero values

        mock_row3 = mock.Mock()
        mock_row3.dimension_values = [mock.Mock(value="Channel Z")]
        mock_row3.metric_values = [mock.Mock(value="5"), mock.Mock(value="2")]
        
        mock_response.rows = [mock_row1, mock_row2, mock_row3]
        mock_data_client.run_report.return_value = mock_response

        property_id = "12345"
        start_date = "2023-01-01"
        end_date = "2023-01-07"

        report_data = channel_overview_report.run_report(property_id, mock_data_client, start_date, end_date)

        self.assertIsNotNone(report_data)
        self.assertEqual(len(report_data["rows"]), 4)

        total_row = report_data["rows"][3]
        self.assertEqual(total_row[0], "Total")
        self.assertEqual(total_row[1], 15)  # 10 + 0 + 5
        self.assertEqual(total_row[2], 7)   # 5 + 0 + 2

if __name__ == '__main__':
    unittest.main()
