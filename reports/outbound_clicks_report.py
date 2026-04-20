# reports/outbound_clicks_report.py

from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs an Outbound Click Tracking report.
    This report identifies where users are going when they leave the site by tracking the 'click' event.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="linkUrl"),
            Dimension(name="linkDomain")
        ],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="totalUsers")
        ],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    value="click"
                )
            )
        ),
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        order_bys=[
            OrderBy(
                metric=OrderBy.MetricOrderBy(metric_name="eventCount"),
                desc=True
            )
        ],
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Outbound Click Tracking Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "Outbound Click Tracking Report",
        "headers": [
            "Link URL", 
            "Domain", 
            "Clicks", 
            "Users"
        ],
        "rows": [],
        "explanation": (
            "This report shows external links that users clicked on, leading them away from your site. "
            "It relies on GA4's 'Enhanced Measurement' being enabled for outbound clicks."
        )
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        link_url = row.dimension_values[0].value
        domain = row.dimension_values[1].value
        clicks = row.metric_values[0].value
        users = row.metric_values[1].value

        report_data["rows"].append([
            link_url,
            domain,
            clicks,
            users
        ])

    return report_data
