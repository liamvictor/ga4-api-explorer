from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
import ga4_client
import run_report
import output_manager
from datetime import datetime, timedelta

def get_event_list(property_id, data_client, start_date, end_date):
    """Fetches the list of events and their counts for a property."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="eventName")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )
    
    try:
        response = data_client.run_report(request)
        
        report_data = {
            "title": "All Tracked Events",
            "headers": ["Event Name", "Event Count"],
            "rows": []
        }
        
        if not response.rows:
            return report_data
            
        for row in response.rows:
            event_name = row.dimension_values[0].value
            event_count = row.metric_values[0].value
            report_data["rows"].append([event_name, event_count])
            
        # Sort by count descending
        report_data["rows"].sort(key=lambda x: int(x[1]), reverse=True)
        
        return report_data
    except Exception as e:
        print(f"Error fetching events for property {property_id}: {e}")
        return None

def main():
    print("Starting global event listing for all properties...")
    
    # Authenticate
    google_auth = ga4_client.get_google_auth()
    if not google_auth:
        print("Failed to authenticate.")
        return
        
    data_client = ga4_client.get_data_client()
    if not data_client:
        print("Failed to get data client.")
        return
        
    # Get all properties
    all_properties = run_report.get_all_properties()
    if not all_properties:
        print("No properties found.")
        return
        
    print(f"Found {len(all_properties)} properties.")
    
    # Set date range (Last 30 days by default)
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    for prop_info in all_properties:
        display_name = prop_info['display_name']
        property_id = prop_info['property_id']
        
        print(f"\n--- Processing: {display_name} (ID: {property_id}) ---")
        
        report_data = get_event_list(property_id, data_client, start_date, end_date)
        
        if report_data:
            report_data['date_range'] = f"{start_date} to {end_date}"
            # Save as CSV and HTML using the standard output manager
            output_manager.save_to_csv_and_html(report_data, prop_info, start_date, end_date)
        else:
            print(f"Skipping {display_name} due to error or no data.")

    print("\nGlobal event listing complete. Check the 'output' directory for results.")

if __name__ == "__main__":
    main()
