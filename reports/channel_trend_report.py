from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter, OrderBy
import json

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a complex Channel Trend report using yearMonth for longitudinal tracking.
    This report is designed for a specialized interactive HTML output.
    """
    
    # Request 1: Monthly Traffic and Engagement by Channel
    traffic_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="sessionDefaultChannelGroup"),
            Dimension(name="yearMonth")
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate"),
            Metric(name="activeUsers")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="yearMonth")),
            OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="sessionDefaultChannelGroup"))
        ]
    )

    # Request 2: Monthly Leads by Channel
    lead_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="sessionDefaultChannelGroup"),
            Dimension(name="yearMonth")
        ],
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
        print(f"Error running Channel Trend Report: {e}")
        return None

    # Nested structure: data[channel][month] = { metrics }
    data_matrix = {}
    all_months = set()
    all_channels = set()

    # Process traffic
    for row in traffic_response.rows:
        channel = row.dimension_values[0].value
        ym = row.dimension_values[1].value
        month_str = f"{ym[:4]}-{ym[4:]}"
        
        all_months.add(month_str)
        all_channels.add(channel)
        
        if channel not in data_matrix: data_matrix[channel] = {}
        
        try:
            rate = f"{float(row.metric_values[2].value) * 100:.2f}%"
        except:
            rate = row.metric_values[2].value

        data_matrix[channel][month_str] = {
            "sessions": row.metric_values[0].value,
            "engaged": row.metric_values[1].value,
            "rate": rate,
            "users": row.metric_values[3].value,
            "leads": "0" # Default
        }

    # Process leads
    for row in lead_response.rows:
        channel = row.dimension_values[0].value
        ym = row.dimension_values[1].value
        month_str = f"{ym[:4]}-{ym[4:]}"
        
        if channel in data_matrix and month_str in data_matrix[channel]:
            data_matrix[channel][month_str]["leads"] = row.metric_values[0].value

    sorted_months = sorted(list(all_months))
    sorted_channels = sorted(list(all_channels))

    # We return a specialized structure for this report
    report_data = {
        "title": "Channel Performance Trends",
        "special_type": "channel_trend",
        "json_data": data_matrix,
        "months": sorted_months,
        "channels": sorted_channels,
        "headers": ["Channel", "Month", "Sessions", "Leads"], # For CSV fallback
        "rows": [] # For CSV fallback
    }

    # Fill rows for CSV fallback
    for channel in sorted_channels:
        for month in sorted_months:
            m_data = data_matrix[channel].get(month, {"sessions": "0", "leads": "0"})
            report_data["rows"].append([channel, month, m_data.get("sessions"), m_data.get("leads")])

    return report_data
