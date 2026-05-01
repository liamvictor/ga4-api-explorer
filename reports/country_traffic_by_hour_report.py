from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report showing traffic by the top 8 countries and an 'All Others' category, by hour of the day.
    """
    
    # Define dimensions: Hour and Country
    dimensions = [
        Dimension(name="hour"),
        Dimension(name="country"),
    ]
    
    # Define metrics: Sessions, Active Users, Engagement Rate
    metrics = [
        Metric(name="sessions"),
        Metric(name="activeUsers"),
        Metric(name="engagementRate"),
    ]
    
    # Order by Hour (ascending)
    order_bys = [
        OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="hour"), desc=False),
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
        print(f"Error running Top 8 Countries Traffic by Hour report: {e}")
        return {
            "title": "Top 8 Countries Traffic by Hour",
            "headers": ["Hour", "Country", "Sessions", "Active Users", "Engagement Rate"],
            "rows": [],
            "explanation": f"Error: {e}"
        }

    report_headers = ["Hour", "Country", "Sessions", "Active Users", "Engagement Rate"]
    
    # First pass: Aggregate totals to identify Top 8 countries
    country_totals = {}
    temp_data = [] # Store raw row data temporarily
    
    if response.rows:
        for row in response.rows:
            hour = row.dimension_values[0].value
            country = row.dimension_values[1].value
            sessions = int(row.metric_values[0].value)
            active_users = int(row.metric_values[1].value)
            
            try:
                engagement_rate_val = float(row.metric_values[2].value)
            except (ValueError, TypeError):
                engagement_rate_val = 0.0
            
            country_totals[country] = country_totals.get(country, 0) + sessions
            temp_data.append({
                "hour": hour,
                "country": country,
                "sessions": sessions,
                "users": active_users,
                "engagement_val": engagement_rate_val
            })

    # Identify Top 8 countries
    sorted_countries = sorted(country_totals.items(), key=lambda item: item[1], reverse=True)
    top_8_names = [c for c, total in sorted_countries[:8] if total > 0]
    has_others = len(sorted_countries) > 8

    # Second pass: Re-aggregate into Top 8 + All Others
    data_matrix = {}
    all_hours_padded = [f"{i:02d}" for i in range(24)]
    
    # Initialize matrix with padded hours
    for h in all_hours_padded:
        data_matrix[h] = {name: {"sessions": 0, "users": 0, "eng_sum": 0, "count": 0} for name in top_8_names}
        if has_others:
            data_matrix[h]["All Others"] = {"sessions": 0, "users": 0, "eng_sum": 0, "count": 0}

    for item in temp_data:
        # API hour might be unpadded (e.g., "0"), convert to padded (e.g., "00")
        hour_padded = f"{int(item['hour']):02d}"
        country = item["country"]
        target = country if country in top_8_names else "All Others"
        
        if target in data_matrix[hour_padded]:
            data_matrix[hour_padded][target]["sessions"] += item["sessions"]
            data_matrix[hour_padded][target]["users"] += item["users"]
            data_matrix[hour_padded][target]["eng_sum"] += item["engagement_val"]
            data_matrix[hour_padded][target]["count"] += 1

    # Format data for report_rows
    report_rows = []
    final_channels = top_8_names + (["All Others"] if has_others else [])
    
    for h in all_hours_padded:
        for ch in final_channels:
            d = data_matrix[h][ch]
            avg_eng_str = f"{(d['eng_sum'] / d['count']) * 100:.2f}%" if d["count"] > 0 else "0.00%"
            
            # Template expects 'engagement' key
            d["engagement"] = avg_eng_str
            
            if d["sessions"] > 0 or d["users"] > 0:
                report_rows.append([h, ch, str(d["sessions"]), str(d["users"]), avg_eng_str])

    return {
        "title": "Top 8 Countries Traffic by Hour",
        "special_type": "channel_traffic_by_hour",
        "category_label": "Country",
        "time_label": "Hour",
        "headers": report_headers,
        "rows": report_rows,
        "json_data": data_matrix,
        "hours": all_hours_padded,
        "channels": final_channels,
        "explanation": (
            "This report shows traffic distribution by hour for the Top 8 countries, with all other countries aggregated into 'All Others'.\n\n"
            "**Hour:** The hour of the day in the property's timezone.\n"
            "**Country:** The country of the user (Top 8 or 'All Others').\n"
            "**Sessions:** Total sessions for that country/group in that hour.\n"
            "**Active Users:** Distinct engaged users in that hour."
        )
    }
