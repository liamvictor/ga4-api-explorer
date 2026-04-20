# reports/utm_full_content_report.py

from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, OrderBy
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

def strip_tracking_params(url):
    """
    Advanced stripping of tracking parameters.
    Removes standard click IDs, Marketo/HubSpot tags, and internal tracking blobs.
    """
    if not url:
        return url
    
    # Exact match parameters to strip (case-insensitive)
    exact_params = {
        'msclkid', 'gclid', 'fbclid', 'gbraid', 'wbraid', 'gad_source', 'gad_campaignid', # Ad Platforms
        'mkt_tok', 'aliid',                                                               # Marketo
        '_hsenc', '_hsmi', '__hssc', '__hstc', 'hsctatracking',                           # HubSpot
        'visit_number'                                                                    # Internal tracking
    }
    
    try:
        parsed = urlparse(url)
        qsl = parse_qsl(parsed.query)
        
        filtered = []
        for k, v in qsl:
            k_low = k.lower()
            
            # Skip if it's an exact match
            if k_low in exact_params:
                continue
            
            # Skip if it starts with utm_
            if k_low.startswith('utm_'):
                continue
                
            # Skip internal state patterns
            if '_running_' in k_low or k_low.endswith('_running'):
                continue
                
            filtered.append((k, v))
        
        new_query = urlencode(filtered)
        cleaned_url = urlunparse(parsed._replace(query=new_query))
        return cleaned_url
    except Exception:
        return url

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
    # Added limit to prevent timeout on high-cardinality datasets
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=dimensions,
        metrics=metrics,
        order_bys=order_bys,
        date_ranges=[{"start_date": start_date, "end_date": end_date}],
        limit=10000 
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
            f"{eng_rate * 100:.2f}%",
            f"{bounce_rate * 100:.2f}%",
            f"{conversions:g}"
        ])

    # Sort final rows by sessions descending
    final_rows.sort(key=lambda x: int(x[3]), reverse=True)

    headers = ["Campaign", "Content", "Landing Page", "Sessions", "Engaged Sessions", "Engagement Rate", "Bounce Rate", "Conversions"]
    
    report_data = {
        "title": "UTM Full Content & Landing Page Report",
        "headers": headers,
        "rows": final_rows,
        "explanation": (
            "**Note:** This report performs aggressive data cleaning to prevent row fragmentation. \n"
            "* **Stripped:** Click IDs (gclid, msclkid, fbclid), Marketo/HubSpot tags, and internal tracking blobs. \n"
            "* **UTM Parameters:** All `utm_*` parameters are stripped from the URL path as they are already captured in the Campaign/Content dimensions. \n"
            "* **Aggregation:** Data is re-aggregated after cleaning to provide a consolidated view. \n"
            "* **Limit:** Initial data fetch is limited to the top 10,000 rows to ensure report stability."
        )
    }

    return report_data
