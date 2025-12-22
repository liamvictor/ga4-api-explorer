# reports/low_exit_rate_pages_report.py

from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, OrderBy, Filter, FilterExpression, DateRange, NumericValue
import statistics

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report to identify pages with a high engagement rate among pages with at least average traffic.
    These are top-performing, 'sticky' pages.
    """
    
    # 1. First API Call: Get data for all pages to calculate average views and create a views lookup map.
    try:
        all_pages_request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            limit=100000
        )
        all_pages_response = data_client.run_report(all_pages_request)
    except Exception as e:
        print(f"Error fetching all pages data for averaging: {e}")
        return None

    if not all_pages_response.rows:
        return {
            "title": "High Engagement Pages",
            "headers": ["Status"],
            "rows": [["No page data found to calculate averages."]]
        }

    # Create a lookup map for page views and a list for averaging
    page_views_map = {row.dimension_values[0].value: int(row.metric_values[0].value) for row in all_pages_response.rows}
    page_views_list = list(page_views_map.values())
    average_views = statistics.mean(page_views_list) if page_views_list else 0

    # 2. Second API Call: Get engagement rate for pages with above-average traffic.
    # We cannot include a metric in the 'metrics' list if it's also used in a filter.
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="engagementRate")], # Remove screenPageViews from here
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="screenPageViews",
                    numeric_filter=Filter.NumericFilter(
                        operation=Filter.NumericFilter.Operation.GREATER_THAN_OR_EQUAL,
                        value=NumericValue(int64_value=int(average_views))
                    )
                )
            ),
            limit=10000
        )
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running High Engagement Pages report: {e}")
        return None

    # Process the response and format it into the standardized dictionary.
    report_headers = ["Page Path", "Screen Page Views", "Engagement Rate"]
    
    report_rows = []
    for row in response.rows:
        page_path = row.dimension_values[0].value
        # Look up the screenPageViews from the map created in the first call
        views = page_views_map.get(page_path, 0)
        engagement_rate = float(row.metric_values[0].value) * 100
        
        report_rows.append([page_path, f"{views:,}", f"{engagement_rate:.2f}%"])

    # Sort the results by engagement rate in descending order to show the best pages first
    report_rows.sort(key=lambda x: float(x[2].strip('%')), reverse=True)

    report_data = {
        "title": "High Engagement Pages (Above Average Traffic)",
        "headers": report_headers,
        "rows": report_rows,
    }

    return report_data
