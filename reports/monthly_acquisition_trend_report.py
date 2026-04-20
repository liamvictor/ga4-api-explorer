from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy
from datetime import datetime
from dateutil.relativedelta import relativedelta

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Monthly Acquisition Trend report.
    This report breaks down traffic by month to show long-term growth trends.
    """
    
    # Ensure we use month as a dimension
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="yearMonth")],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
            Metric(name="conversions"),
            Metric(name="engagementRate")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="yearMonth"))]
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Monthly Acquisition Trend Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "Monthly Acquisition Trend",
        "headers": [
            "Month", 
            "Total Users", 
            "New Users", 
            "Sessions", 
            "Conversions", 
            "Engagement Rate"
        ],
        "rows": [],
        "explanation": "This report shows key acquisition and engagement metrics month-by-month to help identify seasonal trends and long-term growth."
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        # yearMonth is in YYYYMM format
        year_month = row.dimension_values[0].value
        formatted_month = f"{year_month[:4]}-{year_month[4:]}"
        
        total_users = row.metric_values[0].value
        new_users = row.metric_values[1].value
        sessions = row.metric_values[2].value
        conversions = row.metric_values[3].value
        
        try:
            engagement_rate = f"{float(row.metric_values[4].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[4].value

        report_data["rows"].append([
            formatted_month,
            total_users,
            new_users,
            sessions,
            conversions,
            engagement_rate
        ])

    return report_data
