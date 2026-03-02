from google.analytics.admin_v1alpha.types import ListPropertiesRequest
import ga4_client
import output_manager # Import our new output manager
import os
import sys
import importlib.util
from datetime import datetime, timedelta, date
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

def get_selected_date_range(cli_start_date=None, cli_end_date=None):
    """Presents a menu to select a date range and returns start_date, end_date, a display string, and a verbose date range string."""
    today = date.today()

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
    }
    return output_formats_map.get(output_format_str.lower())

def get_selected_output_format(cli_output_format=None):
    """Presents an interactive menu to select the output format."""
    if cli_output_format:
        output_func = _get_output_function_from_args(cli_output_format)
        if output_func:
            print(f"Using output format from command-line: {cli_output_format}")
            return output_func
        else:
            print(f"Invalid output format '{cli_output_format}' provided via command-line. Falling back to interactive selection...")

    # Define options with their display names and corresponding functions
    output_options_raw = [
        ("Print to Console", output_manager.print_to_console),
        ("Save as CSV", output_manager.save_to_csv),
        ("Save as CSV & HTML (Default)", output_manager.save_to_csv_and_html),
        ("Save as HTML", output_manager.save_to_html),
    ]

    # Sort options alphabetically by display name
    output_options_raw.sort(key=lambda x: x[0])

    # Create a numbered menu and a mapping for selection
    output_functions_map = {}
    print("\nSelect Output Format:")
    for i, (display_name, func) in enumerate(output_options_raw, 1):
        output_functions_map[str(i)] = func
        print(f"{i}. {display_name}")

    while True:
        selection = input("Enter the number for the output format (press Enter for default 'Save as CSV & HTML'): ")
        if not selection: # User pressed Enter, use default
            return output_manager.save_to_csv_and_html
        if selection in output_functions_map:
            return output_functions_map[selection]
        else:
            print("Invalid selection. Please enter a valid number.")

def run_dynamic_report(report_module_name, property_id, start_date, end_date, no_cache=False):
    """Dynamically imports and runs a report module for a given date range, with caching."""
    
    # Generate cache key
    cache_key_data = {
        "property_id": property_id,
        "report_module": report_module_name,
        "start_date": start_date,
        "end_date": end_date
    }
    cache_key_string = json.dumps(cache_key_data, sort_keys=True)
    cache_filename = hashlib.md5(cache_key_string.encode('utf-8')).hexdigest() + ".json"
    cache_filepath = os.path.join("cache", cache_filename)

    # Check cache
    if not no_cache and os.path.exists(cache_filepath):
        file_mtime = os.path.getmtime(cache_filepath)
        if (time.time() - file_mtime) < CACHE_DURATION:
            print(f"Loading report from cache: {cache_filepath}")
            try:
                with open(cache_filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache file: {e}. Re-running report.")

    # If not in cache or cache is stale, run report
    data_client = ga4_client.get_data_client()
    if not data_client:
        return None

    try:
        module_path = f"reports.{report_module_name}"
        report_module = importlib.import_module(module_path)
        print(f"\nRunning '{report_module_name.replace('_', ' ').title()}' report for property ID: {property_id} (API call)")
        report_data = report_module.run_report(property_id, data_client, start_date, end_date)
        
        # Save to cache if report ran successfully
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

    # Use default date range (Last Calendar Month)
    start_date, end_date, _, verbose_date_range_str = get_selected_date_range()
    
    # Use default output format (Save as CSV & HTML)
    output_function = output_manager.save_to_csv_and_html

    aggregated_rows = []
    headers = []

    for prop_info in all_properties:
        print(f"\n--- Running report for: {prop_info['display_name']} ---")
        report_data = run_dynamic_report(
            'session_source_medium_report',
            prop_info['property_id'],
            start_date,
            end_date,
            no_cache=no_cache
        )
        
        if report_data and report_data['rows']:
            # Set headers from the first successful report
            if not headers:
                headers = ["property_name"] + report_data['headers']

            # Add property name to each row
            for row in report_data['rows']:
                aggregated_rows.append([prop_info['display_name']] + row)
        else:
            print(f"No data returned for {prop_info['display_name']}.")

    if not aggregated_rows:
        print("No data to generate a report.")
        return

    # Create a single report_data dictionary with the aggregated data
    aggregated_report_data = {
        "title": "Session Source / Medium Report (All Properties)",
        "headers": headers,
        "rows": aggregated_rows,
        "date_range": verbose_date_range_str,
    }

    # Create a generic selected_property_info for the output filename
    selected_property_info = {
        "display_name": "All-Properties",
        "property_id": "all"
    }

    output_function(aggregated_report_data, selected_property_info, start_date, end_date)

    print("\nFinished running aggregated report for all properties.")

def run_all_reports_for_property(selected_property_info, cli_start_date=None, cli_end_date=None, cli_output_format=None, no_cache=False):
    """Runs all available reports for a single property."""
    print(f"\nRunning all available reports for property: {selected_property_info['display_name']}")

    available_reports = get_available_reports()
    if not available_reports:
        print("No reports found in the 'reports' directory.")
        return

    # Get date range and output format once for all reports
    start_date, end_date, _, verbose_date_range_str = get_selected_date_range(cli_start_date, cli_end_date)
    output_function = get_selected_output_format(cli_output_format)
    
    # Loop through all available reports and run them
    for report_key, report_info in sorted(available_reports.items(), key=lambda item: item[1]['name']):
        if report_info['module'] == 'all': continue # Skip the 'All Reports' placeholder
        
        report_data = run_dynamic_report(
            report_info['module'],
            selected_property_info['property_id'],
            start_date,
            end_date,
            no_cache=no_cache
        )
        
        if report_data:
            report_data['date_range'] = verbose_date_range_str
            output_function(report_data, selected_property_info, start_date, end_date)
        else:
            print(f"Failed to generate data for report: {report_info['name']}")

    print(f"\nFinished running all reports for {selected_property_info['display_name']}.")

def get_next_action():
    """Waits for a single key press and returns the selected action."""
    print("Enter your choice: ", end="", flush=True)
    
    # For Windows, use msvcrt to capture single key presses
    if sys.platform == "win32":
        while True:
            char = msvcrt.getch()
            # Esc key pressed
            if char == b'\x1b':
                return "Q"
            # R, C, Q keys (case-insensitive)
            if char.upper() in [b'R', b'C', b'Q']:
                print(char.decode().upper()) # Echo the character
                return char.decode().upper()
    else:
        # For other OSes, fall back to standard input
        while True:
            next_action = input().upper()
            if next_action in ["R", "C", "Q"]:
                return next_action
            else:
                print("Invalid choice. Please enter R, C, or Q.")

def main():
    """Main function to orchestrate the interactive reporting session."""
    _cleanup_cache() # Clean up stale cache files at the start of each session

    parser = argparse.ArgumentParser(description='Run Google Analytics 4 reports.')
    parser.add_argument('-p', '--property-id', type=str, help='Specify a GA4 property ID to run reports non-interactively.')
    parser.add_argument('-r', '--report', type=str, help='Specify the report name (e.g., "top_cities_report") to run non-interactively.')
    parser.add_argument('-sd', '--start-date', type=str, help='Specify the start date for the report in YYYY-MM-DD format.')
    parser.add_argument('-ed', '--end-date', type=str, help='Specify the end date for the report in YYYY-MM-DD format.')
    parser.add_argument('-o', '--output-format', type=str, choices=['console', 'csv', 'html', 'csv_html'], help='Specify the output format (console, csv, html, csv_html) for non-interactive mode.')
    parser.add_argument('--run-all-properties-report', action='store_true', help='Run the Session Source / Medium report for all available properties.')
    parser.add_argument('--run-all-reports', action='store_true', help='Run all available reports for a single specified property.')
    parser.add_argument('--no-cache', action='store_true', help='Force a fresh run of the report, ignoring any cached results.')
    args = parser.parse_args()

    if args.run_all_properties_report:
        run_report_for_all_properties(no_cache=args.no_cache)
        return

    # Handle the new --run-all-reports argument
    if args.run_all_reports:
        if not args.property_id:
            print("Error: --run-all-reports requires a --property-id to be specified.")
            return

        selected_property_info = get_property_info_by_id(args.property_id)
        if not selected_property_info:
            print(f"Error: Invalid or inaccessible property ID '{args.property_id}'.")
            return
            
        run_all_reports_for_property(
            selected_property_info,
            cli_start_date=args.start_date,
            cli_end_date=args.end_date,
            cli_output_format=args.output_format,
            no_cache=args.no_cache
        )
        return

    while True: # Main loop for selecting properties
        # 1. Select Property (interactive or via command-line arg)
        selected_property_info = None
        if args.property_id:
            print(f"Attempting to use property ID from command-line: {args.property_id}")
            selected_property_info = get_property_info_by_id(args.property_id)
            if not selected_property_info:
                print("Invalid or inaccessible property ID provided via command-line. Falling back to interactive selection...")
                # Clear args.property_id to force interactive mode
                args.property_id = None 
        
        if not args.property_id: # If still no property from command line or it was invalid
            selected_property_info = get_selected_property()

        if not selected_property_info:
            break # Exit if no property is selected or found

        while True: # Nested loop for running reports on the selected property
            # 2. Discover and Select Report (interactive or via command-line arg)
            available_reports = get_available_reports()
            if not available_reports:
                print("No reports found in the 'reports' directory.")
                break # Go back to property selection
            
            selected_report = None
            if args.report:
                selected_report = _get_report_by_name(args.report)
                if not selected_report:
                    print(f"Invalid report name '{args.report}' provided via command-line. Falling back to interactive selection...")
                    args.report = None
            
            if not args.report: # If no report from command line or it was invalid
                selected_report = get_selected_report(available_reports)

            if not selected_report:
                break # Exit this loop if no report selected

            # Handle running all reports
            if selected_report['module'] == 'all':
                run_all_reports_for_property(
                    selected_property_info,
                    cli_start_date=args.start_date,
                    cli_end_date=args.end_date,
                    cli_output_format=args.output_format,
                    no_cache=args.no_cache
                )
                # After running all reports, decide what to do next
                if args.property_id: # If in non-interactive mode, exit
                    print("Completed running all reports in non-interactive mode. Exiting.")
                    return
                # In interactive mode, ask the user what to do next
                print("\nWhat would you like to do next?")
                print("(C)hange property")
                print("(Q)uit or press Esc")
                
                # Simplified next action for this context
                while True:
                    next_action = input("Enter your choice: ").upper()
                    if next_action in ["C", "Q"]:
                        break
                    else:
                        print("Invalid choice. Please enter C or Q.")
                
                if next_action == "C":
                    break # Break inner loop to change property
                elif next_action == "Q":
                    print("\nExiting...")
                    return # Exit script
            
            # 3. Select Date Range (interactive or via command-line arg)
            start_date, end_date, friendly_date_range_str, verbose_date_range_str = None, None, None, None
            if args.start_date or args.end_date: # If any date arg is provided, try to use them
                date_args = _get_dates_from_args(args.start_date, args.end_date)
                if date_args:
                    start_date, end_date, friendly_date_range_str, verbose_date_range_str = date_args
                else:
                    print("Invalid date range provided via command-line. Falling back to interactive selection...")
            
            if not start_date: # If no dates from command line or they were invalid
                start_date, end_date, friendly_date_range_str, verbose_date_range_str = get_selected_date_range()

            # 4. Run the selected report
            report_data = run_dynamic_report(
                selected_report['module'], 
                selected_property_info['property_id'], 
                start_date, 
                end_date,
                no_cache=args.no_cache
            )
            
            if not report_data:
                print("Report generation failed.")
                # Ask user what to do next even if report fails
            else:
                # Add verbose date range string to report data for output
                report_data['date_range'] = verbose_date_range_str
                # 5. Select Output Format and process the data (interactive or via command-line arg)
                output_function = None
                if args.output_format:
                    output_function = _get_output_function_from_args(args.output_format)
                    if not output_function:
                        print(f"Invalid output format '{args.output_format}' provided via command-line. Falling back to interactive selection...")
                
                if not output_function: # If no output from command line or it was invalid
                    output_function = get_selected_output_format()
                
                # Pass all necessary info to the output function
                output_function(report_data, selected_property_info, start_date, end_date) 

            # 6. Ask user what to do next - skip if all args provided (fully non-interactive)
            if args.property_id and args.report and (args.start_date or args.end_date) and args.output_format:
                print("All arguments provided via command-line. Exiting non-interactive mode.")
                return # Exit the entire script

            print("\nWhat would you like to do next?")
            print("(R)un another report for this property")
            print("(C)hange property")
            print("(Q)uit or press Esc")
            
            next_action = get_next_action()
            
            if next_action == "R":
                continue # Continue the inner loop
            elif next_action == "C":
                break # Break the inner loop to go to property selection
            elif next_action == "Q":
                print("\nExiting...")
                return # Exit the entire script
        
        # This part is reached if user chose to change property
        print("\nReturning to property selection...")


if __name__ == "__main__":
    main()
