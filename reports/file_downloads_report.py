# reports/file_downloads_report.py

from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter, OrderBy

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a File Downloads report.
    This report identifies which files (PDFs, docs, etc.) users are downloading from the site.
    It relies on GA4's 'Enhanced Measurement' being enabled for file downloads.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="fileName"),
            Dimension(name="fileExtension"),
            Dimension(name="linkUrl"),
        ],
        metrics=[
            Metric(name="eventCount"),
            Metric(name="totalUsers")
        ],
        dimension_filter=FilterExpression(
            filter=Filter(
                field_name="eventName",
                string_filter=Filter.StringFilter(
                    value="file_download"
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
        print(f"Error running File Downloads Report: {e}")
        return None

    # Standardized report data structure
    report_data = {
        "title": "File Downloads Report",
        "headers": [
            "File Name", 
            "Extension", 
            "Link URL",
            "Downloads", 
            "Users"
        ],
        "rows": [],
        "explanation": (
            "This report lists the files downloaded by users. "
            "It automatically captures downloads of common file types (e.g., pdf, xls, doc, txt, zip) "
            "provided 'Enhanced Measurement' is active in your GA4 property settings."
        )
    }

    if not response.rows:
        return report_data

    for row in response.rows:
        file_name = row.dimension_values[0].value
        extension = row.dimension_values[1].value
        link_url = row.dimension_values[2].value
        downloads = row.metric_values[0].value
        users = row.metric_values[1].value

        report_data["rows"].append([
            file_name,
            extension,
            link_url,
            downloads,
            users
        ])

    return report_data
