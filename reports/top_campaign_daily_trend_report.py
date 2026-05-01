from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy, FilterExpression, Filter
import re

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report that isolates the top 10 numeric Campaign IDs and provides a daily breakdown.
    Also separates 'google / cpc' and baseline sources (Direct, Organic, Referral).
    """
    
    # 1. First, identify the Top 10 Numeric Campaign IDs
    top_campaigns_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionCampaignName")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=500 # Look at a broad set to find numeric IDs
    )

    try:
        campaign_response = data_client.run_report(top_campaigns_request)
    except Exception as e:
        print(f"Error identifying top campaigns: {e}")
        return None

    top_ids = []
    for row in campaign_response.rows:
        campaign_name = row.dimension_values[0].value
        # Check if the campaign name is primarily numeric (the "IDs")
        if re.match(r'^\d+$', campaign_name):
            top_ids.append(campaign_name)
            if len(top_ids) >= 10:
                break

    # 2. Query Daily Data for Top IDs, Google CPC, and Baselines
    # We include sessionSourceMedium to isolate 'google / cpc'
    daily_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="date"),
            Dimension(name="sessionCampaignName"),
            Dimension(name="sessionSourceMedium"),
            Dimension(name="sessionDefaultChannelGroup")
        ],
        metrics=[
            Metric(name="sessions"),
            Metric(name="conversions"),
            Metric(name="engagementRate"),
            Metric(name="activeUsers")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name="date"))]
    )

    try:
        daily_response = data_client.run_report(daily_request)
    except Exception as e:
        print(f"Error running daily campaign trend: {e}")
        return None

    final_rows = []
    
    # Process rows into categories
    for row in daily_response.rows:
        raw_date = row.dimension_values[0].value
        formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
        
        campaign = row.dimension_values[1].value
        source_medium = row.dimension_values[2].value
        channel = row.dimension_values[3].value
        
        sessions = int(row.metric_values[0].value)
        conversions = float(row.metric_values[1].value)
        eng_rate = f"{float(row.metric_values[2].value) * 100:.2f}%"
        active_users = int(row.metric_values[3].value)

        category = "Other"
        display_name = campaign

        if campaign in top_ids:
            category = "ID-Based Campaign"
        elif source_medium == "google / cpc":
            category = "Google CPC (Paid)"
            display_name = "Google CPC"
        elif campaign in ["(direct)", "(referral)", "(organic)", "(not set)"]:
            category = "Baseline (Organic/Direct)"
            display_name = campaign
        elif "organic" in channel.lower():
            category = "Baseline (Organic/Direct)"
            display_name = f"Organic ({channel})"
        
        # We only care about reporting the Top 10 IDs daily, 
        # plus the aggregate "Google CPC" and "Baselines"
        # To avoid a massive table, we filter for meaningful items
        if category == "ID-Based Campaign" or category == "Google CPC (Paid)" or category == "Baseline (Organic/Direct)":
            final_rows.append([
                formatted_date,
                category,
                display_name,
                channel,
                str(sessions),
                f"{conversions:g}",
                eng_rate,
                str(active_users)
            ])

    # Sort final rows primarily by date, then category
    final_rows.sort(key=lambda x: (x[0], x[1]))

    # --- Structured Data for Charting ---
    # We want a dictionary where keys are "Campaign/Source" and values are daily data
    # data[campaign_name][date] = { sessions, conversions, engagement_rate, users }
    chart_data = {}
    all_dates = sorted(list(set(row[0] for row in final_rows)))
    all_campaign_names = sorted(list(set(row[2] for row in final_rows)))

    for row in final_rows:
        date_str = row[0]
        campaign_name = row[2]
        
        if campaign_name not in chart_data:
            chart_data[campaign_name] = {}
            
        chart_data[campaign_name][date_str] = {
            "sessions": int(row[4].replace(',', '')),
            "conversions": float(row[5]),
            "engagement_rate": row[6],
            "users": int(row[7].replace(',', ''))
        }

    headers = ["Date", "Category", "Campaign/Source", "Channel", "Sessions", "Conversions", "Engagement Rate", "Active Users"]
    
    report_data = {
        "title": "Top Campaign Daily Trend & Baseline Analysis",
        "special_type": "top_campaign_daily_trend",
        "headers": headers,
        "rows": final_rows,
        "json_data": chart_data,
        "dates": all_dates,
        "campaign_names": all_campaign_names,
        "explanation": (
            "**Report Overview:** This report isolates the top 10 numeric Campaign IDs and tracks their daily performance against baseline traffic sources.\n\n"
            "**Metric Definitions:**\n"
            "* **Sessions:** The number of sessions that began on your site.\n"
            "* **Active Users:** The number of distinct users who visited your site and had an engaged session or when Analytics collects: the first_visit event or at least 2 engagement_speed events.\n"
            "* **Conversions:** The total count of conversion events (e.g., lead generation, purchases).\n"
            "**Engagement Rate:** The percentage of engaged sessions (Sessions that lasted longer than 10 seconds, had a conversion event, or had 2 or more screen or page views).\n\n"
            "**Categorization:**\n"

            "* **ID-Based Campaigns:** Focuses on the top 10 most active campaigns identified by numeric IDs.\n"
            "* **Google CPC:** Separately highlights Paid Search performance to distinguish it from ID-based manual campaigns.\n"
            "* **Baseline:** Includes Direct, Referral, and Organic traffic to provide a 'control group' for performance comparison."
        )
    }

    return report_data
