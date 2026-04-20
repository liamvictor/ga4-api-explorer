from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report to get the top 25 landing pages by sessions for a given date range.
    Includes key metrics like Sessions, Active Users, New Users, and Engagement Rate.
    """
    
    # Define the request with landingPage dimension and relevant metrics.
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="landingPage")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="engagementRate")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=25,
        order_bys=[
            OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="sessions"),
                desc=True
            )
        ],
    )

    try:
        # Execute the report query via the data client.
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Landing Pages report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "Top 25 Landing Pages",
        "headers": ["Landing Page", "Sessions", "Active Users", "New Users", "Engagement Rate"],
        "rows": []
    }

    # If no rows are returned, return the empty report structure.
    if not response.rows:
        return report_data

    # Iterate through the response rows and format the data.
    for row in response.rows:
        landing_page = row.dimension_values[0].value
        sessions = row.metric_values[0].value
        active_users = row.metric_values[1].value
        new_users = row.metric_values[2].value
        
        # Engagement rate is a decimal (e.g., 0.65), format it as a percentage.
        try:
            engagement_rate = f"{float(row.metric_values[3].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[3].value
            
        # Append the formatted row to the report data.
        report_data["rows"].append([
            landing_page, 
            sessions, 
            active_users, 
            new_users, 
            engagement_rate
        ])

    return report_data
