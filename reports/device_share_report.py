from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Device Share report.
    This report calculates the percentage of total traffic each device category represents.
    """
    
    # Request data by device category
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="sessions"),
            Metric(name="engagementRate"),
            Metric(name="bounceRate")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Device Share Report: {e}")
        return None

    if not response.rows:
        return {
            "title": "Device Share Report",
            "headers": ["Device Category", "Users", "% Share", "Sessions", "Bounce Rate"],
            "rows": []
        }

    # 1. Calculate Grand Totals first
    grand_total_users = sum(int(row.metric_values[0].value) for row in response.rows)
    
    # 2. Build rows with percentages
    report_data = {
        "title": "Device Share & Engagement Report",
        "headers": ["Device Category", "Total Users", "% Share of Users", "Sessions", "Bounce Rate"],
        "rows": [],
        "explanation": (
            "This report shows the distribution of your audience across device types. "
            "The '% Share' column helps identify your primary platform, while Bounce Rate "
            "highlights performance issues on specific devices (e.g., a high mobile bounce rate may suggest UI issues)."
        )
    }

    for row in response.rows:
        device = row.dimension_values[0].value
        users = int(row.metric_values[0].value)
        sessions = row.metric_values[1].value
        
        # Calculate percentage share
        share = (users / grand_total_users) * 100 if grand_total_users > 0 else 0
        
        try:
            bounce_rate = f"{float(row.metric_values[3].value) * 100:.2f}%"
        except (ValueError, TypeError):
            bounce_rate = row.metric_values[3].value

        report_data["rows"].append([
            device.title(),
            str(users),
            f"{share:.2f}%",
            sessions,
            bounce_rate
        ])

    # Sort by users descending
    report_data["rows"].sort(key=lambda x: int(x[1]), reverse=True)

    return report_data
