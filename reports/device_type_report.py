from google.analytics.data_v1beta.types import RunReportRequest

def run_report(property_id, data_client, start_date, end_date):
    """
    Generates a report on device types, including total users, engagement rate, and bounce rate.
    """
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[{"name": "deviceCategory"}],
        metrics=[
            {"name": "activeUsers"},
            {"name": "totalUsers"},
            {"name": "newUsers"},
            {"name": "engagedSessions"},
            {"name": "sessions"},
            {"name": "engagementRate"}
        ],
        date_ranges=[{"start_date": start_date, "end_date": end_date}],
    )
    response = data_client.run_report(request)

    headers = ["Device Category", "Active Users", "Total Users", "New Users", "Engaged Sessions", "Sessions", "Engagement Rate", "Bounce Rate"]
    rows = []
    for row in response.rows:
        engagement_rate = float(row.metric_values[5].value) if row.metric_values[5].value != 'null' else 0
        bounce_rate = 1 - engagement_rate
        rows.append([
            row.dimension_values[0].value,
            int(row.metric_values[0].value), # activeUsers
            int(row.metric_values[1].value), # totalUsers
            int(row.metric_values[2].value), # newUsers
            int(row.metric_values[3].value), # engagedSessions
            int(row.metric_values[4].value), # sessions
            f"{engagement_rate:.2%}",
            f"{bounce_rate:.2%}"
        ])

    explanation = """
    **Metrics Explanation:**
    *   **Active Users:** The number of distinct users who had an engaged session on your site or app. This is the primary user metric in GA4.
    *   **Total Users:** The total number of unique users who logged any event, regardless of whether the session was engaged.
    *   **New Users:** The number of unique users who interacted with your site or app for the first time.
    *   **Engaged Sessions:** The number of sessions that lasted longer than 10 seconds, had a conversion event, or had 2 or more page/screen views.
    *   **Sessions:** The total number of sessions initiated. A session is a period of time during which a user is actively engaged with your site or app.
    *   **Engagement Rate:** The percentage of sessions that were engaged sessions (Engaged Sessions / Sessions).
    *   **Bounce Rate:** The percentage of sessions that were not engaged (calculated as 1 - Engagement Rate).
    """

    return {
        "title": "Device Type Report",
        "headers": headers,
        "rows": rows,
        "explanation": explanation
    }
