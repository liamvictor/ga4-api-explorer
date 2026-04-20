# reports/device_type_report.py

from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, DateRange

def run_report(property_id, data_client, start_date, end_date):
    """
    Generates a report on device types, including total users, engagement rate, bounce rate,
    and the percentage of total traffic for each category.
    """
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="deviceCategory")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="totalUsers"),
            Metric(name="newUsers"),
            Metric(name="engagedSessions"),
            Metric(name="sessions"),
            Metric(name="engagementRate"),
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
        active_users = int(row.metric_values[0].value)
        total_users = int(row.metric_values[1].value)
        new_users = int(row.metric_values[2].value)
        engaged_sessions = int(row.metric_values[3].value)
        sessions = int(row.metric_values[4].value)
        engagement_rate = float(row.metric_values[5].value)
        bounce_rate = float(row.metric_values[6].value)
        
        total_users_sum += total_users
        temp_rows.append({
            "category": category,
            "active_users": active_users,
            "total_users": total_users,
            "new_users": new_users,
            "engaged_sessions": engaged_sessions,
            "sessions": sessions,
            "engagement_rate": engagement_rate,
            "bounce_rate": bounce_rate
        })

    # Standardized report data structure
    report_data = {
        "title": "Device Type Traffic Share",
        "headers": [
            "Device Category", 
            "Active Users",
            "Total Users",
            "% of Traffic", 
            "Engagement Rate",
            "Bounce Rate"
        ],
        "rows": [],
        "explanation": (
            "This report breaks down your audience by the type of device they use. \n"
            "* **Active Users:** The number of distinct users who had an engaged session.\n"
            "* **Total Users:** The total number of unique users who logged any event.\n"
            "* **% of Traffic:** Shows the relative share of each device type (based on Total Users).\n"
            "* **Engagement Rate:** The percentage of sessions that were engaged sessions.\n"
            "* **Bounce Rate:** The percentage of sessions that were not engaged (1 - Engagement Rate)."
        )
    }

    for data in temp_rows:
        percentage = (data["total_users"] / total_users_sum * 100) if total_users_sum > 0 else 0
        report_data["rows"].append([
            data["category"].title(),
            str(data["active_users"]),
            str(data["total_users"]),
            f"{percentage:.1f}%",
            f"{data['engagement_rate'] * 100:.2f}%",
            f"{data['bounce_rate'] * 100:.2f}%"
        ])

    return report_data
