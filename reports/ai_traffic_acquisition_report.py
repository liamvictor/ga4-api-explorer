from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs an AI Traffic Acquisition report.
    This report filters traffic to show only known AI tools (e.g., ChatGPT, Gemini, Perplexity).
    """
    
    # Regex pattern for known AI tools
    ai_regex = "chatgpt|openai|perplexity|gemini\\.google|anthropic|claude|copilot|bard\\.google"

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="sessionSource"),
            Dimension(name="sessionMedium")
        ],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="activeUsers"),
            Metric(name="sessions"),
            Metric(name="engagedSessions"),
            Metric(name="engagementRate"),
            Metric(name="conversions")
        ],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="sessionSource",
                string_filter=Filter.StringFilter(
                    match_type=Filter.StringFilter.MatchType.PARTIAL_REGEXP,
                    value=ai_regex
                )
            )
        ),
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[{"metric": {"metric_name": "totalUsers"}, "desc": True}],
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running AI Traffic Acquisition Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "AI Traffic Acquisition Report",
        "headers": [
            "Source", 
            "Medium", 
            "Total Users", 
            "Active Users", 
            "Sessions", 
            "Engaged Sessions", 
            "Engagement Rate", 
            "Conversions"
        ],
        "rows": [],
        "explanation": (
            "This report isolates traffic coming from known AI discovery tools and chatbots. "
            "It helps track how 'Generative Engine Optimization' (GEO) is impacting your site traffic."
        )
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        source = row.dimension_values[0].value
        medium = row.dimension_values[1].value
        total_users = row.metric_values[0].value
        active_users = row.metric_values[1].value
        sessions = row.metric_values[2].value
        engaged_sessions = row.metric_values[3].value
        
        try:
            engagement_rate = f"{float(row.metric_values[4].value) * 100:.2f}%"
        except (ValueError, TypeError):
            engagement_rate = row.metric_values[4].value
            
        conversions = row.metric_values[5].value

        report_data["rows"].append([
            source,
            medium,
            total_users,
            active_users,
            sessions,
            engaged_sessions,
            engagement_rate,
            conversions
        ])

    return report_data
