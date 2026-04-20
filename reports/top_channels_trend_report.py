from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Top Channels Trend report.
    Fetches multi-month data for all channels to allow dynamic 'Top 5' ranking in HTML.
    """
    
    # Request 1: Monthly metrics by channel
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="sessionDefaultChannelGroup"),
            Dimension(name="yearMonth")
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="activeUsers")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="yearMonth"))]
    )

    # Request 2: Monthly leads (generate_lead event)
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
        response = data_client.run_report(request)
        lead_response = data_client.run_report(lead_request)
    except Exception as e:
        print(f"Error running Top Channels Trend Report: {e}")
        return None

    # Nested structure for JS: data[channel][month] = { metrics }
    data_matrix = {}
    all_months = set()
    all_channels = set()

    for row in response.rows:
        channel = row.dimension_values[0].value
        ym = row.dimension_values[1].value
        month_str = f"{ym[:4]}-{ym[4:]}"
        
        all_months.add(month_str)
        all_channels.add(channel)
        
        if channel not in data_matrix: data_matrix[channel] = {}
        data_matrix[channel][month_str] = {
            "sessions": int(row.metric_values[0].value),
            "engaged": int(row.metric_values[1].value),
            "users": int(row.metric_values[2].value),
            "leads": 0
        }

    for row in lead_response.rows:
        channel = row.dimension_values[0].value
        ym = row.dimension_values[1].value
        month_str = f"{ym[:4]}-{ym[4:]}"
        if channel in data_matrix and month_str in data_matrix[channel]:
            data_matrix[channel][month_str]["leads"] = int(row.metric_values[0].value)

    return {
        "title": "Top 5 Channels Comparison",
        "special_type": "top_channels_trend",
        "json_data": data_matrix,
        "months": sorted(list(all_months)),
        "channels": sorted(list(all_channels)),
        "headers": ["Channel", "Month", "Sessions"], # Fallback
        "rows": [] # Fallback
    }
