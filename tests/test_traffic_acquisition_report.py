import unittest
from unittest import mock
from reports import traffic_acquisition_report

class TestTrafficAcquisitionReport(unittest.TestCase):

    def test_run_report_with_totals_and_average(self):
        """
        Test that the run_report function correctly calculates totals for specified
        metrics and the average for the engagement rate.
        """
        mock_data_client = mock.Mock()
        mock_response = mock.Mock()

        # Mock headers
        mock_response.dimension_headers = [
            mock.Mock(name="sessionDefaultChannelGroup"),
            mock.Mock(name="sessionSourceMedium")
        ]
        
        header_names = ["totalUsers", "newUsers", "engagedSessions", "engagementRate", "conversions"]
        header_mocks = []
        for name in header_names:
            header = mock.Mock()
            header.name = name
            header_mocks.append(header)
        mock_response.metric_headers = header_mocks

        # Mock rows of data
        mock_row1 = mock.Mock()
        mock_row1.dimension_values = [mock.Mock(value="Organic Search"), mock.Mock(value="google / organic")]
        mock_row1.metric_values = [
            mock.Mock(value="1000"),  # totalUsers
            mock.Mock(value="800"),   # newUsers
            mock.Mock(value="600"),   # engagedSessions
            mock.Mock(value="0.6"),   # engagementRate
            mock.Mock(value="50")     # conversions
        ]

        mock_row2 = mock.Mock()
        mock_row2.dimension_values = [mock.Mock(value="Direct"), mock.Mock(value="(direct) / (none)")]
        mock_row2.metric_values = [
            mock.Mock(value="500"),
            mock.Mock(value="400"),
            mock.Mock(value="200"),
            mock.Mock(value="0.4"),
            mock.Mock(value="20")
        ]
        
        mock_response.rows = [mock_row1, mock_row2]
        mock_data_client.run_report.return_value = mock_response

        property_id = "12345"
        start_date = "2023-01-01"
        end_date = "2023-01-31"

        report_data = traffic_acquisition_report.run_report(property_id, mock_data_client, start_date, end_date)

        # --- Assertions ---
        self.assertIsNotNone(report_data)
        self.assertEqual(report_data["title"], "Traffic Acquisition Report")
        self.assertEqual(len(report_data["rows"]), 3) # 2 data rows + 1 total row

        # Check the Total row
        total_row = report_data["rows"][2]
        self.assertEqual(total_row[0], "Total")  # sessionDefaultChannelGroup is "Total"
        self.assertEqual(total_row[1], "")  # sessionSourceMedium is blank
        
        # Verify calculated totals
        self.assertEqual(total_row[2], "1500") # Total Users: 1000 + 500
        self.assertEqual(total_row[3], "1200") # New Users: 800 + 400
        self.assertEqual(total_row[4], "800")  # Engaged Sessions: 600 + 200
        
        # Verify average engagement rate
        # (0.6 + 0.4) / 2 = 0.5 --> 50.00%
        self.assertEqual(total_row[5], "50.00%")
        
        # Verify total conversions
        self.assertEqual(total_row[6], "70")   # Conversions: 50 + 20

    def test_run_report_no_rows(self):
        """
        Test that the report handles cases with no data rows gracefully.
        """
        mock_data_client = mock.Mock()
        mock_response = mock.Mock()
        mock_response.dimension_headers = []
        mock_response.metric_headers = []
        mock_response.rows = []
        mock_data_client.run_report.return_value = mock_response

        report_data = traffic_acquisition_report.run_report("123", mock_data_client, "2023-01-01", "2023-01-01")

        self.assertIsNotNone(report_data)
        self.assertEqual(len(report_data["rows"]), 0) # No data rows, so no total row

if __name__ == '__main__':
    unittest.main()
