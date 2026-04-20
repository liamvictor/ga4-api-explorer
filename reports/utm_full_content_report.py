# reports/utm_full_content_report.py

from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, OrderBy
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def strip_tracking_params(url):
    """Strips common tracking parameters (mkt_tok, aliId) from a URL/path string."""
    if not url:
        return url
    
    # Quick check to avoid overhead if no tracking params are likely present
    tracking_params = {'mkt_tok', 'aliId'}
    if not any(param in url for param in tracking_params):
        return url
    
    parsed = urlparse(url)
    qsl = parse_qsl(parsed.query)
    filtered = [(k, v) for k, v in qsl if k not in tracking_params]
    
    new_query = urlencode(filtered)
    return urlunparse(parsed._replace(query=new_query))

def run_report(property_id, data_client, start_date, end_date):
    """Runs a full campaign content and landing page report with tracking param stripping."""
    
    # Define the dimensions and metrics for the report
    dimensions = [
        Dimension(name="sessionCampaignName"),
        Dimension(name="sessionManualAdContent"),
        Dimension(name="landingPagePlusQueryString"),
    ]
    metrics = [
        Metric(name="sessions"),
        Metric(name="engagedSessions"),
        Metric(name="engagementRate"),
        Metric(name="bounceRate"),
        Metric(name="conversions"),
    ]
    order_bys = [
        OrderBy(
            metric=OrderBy.MetricOrderBy(metric_name="sessions"),
            desc=True
        ),
    ]

    # Create the report request
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=dimensions,
        metrics=metrics,
        order_bys=order_bys,
        date_ranges=[{"start_date": start_date, "end_date": end_date}],
    )

    # Execute the report request
    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running UTM Full Content report: {e}")
        return None

    # Process and aggregate rows
    aggregated_data = {}
    
    for row in response.rows:
        campaign = row.dimension_values[0].value
        content = row.dimension_values[1].value
        landing_page = strip_tracking_params(row.dimension_values[2].value)
        
        sessions = int(row.metric_values[0].value)
        engaged = int(row.metric_values[1].value)
        conversions = float(row.metric_values[4].value)
        
        key = (campaign, content, landing_page)
        
        if key not in aggregated_data:
            aggregated_data[key] = {
                "sessions": 0,
                "engagedSessions": 0,
                "conversions": 0.0
            }
        
        aggregated_data[key]["sessions"] += sessions
        aggregated_data[key]["engagedSessions"] += engaged
        aggregated_data[key]["conversions"] += conversions

    # Rebuild rows and recalculate rates
    final_rows = []
    for key, totals in aggregated_data.items():
        sessions = totals["sessions"]
        engaged = totals["engagedSessions"]
        conversions = totals["conversions"]
        
        eng_rate = (engaged / sessions) if sessions > 0 else 0
        bounce_rate = 1 - eng_rate
        
        final_rows.append([
            key[0], # Campaign
            key[1], # Content
            key[2], # Landing Page (Cleaned)
            str(sessions),
            str(engaged),
            f"{eng_rate:.4f}",
            f"{bounce_rate:.4f}",
            f"{conversions:g}"
        ])

    # Sort final rows by sessions descending
    final_rows.sort(key=lambda x: int(x[3]), reverse=True)

    headers = [header.name for header in response.dimension_headers] + [header.name for header in response.metric_headers]
    
    report_data = {
        "title": "UTM Full Content & Landing Page Report",
        "headers": headers,
        "rows": final_rows,
        "explanation": "**Note:** Tracking parameters (`mkt_tok` and `aliId`) have been stripped from the Landing Page URLs, and the data has been re-aggregated to provide a cleaner view of unique campaign paths."
    }

    return report_data
