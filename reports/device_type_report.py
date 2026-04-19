# reports/device_type_report.py

from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, DateRange

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Device Type report focusing on device category (desktop, mobile, tablet).
    Calculates the percentage of total traffic for each category and shows bounce rate.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[
            Metric(name="totalUsers"),
            Metric(name="bounceRate")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Device Type Report: {e}")
        return None

    # Calculate total users across all categories to determine percentages
    total_users_sum = 0
    temp_rows = []
    for row in response.rows:
        category = row.dimension_values[0].value
        users = int(row.metric_values[0].value)
        bounce_rate = float(row.metric_values[1].value)
        total_users_sum += users
        temp_rows.append([category, users, bounce_rate])

    # Standardized report data structure
    report_data = {
        "title": "Device Type Traffic Share",
        "headers": [
            "Device Category", 
            "Users", 
            "% of Traffic", 
            "Bounce Rate"
        ],
        "rows": [],
        "explanation": (
            "This report breaks down your audience by the type of device they use. \n"
            "* **% of Traffic:** Shows the relative share of each device type.\n"
            "* **Bounce Rate:** Helps identify if certain devices (like mobile) have experience issues."
        )
    }

    for category, users, bounce_rate in temp_rows:
        percentage = (users / total_users_sum * 100) if total_users_sum > 0 else 0
        report_data["rows"].append([
            category.title(),
            str(users),
            f"{percentage:.1f}%",
            f"{bounce_rate * 100:.2f}%"
        ])

    return report_data
