# reports/cohort_retention_report.py

from google.analytics.data_v1beta.types import (
    RunCohortReportRequest, 
    Cohort, 
    CohortSpec, 
    CohortReportSettings, 
    Dimension, 
    Metric, 
    DateRange
)
from datetime import datetime, timedelta

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a Cohort Retention report.
    This report shows how many users return to the site in the weeks following their first visit.
    It uses weekly cohorts based on the 'firstSessionDate' dimension.
    """
    
    # We'll split the date range into weekly cohorts.
    # GA4 Cohort reports are powerful but have specific requirements.
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    cohorts = []
    current_dt = start_dt
    
    # Generate up to 5 weekly cohorts to keep the report manageable
    cohort_count = 0
    while current_dt + timedelta(days=6) <= end_dt and cohort_count < 5:
        cohort_start = current_dt.strftime("%Y-%m-%d")
        cohort_end = (current_dt + timedelta(days=6)).strftime("%Y-%m-%d")
        
        cohorts.append(Cohort(
            name=f"week_{cohort_count}",
            dimension="firstSessionDate",
            date_range=DateRange(start_date=cohort_start, end_date=cohort_end)
        ))
        
        current_dt += timedelta(days=7)
        cohort_count += 1

    if not cohorts:
        # Fallback to a single cohort if the range is too small for a full week
        cohorts.append(Cohort(
            name="initial_cohort",
            dimension="firstSessionDate",
            date_range=DateRange(start_date=start_date, end_date=end_date)
        ))

    request = RunCohortReportRequest(
        property=f"properties/{property_id}",
        cohort_spec=CohortSpec(
            cohorts=cohorts,
            cohort_report_settings=CohortReportSettings(accumulate=False)
        ),
        dimensions=[
            Dimension(name="cohort"),
            Dimension(name="cohortNthWeek")
        ],
        metrics=[
            Metric(name="cohortActiveUsers")
        ]
    )

    try:
        response = data_client.run_cohort_report(request)
    except Exception as e:
        print(f"Error running Cohort Retention Report: {e}")
        return None

    # Process the response. 
    # Cohort reports return data in a long format: (Cohort, Week N, Value)
    # We want to pivot this into a table.
    
    # headers: ["Cohort Date Range", "Week 0", "Week 1", "Week 2", "Week 3", "Week 4", "Week 5"]
    max_weeks = 6
    headers = ["Cohort Date Range"] + [f"Week {i}" for i in range(max_weeks)]
    
    # Use a dict to store rows by cohort name
    cohort_rows = {}
    
    # Map cohort names back to their date ranges for display
    cohort_name_map = {c.name: f"{c.date_range.start_date} to {c.date_range.end_date}" for c in cohorts}

    for row in response.rows:
        cohort_name = row.dimension_values[0].value
        nth_week = int(row.dimension_values[1].value)
        active_users = int(row.metric_values[0].value)
        
        if cohort_name not in cohort_rows:
            cohort_rows[cohort_name] = [0] * max_weeks
            
        if nth_week < max_weeks:
            cohort_rows[cohort_name][nth_week] = active_users

    # Convert the dict to a list of rows, sorted by the cohort start date
    final_rows = []
    for cohort_name in sorted(cohort_rows.keys()):
        display_name = cohort_name_map.get(cohort_name, cohort_name)
        # Check if Week 0 has users to avoid division by zero
        week_0_users = cohort_rows[cohort_name][0]
        
        row_data = [display_name]
        for i in range(max_weeks):
            count = cohort_rows[cohort_name][i]
            if i == 0:
                row_data.append(str(count))
            elif week_0_users > 0:
                percentage = (count / week_0_users) * 100
                row_data.append(f"{percentage:.1f}% ({count})")
            else:
                row_data.append(f"0% ({count})")
        
        final_rows.append(row_data)

    report_data = {
        "title": "Cohort Retention Report (Weekly)",
        "headers": headers,
        "rows": final_rows,
        "explanation": (
            "This report shows user retention week-over-week. \n"
            "* **Cohort Date Range:** The week when the users first visited the site.\n"
            "* **Week 0:** Total users acquired in that week.\n"
            "* **Week 1-5:** The percentage of those same users who returned in subsequent weeks.\n"
            "This is a key metric for measuring product-market fit and long-term user value."
        )
    }

    return report_data
