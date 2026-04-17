from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs an expanded Channel Overview report including traffic, engagement, and lead data.
    """
    
    # Request 1: Traffic and Engagement
    traffic_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[{"dimension": {"dimension_name": "sessionDefaultChannelGroup"}, "desc": False}],
    )

    # Request 2: Leads (generate_lead event)
    lead_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[Metric(name="eventCount")],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(value="generate_lead")
            )
        ),
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    # Standardized report data structure
    report_data = {
        "title": "Channel Overview Report",
        "headers": ["Channel", "Sessions", "Active Users", "New Users", "Engaged Sessions", "Engagement Rate", "Leads"],
        "rows": [],
        "explanation": (
            "**Metric Definitions:**\n"
            "* **Sessions:** The number of sessions that began on your site or app.\n"
            "* **Active Users:** The number of distinct users who visited your site or app and had an engaged session.\n"
            "* **New Users:** The number of users who interacted with your site for the first time.\n"
            "* **Engaged Sessions:** Sessions lasting >10s, or with a conversion, or with 2+ page views.\n"
            "* **Engagement Rate:** The percentage of sessions that were engaged sessions.\n"
            "* **Leads:** The total count of 'generate_lead' events."
        )
    }

    try:
        traffic_response = data_client.run_report(traffic_request)
        lead_response = data_client.run_report(lead_request)
    except Exception as e:
        print(f"Error running Channel Overview Report: {e}")
        return report_data

    # Process lead counts
    lead_counts = {}
    if lead_response.rows:
        for row in lead_response.rows:
            channel = row.dimension_values[0].value
            lead_counts[channel] = row.metric_values[0].value

    if not traffic_response.rows:
        return report_data

    for row in traffic_response.rows:
        channel = row.dimension_values[0].value
        sessions = row.metric_values[0].value
        active_users = row.metric_values[1].value
        new_users = row.metric_values[2].value
        engaged_sessions = row.metric_values[3].value
        
        try:
            engagement_rate = f"{float(row.metric_values[4].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[4].value
            
        leads = lead_counts.get(channel, "0")
            
        report_data["rows"].append([
            channel,
            sessions,
            active_users,
            new_users,
            engaged_sessions,
            engagement_rate,
            leads
        ])

    return report_data
