import csv
import os
import time
import re
import datetime

def _sanitize_name(name):
    """Converts a string to a sanitized, hyphenated, lowercase format for filenames/directories."""
    name = name.lower()
    # Replace one or more dots, whitespace, or other non-alphanumeric characters with a single hyphen
    name = re.sub(r'[^a-z0-9]+', '-', name)
    # Remove any leading/trailing hyphens
    name = name.strip('-')
    return name

def _format_value(value):
    """Tries to format a value as an integer with commas, otherwise returns the original value."""
    try:
        # Convert to float first to handle string representations of numbers like "1234.0"
        return f"{int(float(value)):,}"
    except (ValueError, TypeError):
        return value

def _generate_table_html(headers, rows):
    """Generates an HTML table string from headers and rows, with number formatting."""
    
    # Format numbers in rows
    formatted_rows = []
    for row in rows:
        formatted_rows.append([_format_value(cell) for cell in row])
        
    table_html = """
    <table class="table table-striped table-bordered">
        <thead>
            <tr>
                {}
            </tr>
        </thead>
        <tbody>
            {}
        </tbody>
    </table>
    """.format(
        ''.join(f'<th>{header}</th>' for header in headers),
        ''.join(f'<tr>{"".join(f"<td>{cell}</td>" for cell in row)}</tr>' for row in formatted_rows)
    )
    return table_html

def print_to_console(report_data, selected_property_info=None, start_date=None, end_date=None): # Match signature
    """Prints the report data in a formatted table to the console."""
    if not report_data or not report_data.get("rows"):
        print("No data to display.")
        return

    headers = report_data.get("headers", [])
    rows = report_data.get("rows", [])
    title = report_data.get("title", "Report")
    description = report_data.get("description") 
    detailed_description = report_data.get("detailed_description")
    date_range_str = report_data.get("date_range", "")

    # Format numbers for display
    formatted_rows = []
    for row in rows:
        formatted_rows.append([_format_value(cell) for cell in row])

    print(f"\n--- {title} ---")
    if selected_property_info:
        print(f"--- Property: {selected_property_info['display_name']} ({selected_property_info['property_id']}) ---")
    if date_range_str:
        print(f"--- Date Range: {date_range_str} ---")
    
    # Print the description if it exists
    if description:
        print(f"\n{description}\n")
    if detailed_description:
        print(f"{detailed_description}\n")

    # Calculate column widths using formatted rows
    col_widths = [len(h) for h in headers]
    for row in formatted_rows:
        for i, cell in enumerate(row):
            if i < len(col_widths) and len(str(cell)) > col_widths[i]:
                col_widths[i] = len(str(cell)) 

    # Print headers
    header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
    print(header_line)
    print("-" * len(header_line))

    # Print formatted rows
    for row in formatted_rows:
        row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        print(row_line)
    
    print("-" * len(header_line))

def save_to_csv(report_data, selected_property_info, start_date, end_date):
    """Saves the report data to a CSV file in a property-specific subdirectory within 'output'."""
    if not report_data or not report_data.get("rows"):
        print("No data to save.")
        return
    if not selected_property_info or not start_date or not end_date:
        print("Error: Property information or date range missing for CSV output.")
        return

    headers = report_data.get("headers", [])
    rows = report_data.get("rows", [])
    report_title = report_data.get("title", "report")
    
    # Sanitize names according to user preferences
    sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
    sanitized_report_title = _sanitize_name(report_title)

    # Create property-specific directory
    property_output_dir = os.path.join("output", sanitized_property_name)
    os.makedirs(property_output_dir, exist_ok=True) # Create if not exists

    filename = f"{sanitized_report_title}-{start_date}-to-{end_date}.csv"
    filepath = os.path.join(property_output_dir, filename)

    try:
        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"Successfully saved report to {filepath}")
    except Exception as e:
        print(f"Error saving CSV file: {e}")


def save_to_html(report_data, selected_property_info, start_date, end_date):
    """Saves the report data to an HTML file in a property-specific subdirectory within 'output'."""
    if not report_data or not report_data.get("rows"):
        print("No data to save.")
        return
    if not selected_property_info or not start_date or not end_date:
        print("Error: Property information or date range missing for HTML output.")
        return

    headers = report_data.get("headers", [])
    rows = report_data.get("rows", [])
    report_title = report_data.get("title", "Report")
    description = report_data.get("description")
    detailed_description = report_data.get("detailed_description")

    # Sanitize names according to user preferences
    sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
    sanitized_report_title = _sanitize_name(report_title)

    # Create property-specific directory
    property_output_dir = os.path.join("output", sanitized_property_name)
    os.makedirs(property_output_dir, exist_ok=True) # Create if not exists

    filename = f"{sanitized_report_title}-{start_date}-to-{end_date}.html"
    filepath = os.path.join(property_output_dir, filename)

    # Load HTML template
    template_path = os.path.join(os.path.dirname(__file__), "templates", "html-report-template.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"Error: HTML template not found at {template_path}")
        return
    except Exception as e:
        print(f"Error loading HTML template: {e}")
        return

    # Generate table HTML
    table_html = _generate_table_html(headers, rows)
    
    # Generate collapsible details HTML
    details_html = ""
    if description:
        # Convert newline characters in detailed_description to <br> tags for HTML display
        detailed_desc_html = detailed_description.replace('\n', '<br>') if detailed_description else ""
        details_html = f"""
        <p>
            <button class="btn btn-secondary btn-sm" type="button" data-bs-toggle="collapse" data-bs-target="#reportDetails" aria-expanded="false" aria-controls="reportDetails">
                Show/Hide Details
            </button>
        </p>
        <div class="collapse" id="reportDetails">
            <div class="card card-body">
                <p class="mb-2">{description}</p>
                <hr>
                <p class="text-muted small mb-0" style="white-space: pre-wrap;">{detailed_desc_html}</p>
            </div>
        </div>
        """

    # Replace placeholders
    date_range_str = report_data.get("date_range", f"{start_date} to {end_date}")
    html_content = html_content.replace("{{ report_title }}", report_title)
    html_content = html_content.replace("{{ property_display_name }}", selected_property_info['display_name'])
    html_content = html_content.replace("{{ date_range }}", date_range_str)
    html_content = html_content.replace("<!-- COLLAPSIBLE_DETAILS_PLACEHOLDER -->", details_html)
    html_content = html_content.replace("<!-- REPORT_TABLE_PLACEHOLDER -->", table_html)

    try:
        with open(filepath, "w", encoding="utf-8") as htmlfile:
            htmlfile.write(html_content)
        print(f"Successfully saved report to {filepath}")
    except Exception as e:
        print(f"Error saving HTML file: {e}")

def save_to_csv_and_html(report_data, selected_property_info, start_date, end_date):
    """Saves the report data to both CSV and HTML files."""
    save_to_csv(report_data, selected_property_info, start_date, end_date)
    save_to_html(report_data, selected_property_info, start_date, end_date)
