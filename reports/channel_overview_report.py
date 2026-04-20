from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs an expanded Channel Overview report including traffic, engagement, and lead data.
    Metrics are ordered: Sessions, Engaged Sessions, Engagement Rate, Active Users, New Users, Leads.
    """
    
    # Request 1: Traffic and Engagement
    traffic_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate"),
            Metric(name="activeUsers"),
            Metric(name="newUsers")
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
        "headers": ["Channel", "Sessions", "Engaged Sessions", "Engagement Rate", "Active Users", "New Users", "Leads"],
        "rows": [],
        "explanation": (
            "**Metric Definitions:**\n"
            "* **Sessions:** The number of sessions that began on your site or app.\n"
            "* **Engaged Sessions:** Sessions lasting >10s, or with a conversion, or with 2+ page views.\n"
            "* **Engagement Rate:** The percentage of sessions that were engaged sessions.\n"
            "* **Active Users:** The number of distinct users who visited your site or app and had an engaged session.\n"
            "* **New Users:** The number of users who interacted with your site for the first time.\n"
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

    total_sessions = 0
    total_engaged_sessions = 0
    total_active_users = 0
    total_new_users = 0
    total_leads = 0

    for row in traffic_response.rows:
        channel = row.dimension_values[0].value
        sessions = int(row.metric_values[0].value)
        engaged_sessions = int(row.metric_values[1].value)
        
        try:
            engagement_rate = f"{float(row.metric_values[2].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[2].value
            
        active_users = int(row.metric_values[3].value)
        new_users = int(row.metric_values[4].value)
        leads = int(lead_counts.get(channel, "0"))
            
        report_data["rows"].append([
            channel,
            sessions,
            engaged_sessions,
            engagement_rate,
            active_users,
            new_users,
            leads
        ])

        total_sessions += sessions
        total_engaged_sessions += engaged_sessions
        total_active_users += active_users
        total_new_users += new_users
        total_leads += leads

    # Add total row
    total_engagement_rate = f"{(total_engaged_sessions / total_sessions * 100):.2f}%" if total_sessions > 0 else "0.00%"
    report_data["rows"].append([
        "Total",
        total_sessions,
        total_engaged_sessions,
        total_engagement_rate,
        total_active_users,
        total_new_users,
        total_leads
    ])

    return report_data
