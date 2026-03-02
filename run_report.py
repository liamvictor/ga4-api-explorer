from google.analytics.admin_v1alpha.types import ListPropertiesRequest
from google.analytics.data_v1beta.types import RunReportRequest
import ga4_client
import output_manager # Import our new output manager
import os
import sys
import importlib.util
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json # New import for caching
import hashlib # New import for caching
import time
import argparse # New import for command-line arguments
if sys.platform == "win32":
    import msvcrt

from settings import CACHE_DURATION # Import CACHE_DURATION from settings.py

def _cleanup_cache():
    """Deletes stale cache files from the cache directory."""
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        return

    current_time = time.time()
    for filename in os.listdir(cache_dir):
        filepath = os.path.join(cache_dir, filename)
        if os.path.isfile(filepath):
            file_mtime = os.path.getmtime(filepath)
            if (current_time - file_mtime) > CACHE_DURATION:
                try:
                    os.remove(filepath)
                    print(f"Cleaned up stale cache file: {filepath}")
                except Exception as e:
                    print(f"Error cleaning up cache file {filepath}: {e}") 


def get_available_reports():
    """Dynamically discovers available reports in the 'reports' directory."""
    reports = {}
    reports_dir = "reports"
    for filename in os.listdir(reports_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            report_name = filename[:-3] # Remove .py extension
            reports[report_name] = { # Use name as key for lookup
                "name": report_name.replace("_", " ").title(),
                "module": report_name
            }
    return reports

def _get_report_by_name(report_name_str):
    """Retrieves report info by its module name."""
    available_reports = get_available_reports()
    for key, report_info in available_reports.items():
        if report_info['module'].lower() == report_name_str.lower() or report_info['name'].replace(" ", "").lower() == report_name_str.lower():
            return report_info
    return None

def get_property_info_by_id(property_id_str):
    """Fetches property info by ID using the Admin API."""
    admin_client = ga4_client.get_admin_client()
    if not admin_client:
        return None
    try:
        property_resource = admin_client.get_property(name=f"properties/{property_id_str}")
        return {
            "display_name": property_resource.display_name,
            "property_id": property_id_str
        }
    except Exception as e:
        print(f"Error: Could not find or access property ID '{property_id_str}'. {e}")
        return None

def get_all_properties():
    """Fetches and returns a list of all available GA4 properties, sorted alphabetically."""
    admin_client = ga4_client.get_admin_client()
    if not admin_client:
        return []

    all_accounts = list(admin_client.list_accounts())
    all_accounts.sort(key=lambda account: account.display_name)

    if not all_accounts:
        print("No GA4 accounts found that are accessible by this service account.")
        return []

    all_properties = []
    for account in all_accounts:
        request = ListPropertiesRequest(filter=f"ancestor:{account.name}")
        account_properties = list(admin_client.list_properties(request=request))
        
        for prop in account_properties:
            all_properties.append({
                "display_name": prop.display_name,
                "property_id": prop.name.split('/')[-1]
            })

    # Sort all properties alphabetically by display name
    all_properties.sort(key=lambda prop: prop['display_name'])
    
    return all_properties

def get_selected_property(cli_property_id=None):
    """Presents a sorted, interactive menu to the user to select a GA4 property."""
    if cli_property_id:
        selected_property = get_property_info_by_id(cli_property_id)
        if selected_property:
            print(f"Using property ID from command-line: {selected_property['display_name']} (ID: {selected_property['property_id']})")
            return selected_property
        else:
            print(f"Invalid or inaccessible property ID '{cli_property_id}' provided via command-line. Falling back to interactive selection...")

    admin_client = ga4_client.get_admin_client()
    if not admin_client:
        return None

    # Fetch and sort accounts alphabetically by display name
    all_accounts = list(admin_client.list_accounts())
    all_accounts.sort(key=lambda account: account.display_name)

    if not all_accounts:
        print("No GA4 accounts found that are accessible by this service account.")
        return None

    properties = {}
    property_list_counter = 1
    
    print("\nAvailable GA4 Properties:")
    for account in all_accounts:
        print(f"\n--- Account: {account.display_name} ---")
        
        # Fetch all properties for the account
        request = ListPropertiesRequest(filter=f"ancestor:{account.name}")
        account_properties = list(admin_client.list_properties(request=request))

        # Sort properties: 'www' first, then alphabetically
        def sort_key(prop):
            is_www = prop.display_name.lower().startswith('www')
            return (0, prop.display_name) if is_www else (1, prop.display_name)
        
        account_properties.sort(key=sort_key)

        if not account_properties:
            print("  No properties found for this account.")
            continue

        for prop in account_properties:
            properties[str(property_list_counter)] = {
                "display_name": prop.display_name,
                "property_id": prop.name.split('/')[-1]
            }
            print(f"{property_list_counter}. {prop.display_name} (ID: {prop.name.split('/')[-1]})")
            property_list_counter += 1
    
    if not properties:
        print("No GA4 properties found that are accessible by this service account.")
        return None

    while True:
        selection = input("\nEnter the number of the property you want to report on: ")
        if selection in properties:
            selected_property = properties[selection]
            print(f"You selected: {selected_property['display_name']} (ID: {selected_property['property_id']})")
            return selected_property
        else:
            print("Invalid selection. Please enter a valid number.")

def get_selected_report(reports, cli_report_name=None):
    """Presents an interactive menu to select an available report, including an option to run all reports."""
    if cli_report_name:
        if cli_report_name.lower() == 'all':
            print("Selected to run all available reports via command-line.")
            return {"name": "All Reports", "module": "all"}
            
        selected_report = _get_report_by_name(cli_report_name)
        if selected_report:
            print(f"Using report from command-line: {selected_report['name']}")
            return selected_report
        else:
            print(f"Invalid report name '{cli_report_name}' provided via command-line. Falling back to interactive selection...")

    print("\nAvailable Reports:")
    numbered_reports = {}
    
    # Add an option to run all reports
    print("1. All Reports")
    numbered_reports['1'] = {"name": "All Reports", "module": "all"}
    
    # List individual reports
    for i, (report_key, report_info) in enumerate(sorted(reports.items(), key=lambda item: item[1]['name']), 2):
        numbered_reports[str(i)] = report_info
        print(f"{i}. {report_info['name']}")
    
    while True:
        selection = input("Enter the number of the report you want to run: ")
        if selection in numbered_reports:
            return numbered_reports[selection]
        else:
            print("Invalid selection. Please enter a valid number.")

def _get_dates_from_args(start_date_str, end_date_str):
    """Validates and parses custom date ranges from command-line arguments."""
    try:
        if not start_date_str or not end_date_str:
            raise ValueError("Both --start-date and --end-date must be provided for custom range.")
        datetime.strptime(start_date_str, '%Y-%m-%d')
        datetime.strptime(end_date_str, '%Y-%m-%d')
        return start_date_str, end_date_str, f"{start_date_str} to {end_date_str}", f"{start_date_str} to {end_date_str}"
    except ValueError as e:
        print(f"Error parsing custom date range from command-line: {e}. Dates must be in YYYY-MM-DD format.")
        return None

def get_selected_date_range(cli_start_date=None, cli_end_date=None, cli_all_months=False):
    """Presents a menu to select a date range and returns start_date, end_date, a display string, and a verbose date range string."""
    today = date.today()

    if cli_all_months:
        return "all-months", "all-months", "All Months", "All Months"

    # Try to get dates from command-line if provided
    if cli_start_date or cli_end_date:
        dates_from_args = _get_dates_from_args(cli_start_date, cli_end_date)
        if dates_from_args:
            print(f"Using date range from command-line: {dates_from_args[3]}")
            return dates_from_args
        else:
            print("Invalid custom date range provided via command-line. Falling back to interactive selection...")

    print("\nSelect a Date Range:")
    print("1. Last 7 Days")
    print("2. Last 28 Days")
    print("3. Last 90 Days")
    print("4. Last Calendar Month (Default)")
    print("5. Custom Date Range")
    print("6. All Months (Generates a file for each month)")


    selection = input("Enter your choice (press Enter for default): ")

    if selection == "1":
        start_date = today - timedelta(days=7)
        return start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), "Last 7 Days", f"{start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
    elif selection == "2":
        start_date = today - timedelta(days=28)
        return start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), "Last 28 Days", f"{start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
    elif selection == "3":
        start_date = today - timedelta(days=90)
        return start_date.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d'), "Last 90 Days", f"{start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
    elif selection == "5":
        while True:
            try:
                start_str = input("Enter start date (YYYY-MM-DD): ")
                end_str = input("Enter end date (YYYY-MM-DD): ")
                datetime.strptime(start_str, '%Y-%m-%d')
                datetime.strptime(end_str, '%Y-%m-%d')
                return start_str, end_str, f"{start_str} to {end_str}", f"{start_str} to {end_str}"
            except ValueError:
                print("Invalid date format. Please use YYYY-MM-DD.")
    elif selection == "6":
        return "all-months", "all-months", "All Months", "All Months"
    else: # Default to Last Calendar Month
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        start_date = last_day_of_previous_month.replace(day=1)
        return start_date.strftime('%Y-%m-%d'), last_day_of_previous_month.strftime('%Y-%m-%d'), "Last Calendar Month", f"{start_date.strftime('%Y-%m-%d')} to {last_day_of_previous_month.strftime('%Y-%m-%d')}"

def _get_output_function_from_args(output_format_str):
    """Maps a command-line output format string to its corresponding function."""
    output_formats_map = {
        "console": output_manager.print_to_console,
        "csv": output_manager.save_to_csv,
        "html": output_manager.save_to_html,
        "csv_html": output_manager.save_to_csv_and_html,
        "txt": output_manager.save_report_to_file,
    }
    return output_formats_map.get(output_format_str.lower())

def get_selected_output_format(cli_output_format=None):
    """Presents an interactive menu to select the output format."""
    if cli_output_format:
        output_func = _get_output_function_from_args(cli_output_format)
        if output_func:
            print(f"Using output format from command-line: {cli_output_format}")
            return output_func, cli_output_format
        else:
            print(f"Invalid output format '{cli_output_format}' provided via command-line. Falling back to interactive selection...")

    output_options_raw = [
        ("Print to Console", output_manager.print_to_console, "console"),
        ("Save as Text File", output_manager.save_report_to_file, "txt"),
        ("Save as CSV", output_manager.save_to_csv, "csv"),
        ("Save as HTML", output_manager.save_to_html, "html"),
        ("Save as CSV & HTML (Default)", output_manager.save_to_csv_and_html, "csv_html"),
    ]
    output_options_raw.sort(key=lambda x: x[0])

    output_functions_map = {}
    print("\nSelect Output Format:")
    for i, (display_name, func, key) in enumerate(output_options_raw, 1):
        output_functions_map[str(i)] = (func, key)
        print(f"{i}. {display_name}")

    while True:
        selection = input("Enter the number for the output format (press Enter for default): ")
        if not selection:
            return output_manager.save_to_csv_and_html, "csv_html"
        if selection in output_functions_map:
            return output_functions_map[selection]
        else:
            print("Invalid selection. Please enter a valid number.")

from google.analytics.data_v1beta.types import RunReportRequest

def get_earliest_data_date(property_id, data_client):
    """Finds the earliest date with data for a given property by querying the API."""
    start_date = datetime(2020, 1, 1).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[{"name": "date"}],
            metrics=[{"name": "activeUsers"}],
            date_ranges=[{"start_date": start_date, "end_date": end_date}],
            order_bys=[{"dimension": {"order_type": "ALPHANUMERIC", "dimension_name": "date"}, "desc": False}],
            limit=1
        )
        response = data_client.run_report(request)
        if response.rows:
            earliest_date_str = response.rows[0].dimension_values[0].value
            return datetime.strptime(earliest_date_str, '%Y%m%d').date()
    except Exception as e:
        print(f"Error discovering the earliest data date for property {property_id}: {e}")
    return None

def run_monthly_reports_for_property(selected_property_info, selected_report, cli_output_format=None, no_cache=False):
    """Runs a report for every month since data collection began."""
    print(f"\nRunning monthly reports for '{selected_report['name']}' on property: {selected_property_info['display_name']}")
    
    data_client = ga4_client.get_data_client()
    earliest_date = get_earliest_data_date(selected_property_info['property_id'], data_client)
    
    if not earliest_date:
        print("Could not determine the earliest data date. Aborting.")
        return

    print(f"Earliest data found on: {earliest_date}. Generating monthly reports...")

    output_function, output_key = get_selected_output_format(cli_output_format)

    if output_key == 'console':
        print("\nWarning: 'All Months' option requires a file-based output.")
        print("Defaulting to 'Save as Text File' format.")
        output_function = output_manager.save_report_to_file
        output_key = 'txt'
    
    current_date = earliest_date.replace(day=1)
    end_loop_date = datetime.now().date()

    while current_date <= end_loop_date:
        start_of_month = current_date.strftime("%Y-%m-%d")
        end_of_month_date = current_date + relativedelta(months=1) - timedelta(days=1)
        end_of_month = end_of_month_date.strftime("%Y-%m-%d")

        month_str = current_date.strftime("%Y-%m")
        print(f"Running report for {month_str}...")

        report_data = run_dynamic_report(
            selected_report['module'],
            selected_property_info['property_id'],
            start_of_month,
            end_of_month,
            no_cache=no_cache
        )

        if report_data:
            report_data['date_range'] = f"{start_of_month} to {end_of_month}"
            
            # For file-based outputs, we generate a specific filename
            if output_key != 'console':
                 filename = f"{selected_report['module']}_{selected_property_info['property_id']}_{month_str}.{output_key.split('_')[0]}"
                 # The save_report_to_file function is simpler and needs a direct filename
                 if output_function == output_manager.save_report_to_file:
                     output_function(report_data, filename)
                 else: # Other file-based savers have a different signature
                     output_function(report_data, selected_property_info, start_of_month, end_of_month)

            else: # Should not happen due to the check above, but as a fallback
                output_function(report_data, selected_property_info, start_of_month, end_of_month)
        else:
            print(f"  -> Failed to generate report for {month_str}.")

        current_date += relativedelta(months=1)

    print("\nMonthly report generation complete.")

def run_dynamic_report(report_module_name, property_id, start_date, end_date, no_cache=False):
    """Dynamically imports and runs a report module for a given date range, with caching."""
    
    cache_key_data = {"property_id": property_id, "report_module": report_module_name, "start_date": start_date, "end_date": end_date}
    cache_key_string = json.dumps(cache_key_data, sort_keys=True)
    cache_filename = hashlib.md5(cache_key_string.encode('utf-8')).hexdigest() + ".json"
    cache_filepath = os.path.join("cache", cache_filename)

    if not no_cache and os.path.exists(cache_filepath):
        if (time.time() - os.path.getmtime(cache_filepath)) < CACHE_DURATION:
            print(f"Loading report from cache: {cache_filepath}")
            try:
                with open(cache_filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache file: {e}. Re-running report.")

    data_client = ga4_client.get_data_client()
    if not data_client: return None

    try:
        module_path = f"reports.{report_module_name}"
        report_module = importlib.import_module(module_path)
        print(f"\nRunning '{report_module_name.replace('_', ' ').title()}' report for property ID: {property_id} (API call)")
        report_data = report_module.run_report(property_id, data_client, start_date, end_date)
        
        if report_data:
            os.makedirs("cache", exist_ok=True)
            with open(cache_filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f)
            print(f"Report saved to cache: {cache_filepath}")
        
        return report_data

    except ImportError as e:
        print(f"Error: Could not import report module '{report_module_name}'. {e}")
        return None
    except Exception as e:
        print(f"An error occurred while running the report: {e}")
        return None

def run_report_for_all_properties(no_cache=False):
    """Runs the Session Source / Medium report for all available properties and aggregates the data."""
    print("Running Session Source / Medium report for all available properties...")
    
    all_properties = get_all_properties()
    if not all_properties:
        print("No properties found to run the report on.")
        return

    start_date, end_date, _, verbose_date_range_str = get_selected_date_range(cli_all_months=True)
    
    output_function, _ = get_selected_output_format("csv_html")

    aggregated_rows = []
    headers = []

    for prop_info in all_properties:
        print(f"\n--- Running report for: {prop_info['display_name']} ---")
        report_data = run_dynamic_report('session_source_medium_report', prop_info['property_id'], start_date, end_date, no_cache=no_cache)
        
        if report_data and report_data['rows']:
            if not headers: headers = ["property_name"] + report_data['headers']
            for row in report_data['rows']: aggregated_rows.append([prop_info['display_name']] + row)
        else:
            print(f"No data returned for {prop_info['display_name']}.")

    if not aggregated_rows:
        print("No data to generate a report.")
        return

    aggregated_report_data = {"title": "Session Source / Medium Report (All Properties)", "headers": headers, "rows": aggregated_rows, "date_range": verbose_date_range_str}
    selected_property_info = {"display_name": "All-Properties", "property_id": "all"}
    output_function(aggregated_report_data, selected_property_info, start_date, end_date)
    print("\nFinished running aggregated report for all properties.")

def run_all_reports_for_property(selected_property_info, cli_start_date=None, cli_end_date=None, cli_all_months=False, cli_output_format=None, no_cache=False):
    """Runs all available reports for a single property."""
    start_date, end_date, _, verbose_date_range_str = get_selected_date_range(cli_start_date, cli_end_date, cli_all_months)

    if start_date == "all-months":
        available_reports = get_available_reports()
        for report_key, report_info in sorted(available_reports.items(), key=lambda item: item[1]['name']):
            if report_info['module'] == 'all': continue
            run_monthly_reports_for_property(selected_property_info, report_info, cli_output_format, no_cache)
        return

    print(f"\nRunning all available reports for property: {selected_property_info['display_name']}")
    available_reports = get_available_reports()
    if not available_reports:
        print("No reports found in the 'reports' directory.")
        return

    output_function, _ = get_selected_output_format(cli_output_format)
    
    for report_key, report_info in sorted(available_reports.items(), key=lambda item: item[1]['name']):
        if report_info['module'] == 'all': continue
        
        report_data = run_dynamic_report(report_info['module'], selected_property_info['property_id'], start_date, end_date, no_cache=no_cache)
        
        if report_data:
            report_data['date_range'] = verbose_date_range_str
            output_function(report_data, selected_property_info, start_date, end_date)
        else:
            print(f"Failed to generate data for report: {report_info['name']}")

    print(f"\nFinished running all reports for {selected_property_info['display_name']}.")

def get_next_action():
    """Waits for a single key press and returns the selected action."""
    print("Enter your choice: ", end="", flush=True)
    if sys.platform == "win32":
        while True:
            char = msvcrt.getch()
            if char == b'\x1b': return "Q"
            if char.upper() in [b'R', b'C', b'Q']:
                print(char.decode().upper())
                return char.decode().upper()
    else:
        while True:
            next_action = input().upper()
            if next_action in ["R", "C", "Q"]: return next_action
            else: print("Invalid choice. Please enter R, C, or Q.")

def main():
    """Main function to orchestrate the interactive reporting session."""
    _cleanup_cache()

    parser = argparse.ArgumentParser(description='Run Google Analytics 4 reports.')
    parser.add_argument('-p', '--property-id', type=str, help='Specify a GA4 property ID.')
    parser.add_argument('-r', '--report', type=str, help='Specify the report name.')
    parser.add_argument('-sd', '--start-date', type=str, help='Start date in YYYY-MM-DD format.')
    parser.add_argument('-ed', '--end-date', type=str, help='End date in YYYY-MM-DD format.')
    parser.add_argument('--all-months', action='store_true', help='Run report for all available months.')
    parser.add_argument('-o', '--output-format', type=str, help='Output format (console, txt, csv, html, csv_html).')
    parser.add_argument('--run-all-properties-report', action='store_true', help='Run Session Source/Medium report for all properties.')
    parser.add_argument('--run-all-reports', action='store_true', help='Run all reports for a single property.')
    parser.add_argument('--no-cache', action='store_true', help='Ignore cached results.')
    args = parser.parse_args()

    if args.run_all_properties_report:
        run_report_for_all_properties(no_cache=args.no_cache)
        return

    if args.run_all_reports:
        if not args.property_id:
            print("Error: --run-all-reports requires a --property-id.")
            return
        selected_property_info = get_property_info_by_id(args.property_id)
        if not selected_property_info: return
        run_all_reports_for_property(selected_property_info, args.start_date, args.end_date, args.all_months, args.output_format, args.no_cache)
        return

    while True:
        selected_property_info = get_selected_property(args.property_id) if not 'selected_property_info' in locals() else locals()['selected_property_info']
        if not selected_property_info: break

        while True:
            available_reports = get_available_reports()
            selected_report = get_selected_report(available_reports, args.report)
            if not selected_report: break

            if selected_report['module'] == 'all':
                run_all_reports_for_property(selected_property_info, args.start_date, args.end_date, args.all_months, args.output_format, args.no_cache)
                if args.property_id: return
            else:
                start_date, end_date, _, verbose_date_range_str = get_selected_date_range(args.start_date, args.end_date, args.all_months)
                if start_date == "all-months":
                    run_monthly_reports_for_property(selected_property_info, selected_report, args.output_format, args.no_cache)
                else:
                    report_data = run_dynamic_report(selected_report['module'], selected_property_info['property_id'], start_date, end_date, no_cache=args.no_cache)
                    if report_data:
                        report_data['date_range'] = verbose_date_range_str
                        output_function, _ = get_selected_output_format(args.output_format)
                        output_function(report_data, selected_property_info, start_date, end_date)
                    else:
                        print("Report generation failed.")

            if args.property_id and args.report: return

            print("\n(R)un another report, (C)hange property, (Q)uit")
            next_action = get_next_action()
            if next_action == "C": break
            if next_action == "Q": print("\nExiting..."); return
        
        if args.property_id: return


if __name__ == "__main__":
    main()
