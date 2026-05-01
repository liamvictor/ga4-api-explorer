from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, OrderBy
import re

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a report that isolates ONLY the top 15 numeric Campaign IDs.
    Provides a daily breakdown for these specific IDs.
    """
    
    # 1. Identify the Top 15 Numeric Campaign IDs
    top_campaigns_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionCampaignName")],
        metrics=[Metric(name="sessions")],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=1000 # Broad scan to find IDs
    )

    try:
        campaign_response = data_client.run_report(top_campaigns_request)
    except Exception as e:
        print(f"Error identifying numeric campaigns: {e}")
        return None

    top_ids = []
    for row in campaign_response.rows:
        campaign_name = row.dimension_values[0].value
        # Strict numeric match
        if re.match(r'^\d+$', campaign_name):
            top_ids.append(campaign_name)
            if len(top_ids) >= 15:
                break

    if not top_ids:
        print("No numeric campaign IDs found.")
        return None

    # 2. Query Daily Data filtered by these Top 15 IDs
    daily_request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="date"),
            Dimension(name="sessionCampaignName"),
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
        print(f"Error running numeric campaign daily trend: {e}")
        return None

    final_rows = []
    chart_data = {}
    
    # Filter and process rows
    for row in daily_response.rows:
        campaign = row.dimension_values[1].value
        
        # ONLY include the isolated numeric IDs
        if campaign in top_ids:
            raw_date = row.dimension_values[0].value
            formatted_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            channel = row.dimension_values[2].value
            
            sessions = int(row.metric_values[0].value)
            conversions = float(row.metric_values[1].value)
            eng_rate_raw = float(row.metric_values[2].value)
            eng_rate = f"{eng_rate_raw * 100:.2f}%"
            active_users = int(row.metric_values[3].value)

            final_rows.append([
                formatted_date,
                "Numeric Campaign",
                campaign,
                channel,
                str(sessions),
                f"{conversions:g}",
                eng_rate,
                str(active_users)
            ])

            if campaign not in chart_data:
                chart_data[campaign] = {}
            
            chart_data[campaign][formatted_date] = {
                "sessions": sessions,
                "conversions": conversions,
                "engagement_rate": eng_rate,
                "users": active_users
            }

    # Sort primarily by date
    final_rows.sort(key=lambda x: (x[0], x[2]))

    all_dates = sorted(list(set(row[0] for row in final_rows)))
    all_campaign_names = sorted(list(chart_data.keys()))

    headers = ["Date", "Category", "Campaign ID", "Channel", "Sessions", "Conversions", "Engagement Rate", "Active Users"]
    
    report_data = {
        "title": "Top 15 Numeric Campaign Daily Performance",
        "special_type": "top_campaign_daily_trend", # Reuses the existing chart template
        "headers": headers,
        "rows": final_rows,
        "json_data": chart_data,
        "dates": all_dates,
        "campaign_names": all_campaign_names,
        "explanation": (
            "**Report Overview:** This report provides a surgical focus on the top 15 marketing campaigns identified by numeric IDs.\n\n"
            "**Metric Definitions:**\n"
            "* **Sessions:** The number of sessions that began on your site.\n"
            "* **Active Users:** The number of distinct users who visited your site and had an engaged session or when Analytics collects: the first_visit event or at least 2 engagement_speed events.\n"
            "* **Conversions:** The total count of conversion events (e.g., lead generation, purchases).\n"
            "**Engagement Rate:** The percentage of engaged sessions (Sessions that lasted longer than 10 seconds, had a conversion event, or had 2 or more screen or page views).\n\n"
            "**Scope:** Excludes all non-numeric campaigns, direct traffic, and generic organic/referral sources."

        )
    }

    return report_data
