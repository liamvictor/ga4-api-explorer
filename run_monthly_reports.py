import argparse
import importlib
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os

from ga4_client import GA4Client
from output_manager import save_report_to_file, print_report

def get_earliest_data_date(property_id, data_client):
    """
    Finds the earliest date with data for a given property by querying the API.
    """
    # Start checking from a very early date. GA4 launched in late 2020.
    start_date = datetime(2020, 1, 1).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    try:
        # A simple report to find any activity.
        # We ask for the date dimension to find the first date with users.
        response = data_client.run_report(
            property=f"properties/{property_id}",
            dimensions=[{"name": "date"}],
            metrics=[{"name": "activeUsers"}],
            date_ranges=[{"start_date": start_date, "end_date": end_date}],
            order_bys=[{"dimension": {"order_type": "ALPHANUMERIC", "dimension_name": "date"}, "desc": False}],
            limit=1
        )
        if response.rows:
            # The date is returned as a string 'YYYYMMDD'
            earliest_date_str = response.rows[0].dimension_values[0].value
            return datetime.strptime(earliest_date_str, '%Y%m%d').date()
    except Exception as e:
        print(f"Error discovering the earliest data date for property {property_id}: {e}")
        return None
    
    return None

def run_monthly_reports():
    """
    Runs a specified report for each calendar month for a given GA4 property,
    starting from the earliest available data month up to the current month.
    """
    parser = argparse.ArgumentParser(description="Run monthly GA4 reports from the earliest data until today.")
    parser.add_argument("property_id", help="The GA4 property ID.")
    parser.add_argument("report_name", help="The name of the report module to run (e.g., 'device_type_report').")
    args = parser.parse_args()

    # Ensure the reports directory exists
    if not os.path.exists("reports"):
        print("Error: 'reports' directory not found. Please run from the 'ga4-api-explorer' root.")
        return

    try:
        report_module = importlib.import_module(f"reports.{args.report_name}")
    except ImportError:
        print(f"Error: Report module 'reports/{args.report_name}.py' not found.")
        return

    data_client = GA4Client()
    print(f"Discovering first data point for property {args.property_id}...")
    
    earliest_date = get_earliest_data_date(args.property_id, data_client.client)
    
    if not earliest_date:
        print("Could not determine the earliest data date. Aborting.")
        return

    print(f"Earliest data found on: {earliest_date}. Generating monthly reports...")

    # Set the start date to the first day of the earliest month
    current_date = earliest_date.replace(day=1)
    end_date = datetime.now().date()

    while current_date <= end_date:
        # First day of the month
        start_of_month = current_date.strftime("%Y-%m-%d")
        # Last day of the month
        end_of_month_date = current_date + relativedelta(months=1) - timedelta(days=1)
        end_of_month = end_of_month_date.strftime("%Y-%m-%d")

        month_str = current_date.strftime("%Y-%m")
        print(f"Running report for {month_str}...")

        try:
            report_data = report_module.run_report(args.property_id, data_client.client, start_of_month, end_of_month)
            
            # Add date range info to the report
            report_data['date_range'] = f"{start_of_month} to {end_of_month}"
            
            # Define filename
            filename = f"{args.report_name}_{args.property_id}_{month_str}.txt"
            
            # Save the report to a file
            save_report_to_file(report_data, filename)
            print(f"  -> Saved to {filename}")

        except Exception as e:
            print(f"  -> Failed to generate report for {month_str}. Error: {e}")

        # Move to the first day of the next month
        current_date += relativedelta(months=1)

    print("Monthly report generation complete.")

if __name__ == "__main__":
    run_monthly_reports()
