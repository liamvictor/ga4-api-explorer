from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report showing channel traffic by hour of the day.
    Returns data structured for both standard table output and a specialized HTML chart.
    """
    
    # Define dimensions: Hour and Channel
    dimensions = [
        Dimension(name="hour"),
        Dimension(name="sessionDefaultChannelGroup"),
    ]
    
    # Define metrics: Sessions, Active Users, Engagement Rate
    metrics = [
        Metric(name="sessions"),
        Metric(name="activeUsers"),
        Metric(name="engagementRate"),
    ]
    
    # Order by Hour (ascending) and then Sessions (descending)
    order_bys = [
        OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"), desc=False),
        OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True),
    ]

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=dimensions,
        metrics=metrics,
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=order_bys,
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Channel Traffic by Hour report: {e}")
        return {
            "title": "Channel Traffic by Hour of Day",
            "headers": ["Hour", "Channel", "Sessions", "Active Users", "Engagement Rate"],
            "rows": [],
            "explanation": f"Error: {e}"
        }

    report_headers = ["Hour", "Channel", "Sessions", "Active Users", "Engagement Rate"]
    report_rows = []
    
    # Matrix structure for the chart: data[hour][channel] = { sessions, users, engagement }
    data_matrix = {}
    channel_totals = {}
    all_hours = [f"{i:02d}" for i in range(24)]

    if response.rows:
        for row in response.rows:
            hour = row.dimension_values[0].value
            channel = row.dimension_values[1].value
            sessions = int(row.metric_values[0].value)
            active_users = int(row.metric_values[1].value)
            
            # Only process rows with actual traffic
            if sessions == 0 and active_users == 0:
                continue
                
            try:
                engagement_rate_val = float(row.metric_values[2].value)
                engagement_rate_str = f"{engagement_rate_val * 100:.2f}%"
            except (ValueError, TypeError):
                engagement_rate_str = row.metric_values[2].value
            
            # Update totals for filtering
            channel_totals[channel] = channel_totals.get(channel, 0) + sessions

            if hour not in data_matrix:
                data_matrix[hour] = {}
            data_matrix[hour][channel] = {
                "sessions": sessions,
                "users": active_users,
                "engagement": engagement_rate_str
            }

    # Filter out channels with zero total sessions
    filtered_channels = [ch for ch, total in channel_totals.items() if total > 0]
    
    # Build final report rows only for filtered channels
    for hour in sorted(data_matrix.keys()):
        for channel in sorted(data_matrix[hour].keys()):
            if channel in filtered_channels:
                item = data_matrix[hour][channel]
                report_rows.append([
                    hour,
                    channel,
                    str(item["sessions"]),
                    str(item["users"]),
                    item["engagement"]
                ])

    return {
        "title": "Channel Traffic by Hour of Day",
        "special_type": "channel_traffic_by_hour",
        "category_label": "Channel",
        "time_label": "Hour",
        "headers": report_headers,
        "rows": report_rows,
        "json_data": data_matrix,
        "hours": all_hours,
        "channels": sorted(filtered_channels),
        "explanation": (
            "This report shows how traffic from different channels is distributed across the hours of the day (00-23).\n\n"
            "**Hour:** The hour of the day in the property's timezone.\n"
            "**Channel:** The Session Default Channel Group.\n"
            "**Sessions:** The number of sessions that began in that hour.\n"
            "**Active Users:** The number of distinct users who had an engaged session in that hour.\n"
            "**Engagement Rate:** The percentage of sessions that were engaged sessions."
        )
    }
