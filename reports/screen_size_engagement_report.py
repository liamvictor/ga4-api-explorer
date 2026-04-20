from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Screen Size Engagement report.
    This report shows how different screen resolutions impact user engagement and bounce rate.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="screenResolution")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="engagementRate"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
        limit=25
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Screen Size Engagement Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "Top 25 Screen Resolutions by Engagement",
        "headers": [
            "Screen Resolution", 
            "Active Users", 
            "Sessions", 
            "Engagement Rate", 
            "Bounce Rate", 
            "Avg. Duration (s)"
        ],
        "rows": [],
        "explanation": (
            "This report helps identify if certain screen sizes have high bounce rates, "
            "which could indicate responsive design issues or content not fitting the screen correctly."
        )
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        resolution = row.dimension_values[0].value
        active_users = row.metric_values[0].value
        sessions = row.metric_values[1].value
        
        try:
            engagement_rate = f"{float(row.metric_values[2].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[2].value
            
        try:
            bounce_rate = f"{float(row.metric_values[3].value) * 100:.2f}%"
        except (ValueError, TypeError):
            bounce_rate = row.metric_values[3].value
            
        try:
            avg_duration = f"{float(row.metric_values[4].value):.2f}"
        except (ValueError, TypeError):
            avg_duration = row.metric_values[4].value

        report_data["rows"].append([
            resolution,
            active_users,
            sessions,
            engagement_rate,
            bounce_rate,
            avg_duration
        ])

    return report_data
