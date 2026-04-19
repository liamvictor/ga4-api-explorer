# reports/cohort_retention_report.py

from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter, FilterExpressionList
from datetime import datetime, timedelta

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Cohort Retention report using standard run_report.
    This report shows how many users return to the site in the weeks following their first visit.
    """
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="firstSessionDate"),
            Dimension(name="date")
        ],
        metrics=[
            Metric(name="activeUsers")
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Cohort Retention Report: {e}")
        return None

    # We need to process the rows to group by "Acquisition Week" and "Retention Week"
    # firstSessionDate is YYYYMMDD
    # date is YYYYMMDD
    
    cohort_data = {} # { acquisition_week_start: { week_n: users } }
    
    for row in response.rows:
        acquisition_date_str = row.dimension_values[0].value
        activity_date_str = row.dimension_values[1].value
        users = int(row.metric_values[0].value)
        
        if not acquisition_date_str or not activity_date_str:
            continue
            
        try:
            acq_dt = datetime.strptime(acquisition_date_str, "%Y%m%d")
            act_dt = datetime.strptime(activity_date_str, "%Y%m%d")
        except ValueError:
            continue
        
        # Determine the start of the acquisition week (Monday)
        acq_week_start = acq_dt - timedelta(days=acq_dt.weekday())
        acq_week_start_str = acq_week_start.strftime("%Y-%m-%d")
        
        # Determine how many weeks after acquisition this activity happened
        days_diff = (act_dt - acq_week_start).days
        week_n = days_diff // 7
        
        if week_n < 0: continue # Should not happen with firstSessionDate
        if week_n > 5: continue # Limit to 6 weeks (0-5)
        
        if acq_week_start_str not in cohort_data:
            cohort_data[acq_week_start_str] = {}
            
        cohort_data[acq_week_start_str][week_n] = cohort_data[acq_week_start_str].get(week_n, 0) + users

    # Pivot into table format
    max_weeks = 6
    headers = ["Cohort (Week Starting)"] + [f"Week {i}" for i in range(max_weeks)]
    final_rows = []
    
    # Sort by acquisition week
    for acq_week in sorted(cohort_data.keys()):
        week_0_users = cohort_data[acq_week].get(0, 0)
        if week_0_users == 0: continue
        
        row_data = [acq_week]
        row_data.append(str(week_0_users))
        
        for i in range(1, max_weeks):
            count = cohort_data[acq_week].get(i, 0)
            percentage = (count / week_0_users) * 100
            row_data.append(f"{percentage:.1f}% ({count})")
            
        final_rows.append(row_data)

    report_data = {
        "title": "Cohort Retention Report (Weekly)",
        "headers": headers,
        "rows": final_rows,
        "explanation": (
            "This report shows user retention week-over-week. \n"
            "* **Cohort:** The week when users first visited the site (starting Monday).\n"
            "* **Week 0:** Total users acquired in that week.\n"
            "* **Week 1-5:** The percentage of those same users who returned in subsequent weeks.\n"
            "This is a manual calculation based on 'First Session Date' to ensure compatibility across SDK versions."
        )
    }

    return report_data
