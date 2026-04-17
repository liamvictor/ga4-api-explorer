from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a New vs. Returning Engagement report.
    This report compares metrics for new and returning users to determine
    if the property is building a loyal audience or seeing 'one and done' visitors.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="newVsReturning")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate"),
            Metric(name="averageSessionDuration"),
            Metric(name="sessionsPerUser")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running New vs. Returning Engagement Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "New vs. Returning Engagement Report",
        "headers": [
            "User Type", 
            "Active Users", 
            "Sessions", 
            "Engaged Sessions", 
            "Engagement Rate", 
            "Avg. Session Duration (s)", 
            "Sessions per User"
        ],
        "rows": [],
        "explanation": (
            "**Key Insights:**\n"
            "* **New Users:** High volume here indicates successful acquisition but potentially 'one and done' behavior if engagement is low.\n"
            "* **Returning Users:** High engagement and sessions per user here indicate a successful 'audience building' strategy.\n"
            "* **Engagement Rate:** Compare this between types to see who finds your content more valuable."
        )
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        user_type = row.dimension_values[0].value.title() # e.g., 'new' -> 'New'
        active_users = row.metric_values[0].value
        sessions = row.metric_values[1].value
        engaged_sessions = row.metric_values[2].value
        
        try:
            engagement_rate = f"{float(row.metric_values[3].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[3].value
            
        try:
            # averageSessionDuration is usually in seconds
            avg_duration = f"{float(row.metric_values[4].value):.2f}"
        except (ValueError, TypeError):
            avg_duration = row.metric_values[4].value
            
        try:
            sessions_per_user = f"{float(row.metric_values[5].value):.2f}"
        except (ValueError, TypeError):
            sessions_per_user = row.metric_values[5].value

        report_data["rows"].append([
            user_type,
            active_users,
            sessions,
            engaged_sessions,
            engagement_rate,
            avg_duration,
            sessions_per_user
        ])

    return report_data
