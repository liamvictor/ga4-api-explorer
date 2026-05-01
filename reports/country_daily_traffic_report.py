from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report showing daily traffic for the Top 8 countries and an 'All Others' category.
    Based on the Top 8 Countries Traffic by Hour report structure.
    """
    
    # Define dimensions: Date and Country
    dimensions = [
        Dimension(name="date"),
        Dimension(name="country"),
    ]
    
    # Define metrics: Sessions, Active Users, Engagement Rate
    metrics = [
        Metric(name="sessions"),
        Metric(name="activeUsers"),
        Metric(name="engagementRate"),
    ]
    
    # Order by Date (ascending)
    order_bys = [
        OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"), desc=False),
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
        print(f"Error running Top 8 Countries Traffic by Day report: {e}")
        return {
            "title": "Top 8 Countries Traffic by Day",
            "headers": ["Date", "Country", "Sessions", "Active Users", "Engagement Rate"],
            "rows": [],
            "explanation": f"Error: {e}"
        }

    report_headers = ["Date", "Country", "Sessions", "Active Users", "Engagement Rate"]
    
    # First pass: Aggregate totals to identify Top 8 countries
    country_totals = {}
    temp_data = [] # Store raw row data temporarily
    all_dates = set()
    
    if response.rows:
        for row in response.rows:
            # Format date YYYYMMDD to YYYY-MM-DD
            raw_date = row.dimension_values[0].value
            date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            country = row.dimension_values[1].value
            sessions = int(row.metric_values[0].value)
            active_users = int(row.metric_values[1].value)
            
            try:
                engagement_rate_val = float(row.metric_values[2].value)
            except (ValueError, TypeError):
                engagement_rate_val = 0.0
            
            country_totals[country] = country_totals.get(country, 0) + sessions
            all_dates.add(date)
            temp_data.append({
                "date": date,
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
    sorted_all_dates = sorted(list(all_dates))
    
    # Initialize matrix
    for d in sorted_all_dates:
        data_matrix[d] = {name: {"sessions": 0, "users": 0, "eng_sum": 0, "count": 0} for name in top_8_names}
        if has_others:
            data_matrix[d]["All Others"] = {"sessions": 0, "users": 0, "eng_sum": 0, "count": 0}

    for item in temp_data:
        date = item["date"]
        country = item["country"]
        target = country if country in top_8_names else "All Others"
        
        if target in data_matrix[date]:
            m = data_matrix[date][target]
            m["sessions"] += item["sessions"]
            m["users"] += item["users"]
            m["eng_sum"] += item["engagement_val"]
            m["count"] += 1

    # Format data for report_rows
    report_rows = []
    final_channels = top_8_names + (["All Others"] if has_others else [])
    
    for d_str in sorted_all_dates:
        for ch in final_channels:
            m = data_matrix[d_str][ch]
            avg_eng_str = f"{(m['eng_sum'] / m['count']) * 100:.2f}%" if m["count"] > 0 else "0.00%"
            m["engagement"] = avg_eng_str # Template expects this
            
            if m["sessions"] > 0 or m["users"] > 0:
                report_rows.append([d_str, ch, str(m["sessions"]), str(m["users"]), avg_eng_str])

    return {
        "title": "Top 8 Countries Traffic by Day",
        "special_type": "channel_traffic_by_hour", # Use the same template logic
        "category_label": "Country",
        "time_label": "Date",
        "headers": report_headers,
        "rows": report_rows,
        "json_data": data_matrix,
        "hours": sorted_all_dates, # Re-use hours key for simplicity in template
        "channels": final_channels,
        "explanation": (
            "This report shows traffic distribution by day for the Top 8 countries, with all other countries aggregated into 'All Others'.\n\n"
            "**Date:** The date of the traffic.\n"
            "**Country:** The country of the user (Top 8 or 'All Others').\n"
            "**Sessions:** Total sessions for that country/group on that day.\n"
            "**Active Users:** Distinct engaged users on that day."
        )
    }
