from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
from google.analytics.data_v1beta.types import RunReportRequest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import collections

def get_all_time_date_range(google_auth, property_id):
    """
    Gets the creation time of a property and returns it as a start date.
    """
    try:
        admin_client = AnalyticsAdminServiceClient(credentials=google_auth)
        property_name = f"properties/{property_id}"
        prop = admin_client.get_property(name=property_name)
        create_time = prop.create_time
        start_date = create_time.strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        return start_date, end_date
    except Exception as e:
        print(f"Error getting property creation time: {e}")
        # Fallback to last 12 months
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        return start_date, end_date

def run_report(property_id,
               data_client,
               google_auth,
               start_date=None,
               end_date=None):
    """
    Generates a historical report on device types, including total users, engagement rate, and bounce rate.
    """
    if not start_date or not end_date:
        start_date, end_date = get_all_time_date_range(google_auth, property_id)

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

    months = []
    incomplete_months = {}
    
    monthly_reports = []

    current_date = start_date_obj
    while current_date <= end_date_obj:
        month_start = current_date.replace(day=1)
        month_end = month_start + relativedelta(months=1) - timedelta(days=1)
        
        query_start_date = max(month_start, start_date_obj)
        query_end_date = min(month_end, end_date_obj)
        
        month_str = query_start_date.strftime("%b %Y")
        months.append(month_str)

        if query_start_date.day != 1 or query_end_date.day != month_end.day:
            incomplete_months[month_str] = "Incomplete month"

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[{"name": "deviceCategory"}],
            metrics=[
                {"name": "activeUsers"},
                {"name": "engagedSessions"},
                {"name": "sessions"}
            ],
            date_ranges=[{"start_date": query_start_date.strftime("%Y-%m-%d"), "end_date": query_end_date.strftime("%Y-%m-%d")}],
        )
        response = data_client.run_report(request)
        monthly_reports.append(response)
        
        current_date += relativedelta(months=1)
    
    all_categories = set()
    for report in monthly_reports:
        for row in report.rows:
            all_categories.add(row.dimension_values[0].value)
            
    all_categories_sorted = sorted(list(all_categories))
    
    table_data = collections.defaultdict(lambda: collections.defaultdict(list))
    chart_data = collections.defaultdict(lambda: collections.defaultdict(list))

    for report in monthly_reports:
        data_for_month = {row.dimension_values[0].value: row.metric_values for row in report.rows}
        for category in all_categories_sorted:
            metric_values = data_for_month.get(category)
            if metric_values:
                active_users = int(metric_values[0].value)
                engaged_sessions = int(metric_values[1].value)
                sessions = int(metric_values[2].value)
            else:
                active_users = 0
                engaged_sessions = 0
                sessions = 0
                
            table_data['Active Users'][category].append(active_users)
            table_data['Engaged Sessions'][category].append(engaged_sessions)
            table_data['Sessions'][category].append(sessions)

            chart_data[category]['Active Users'].append(active_users)
            chart_data[category]['Engaged Sessions'].append(engaged_sessions)
            chart_data[category]['Sessions'].append(sessions)
            
            bounce_rate = (1 - (engaged_sessions / sessions)) if sessions > 0 else 0
            table_data['Bounce Rate'][category].append(f"{bounce_rate:.2%}")
            chart_data[category]['Bounce Rate'].append(bounce_rate)

    explanation = """
    **Metrics Explanation:**
    *   **Active Users:** The number of distinct users who had an engaged session on your site or app. This is the primary user metric in GA4.
    *   **Engaged Sessions:** The number of sessions that lasted longer than 10 seconds, had a conversion event, or had 2 or more page/screen views.
    *   **Sessions:** The total number of sessions initiated. A session is a period of time during which a user is actively engaged with your site or app.
    *   **Bounce Rate:** The percentage of sessions that were not engaged (calculated as 1 - Engagement Rate).
    """

    return {
        "title": "Device Type Historical Report",
        "table_data": table_data,
        "chart_data": chart_data,
        "months": months,
        "incomplete_months": incomplete_months,
        "explanation": explanation
    }
