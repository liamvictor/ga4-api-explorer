from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a New vs. Returning by Channel report.
    This report breaks down new and returning user engagement by acquisition channel.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="sessionDefaultChannelGroup"),
            Dimension(name="newVsReturning")
        ],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="engagementRate"),
            Metric(name="averageSessionDuration")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="sessionDefaultChannelGroup")),
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="newVsReturning"))
        ]
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running New vs. Returning by Channel Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "New vs. Returning by Channel",
        "headers": [
            "Channel", 
            "User Type", 
            "Active Users", 
            "Sessions", 
            "Engagement Rate", 
            "Avg. Session Duration (s)"
        ],
        "rows": [],
        "explanation": (
            "This report shows how different channels perform in bringing back users versus acquiring new ones. "
            "High 'Returning' engagement in a channel like 'Email' or 'Direct' is expected, while 'Paid Search' "
            "often focuses on 'New' users."
        )
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        channel = row.dimension_values[0].value
        user_type = row.dimension_values[1].value.title()
        active_users = row.metric_values[0].value
        sessions = row.metric_values[1].value
        
        try:
            engagement_rate = f"{float(row.metric_values[2].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[2].value
            
        try:
            avg_duration = f"{float(row.metric_values[3].value):.2f}"
        except (ValueError, TypeError):
            avg_duration = row.metric_values[3].value

        report_data["rows"].append([
            channel,
            user_type,
            active_users,
            sessions,
            engagement_rate,
            avg_duration
        ])

    return report_data
