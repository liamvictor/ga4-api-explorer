from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
import ga4_client

def list_events(property_id):
    data_client = ga4_client.get_data_client()
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date="2026-04-01", end_date="2026-04-16")],
    )
    response = data_client.run_report(request)
    print(f"Events for property {property_id}:")
    for row in response.rows:
        print(f" - {row.dimension_values[0].value}: {row.metric_values[0].value}")

if __name__ == "__main__":
    list_events("256798047") # Croner GA4
