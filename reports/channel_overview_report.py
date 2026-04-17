from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report to get channel data by new users and engaged sessions for a given date range.
    Returns the report data in a standardized format, sorted alphabetically by channel.
    """
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="newUsers"), Metric(name="engagedSessions")],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[{"dimension": {"dimension_name": "sessionDefaultChannelGroup"}, "desc": False}], # Alphabetical order
    )

    # Standardized report data structure
    report_data = {
        "title": "Channel Overview Report",
        "headers": ["Channel", "New Users", "Engaged Sessions"],
        "rows": [],
        "explanation": (
            "**Metric Definitions:**\n"
            "* **New Users:** The number of users who interacted with your site or launched your app for the first time.\n"
            "* **Engaged Sessions:** The number of sessions that lasted longer than 10 seconds, or had a conversion event, or had 2 or more screen or page views."
        )
    }

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Channel Overview Report: {e}")
        return report_data

    if not response.rows:
        return report_data # Return with empty rows

    for row in response.rows:
        channel = row.dimension_values[0].value
        new_users = row.metric_values[0].value
        engaged_sessions = row.metric_values[1].value
        report_data["rows"].append([channel, new_users, engaged_sessions])

    return report_data
