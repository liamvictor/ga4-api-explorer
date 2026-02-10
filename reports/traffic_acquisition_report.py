# reports/traffic_acquisition_report.py

from google.analytics.data_v1beta.types import RunReportRequest, Dimension, Metric, OrderBy, DateRange

def run_report(property_id, data_client, start_date, end_date):
    """
    Runs a detailed Traffic Acquisition report, including engagement and conversion metrics,
    ordered by the total number of users.
    """
    
    # Define the dimensions and metrics for the report.
    # This report provides a comprehensive view of how different channels are performing.
    dimensions = [
        Dimension(name="sessionDefaultChannelGroup"),
        Dimension(name="sessionSourceMedium"),
    ]
    metrics = [
        Metric(name="totalUsers"),
        Metric(name="newUsers"),
        Metric(name="engagedSessions"),
        Metric(name="engagementRate"),
        Metric(name="conversions"), # Note: This will sum ALL conversion events.
    ]
    
    # Order the results by the total number of users in descending order
    # to see the most significant traffic sources first.
    order_bys = [
        OrderBy(
            metric=OrderBy.MetricOrderBy(metric_name="totalUsers"),
            desc=True
        ),
    ]

    # Create the report request
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=dimensions,
        metrics=metrics,
        order_bys=order_bys,
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    # Execute the report request
    try:
        response = data_client.run_report(request)
    except Exception as e:
        print(f"Error running Traffic Acquisition report: {e}")
        return None

    # Process the response and format it into the standardized dictionary.
    
    # Extract headers for dimensions and metrics
    report_headers = [header.name for header in response.dimension_headers] + [header.name for header in response.metric_headers]
    
    # Process each row of the response
    report_rows = []
    total_total_users = 0
    total_new_users = 0
    total_engaged_sessions = 0
    total_conversions = 0
    sum_engagement_rate = 0.0
    row_count = 0

    if response.rows:
        for row in response.rows:
            row_count += 1
            row_data = []
            # Add dimension values
            for value in row.dimension_values:
                row_data.append(value.value)
            
            # Create a dictionary of metric values for easier lookup
            metric_values_dict = {}
            for i, value in enumerate(row.metric_values):
                metric_name = response.metric_headers[i].name
                metric_values_dict[metric_name] = value.value

            # Add to totals, converting to the correct type
            total_total_users += int(metric_values_dict.get('totalUsers', 0))
            total_new_users += int(metric_values_dict.get('newUsers', 0))
            total_engaged_sessions += int(metric_values_dict.get('engagedSessions', 0))
            total_conversions += int(metric_values_dict.get('conversions', 0))
            sum_engagement_rate += float(metric_values_dict.get('engagementRate', 0.0))

            # Append metric values to row_data in the correct order defined by headers
            for header in response.metric_headers:
                metric_name = header.name
                value = metric_values_dict.get(metric_name)
                if metric_name == 'engagementRate':
                    row_data.append(f"{float(value) * 100:.2f}%")
                else:
                    row_data.append(value)
            report_rows.append(row_data)

    # Add a total row if there was data
    if row_count > 0:
        average_engagement_rate = (sum_engagement_rate / row_count) * 100
        total_row = [
            "Total",  # sessionDefaultChannelGroup
            "",  # sessionSourceMedium
            str(total_total_users),
            str(total_new_users),
            str(total_engaged_sessions),
            f"{average_engagement_rate:.2f}%",
            str(total_conversions)
        ]
        report_rows.append(total_row)

    report_data = {
        "title": "Traffic Acquisition Report",
        "headers": report_headers,
        "rows": report_rows,
    }

    return report_data
