from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Lead Quality by Channel report.
    This report combines total traffic metrics with 'generate_lead' event counts
    to provide a view of lead generation performance across different channels.
    """
    
    # Request 1: Get total traffic metrics by channel
    traffic_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="engagementRate")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[{"dimension": {"dimension_name": "sessionDefaultChannelGroup"}, "desc": False}],
    )

    # Request 2: Get 'generate_lead' event counts by channel
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

    try:
        traffic_response = data_client.run_report(traffic_request)
        lead_response = data_client.run_report(lead_request)
    except Exception as e:
        print(f"Error running Lead Quality by Channel Report: {e}")
        return None

    # Process lead counts into a lookup dictionary
    lead_counts = {}
    if lead_response.rows:
        for row in lead_response.rows:
            channel = row.dimension_values[0].value
            count = int(row.metric_values[0].value)
            lead_counts[channel] = count

    # Standardized report data structure
    report_data = {
        "title": "Lead Quality by Channel Report",
        "headers": ["Channel", "Sessions", "Active Users", "Engagement Rate", "Leads", "Lead Conv. Rate"],
        "rows": [],
        "explanation": (
            "**Metric Definitions:**\n"
            "* **Sessions:** The number of sessions that began on your site or app.\n"
            "* **Active Users:** The number of distinct users who visited your site or app and had an engaged session.\n"
            "* **Engagement Rate:** The percentage of sessions that were engaged sessions.\n"
            "* **Leads:** The total count of 'generate_lead' events triggered by users.\n"
            "* **Lead Conv. Rate:** The number of 'generate_lead' events divided by the number of total Sessions."
        )
    }

    if not traffic_response.rows:
        return report_data

    for row in traffic_response.rows:
        channel = row.dimension_values[0].value
        sessions = int(row.metric_values[0].value)
        active_users = row.metric_values[1].value
        
        try:
            engagement_rate = f"{float(row.metric_values[2].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[2].value
            
        leads = lead_counts.get(channel, 0)
        
        # Calculate Lead Conversion Rate
        if sessions > 0:
            conv_rate = (leads / sessions) * 100
            conv_rate_str = f"{conv_rate:.2f}%"
        else:
            conv_rate_str = "0.00%"
            
        report_data["rows"].append([
            channel,
            str(sessions),
            active_users,
            engagement_rate,
            str(leads),
            conv_rate_str
        ])

    return report_data
