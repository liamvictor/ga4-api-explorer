import csv
import os
import time
import re
import datetime
import json

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
    <table id="reportTable" class="table table-striped table-bordered">
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

def _markdown_to_html(text):
    """A simple markdown to HTML converter for the explanation text."""
    if not text:
        return ""
    
    lines = text.strip().split('\n')
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Convert bold syntax (**text**) to <strong>text</strong>
        line = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', line)

        if line.startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line[2:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            html_lines.append(f'<p>{line}</p>')
            
    if in_list:
        html_lines.append('</ul>')
        
    return ''.join(html_lines)

def print_to_console(report_data, selected_property_info=None, start_date=None, end_date=None): # Match signature
    """Prints the report data in a formatted table to the console."""
    if not report_data or not report_data.get("rows"):
        print("No data to display.")
        return

    headers = report_data.get("headers", [])
    rows = report_data.get("rows", [])
    title = report_data.get("title", "Report")
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

    explanation = report_data.get("explanation")
    if explanation:
        print(f"\n{explanation}")

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


def _save_historical_report_to_html(report_data, property_info, start_date, end_date):
    """Saves a historical report to an HTML file."""
    if not property_info or 'display_name' not in property_info or 'property_id' not in property_info:
        print("Error: Property information is incomplete. Cannot save HTML report.")
        return

    property_name = property_info['display_name']
    property_id = property_info['property_id']
    title = report_data.get('title', 'GA4 Report')
    
    # Sanitize property_name for filename
    sanitized_property_name = "".join(c for c in property_name if c.isalnum() or c in (' ', '_')).rstrip()
    
    filename = f"{title.replace(' ', '_')}_{sanitized_property_name}_{start_date}_to_{end_date}.html"
    
    # Ensure the 'output' directory exists
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)

    try:
        from jinja2 import Environment, FileSystemLoader
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('historical_report_template.html')
        
        html_content = template.render(
            title=title,
            property_name=property_name,
            property_id=property_id,
            date_range=report_data.get('date_range', f'{start_date} to {end_date}'),
            table_data=report_data.get('table_data', {}),
            chart_data=report_data.get('chart_data', {}),
            months=report_data.get('months', []),
            incomplete_months=report_data.get('incomplete_months', {}),
            explanation=report_data.get('explanation', '')
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"Report successfully saved to: {filepath}")

    except ImportError:
        print("Jinja2 is not installed. Please install it using: pip install Jinja2")
    except Exception as e:
        print(f"An error occurred while generating the HTML report: {e}")


def save_to_html(report_data, selected_property_info, start_date, end_date):
    """Saves the report data to an HTML file in a property-specific subdirectory within 'output'."""
    if 'table_data' in report_data and 'chart_data' in report_data:
        _save_historical_report_to_html(report_data, selected_property_info, start_date, end_date)
        return

    # Specialized Trend Report with Charting
    if report_data.get("special_type") == "channel_trend":
        sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
        property_output_dir = os.path.join("output", sanitized_property_name)
        os.makedirs(property_output_dir, exist_ok=True)
        filename = f"channel-performance-trends-{start_date}-to-{end_date}.html"
        filepath = os.path.join(property_output_dir, filename)
        
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template('channel_trend_template.html')
            
            html_content = template.render(
                report_title=report_data.get("title"),
                property_display_name=selected_property_info['display_name'],
                property_id=selected_property_info['property_id'],
                date_range=report_data.get("date_range", f"{start_date} to {end_date}"),
                channels=report_data.get("channels"),
                months=report_data.get("months"),
                json_data=json.dumps(report_data.get("json_data"))
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Successfully saved specialized trend report to {filepath}")
            return
        except Exception as e:
            print(f"Error generating specialized HTML report: {e}. Falling back to standard format.")

    # Specialized Top Channels Comparison Report
    if report_data.get("special_type") == "top_channels_trend":
        sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
        property_output_dir = os.path.join("output", sanitized_property_name)
        os.makedirs(property_output_dir, exist_ok=True)
        filename = f"top-channels-comparison-{start_date}-to-{end_date}.html"
        filepath = os.path.join(property_output_dir, filename)
        
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template('top_channels_trend_template.html')
            
            html_content = template.render(
                report_title=report_data.get("title"),
                property_display_name=selected_property_info['display_name'],
                property_id=selected_property_info['property_id'],
                date_range=report_data.get("date_range", f"{start_date} to {end_date}"),
                channels=report_data.get("channels"),
                months=report_data.get("months"),
                json_data=json.dumps(report_data.get("json_data"))
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Successfully saved specialized top channels report to {filepath}")
            return
        except Exception as e:
            print(f"Error generating specialized HTML report: {e}. Falling back to standard format.")

    # Specialized Top Campaign Daily Trend Report
    if report_data.get("special_type") == "top_campaign_daily_trend":
        sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
        property_output_dir = os.path.join("output", sanitized_property_name)
        os.makedirs(property_output_dir, exist_ok=True)
        
        report_title = report_data.get("title", "Top Campaign Daily Trend")
        sanitized_report_title = _sanitize_name(report_title)
        filename = f"{sanitized_report_title}-{start_date}-to-{end_date}.html"
        filepath = os.path.join(property_output_dir, filename)
        
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template('top_campaign_daily_trend_template.html')
            
            # Convert explanation from Markdown to HTML
            explanation = report_data.get("explanation", "")
            explanation_html = _markdown_to_html(explanation)
            
            html_content = template.render(
                report_title=report_data.get("title"),
                property_display_name=selected_property_info['display_name'],
                property_id=selected_property_info['property_id'],
                date_range=report_data.get("date_range", f"{start_date} to {end_date}"),
                campaign_names=report_data.get("campaign_names"),
                dates=report_data.get("dates"),
                json_data=json.dumps(report_data.get("json_data")),
                explanation_html=explanation_html,
                now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Successfully saved specialized daily trend report to {filepath}")
            return
        except Exception as e:
            print(f"Error generating specialized HTML report: {e}. Falling back to standard format.")

    # Specialized Channel Traffic by Hour Report
    if report_data.get("special_type") == "channel_traffic_by_hour":
        sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
        property_output_dir = os.path.join("output", sanitized_property_name)
        os.makedirs(property_output_dir, exist_ok=True)
        
        report_title = report_data.get("title", "Channel Traffic by Hour")
        sanitized_report_title = _sanitize_name(report_title)
        filename = f"{sanitized_report_title}-{start_date}-to-{end_date}.html"
        filepath = os.path.join(property_output_dir, filename)
        
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template('channel_traffic_by_hour_template.html')
            
            # Convert explanation from Markdown to HTML
            explanation = report_data.get("explanation", "")
            explanation_html = _markdown_to_html(explanation)

            # Pre-calculate tables for static HTML display
            hours = report_data.get("hours")
            channels = report_data.get("channels")
            json_data = report_data.get("json_data")
            category_label = report_data.get("category_label", "Channel")
            time_label = report_data.get("time_label", "Hour")

            # 1. Totals Table
            totals_headers = [category_label, "Sessions"]
            totals_rows = []
            grand_total = 0
            for ch in channels:
                ch_total = 0
                for h in hours:
                    # Try both padded and unpadded hour strings (for hourly reports)
                    h_unpadded = str(int(h)) if h.isdigit() else h
                    h_data = json_data.get(h, json_data.get(h_unpadded, {}))
                    ch_total += h_data.get(ch, {}).get('sessions', 0)
                totals_rows.append([ch, ch_total])
                grand_total += ch_total
            totals_html = _generate_table_html(totals_headers, totals_rows)
            # Add grand total to the bottom of the rendered HTML
            totals_html = totals_html.replace("</tbody>", f'<tr class="table-secondary fw-bold"><td>Grand Total</td><td>{_format_value(grand_total)}</td></tr></tbody>')

            # 2. Detail Table (Hourly or Daily)
            detail_headers = [time_label] + channels + ["Total"]
            detail_rows = []
            ch_column_totals = {ch: 0 for ch in channels}
            for h in hours:
                # Format time label: add :00 only if it looks like an hour (0-23)
                display_time = f"{h}:00" if (h.isdigit() and len(h) <= 2) else h
                row = [display_time]
                h_total = 0
                h_unpadded = str(int(h)) if h.isdigit() else h
                h_data = json_data.get(h, json_data.get(h_unpadded, {}))
                
                for ch in channels:
                    val = h_data.get(ch, {}).get('sessions', 0)
                    row.append(val)
                    h_total += val
                    ch_column_totals[ch] += val
                row.append(h_total)
                detail_rows.append(row)
            
            detail_html = _generate_table_html(detail_headers, detail_rows)
            # Add totals row to the bottom
            footer_cells = ["<td>Total</td>"]
            for ch in channels:
                footer_cells.append(f"<td>{_format_value(ch_column_totals[ch])}</td>")
            footer_cells.append(f"<td>{_format_value(grand_total)}</td>")
            detail_html = detail_html.replace("</tbody>", f'<tr class="table-secondary fw-bold">{"".join(footer_cells)}</tr></tbody>')

            html_content = template.render(
                report_title=report_data.get("title"),
                property_display_name=selected_property_info['display_name'],
                property_id=selected_property_info['property_id'],
                date_range=report_data.get("date_range", f"{start_date} to {end_date}"),
                hours=hours,
                channels=channels,
                category_label=category_label,
                time_label=time_label,
                json_data=json.dumps(json_data), # Keep for Chart.js
                explanation_html=explanation_html,
                totals_html=totals_html,
                hourly_html=detail_html
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Successfully saved specialized report to {filepath}")
            return
        except Exception as e:
            print(f"Error generating specialized HTML report: {e}. Falling back to standard format.")

    # Specialized Top Campaign Daily Trend (used for Countries too)
    if report_data.get("special_type") == "top_campaign_daily_trend":
        sanitized_property_name = _sanitize_name(selected_property_info['display_name'])
        property_output_dir = os.path.join("output", sanitized_property_name)
        os.makedirs(property_output_dir, exist_ok=True)
        
        report_title = report_data.get("title", "Daily Trend")
        sanitized_report_title = _sanitize_name(report_title)
        filename = f"{sanitized_report_title}-{start_date}-to-{end_date}.html"
        filepath = os.path.join(property_output_dir, filename)
        
        try:
            from jinja2 import Environment, FileSystemLoader
            env = Environment(loader=FileSystemLoader('templates'))
            template = env.get_template('top_campaign_daily_trend_template.html')
            
            explanation_html = _markdown_to_html(report_data.get("explanation", ""))
            
            html_content = template.render(
                report_title=report_data.get("title"),
                property_display_name=selected_property_info['display_name'],
                date_range=f"{start_date} to {end_date}",
                campaign_names=report_data.get("campaign_names"),
                dates=report_data.get("dates"),
                json_data=json.dumps(report_data.get("json_data")),
                explanation_html=explanation_html,
                now=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Successfully saved specialized daily trend report to {filepath}")
            return
        except Exception as e:
            print(f"Error generating specialized daily trend HTML report: {e}. Falling back to standard format.")

    if not report_data or not report_data.get("rows"):
        print("No data to save.")
        return
    if not selected_property_info or not start_date or not end_date:
        print("Error: Property information or date range missing for HTML output.")
        return

    headers = report_data.get("headers", [])
    rows = report_data.get("rows", [])
    report_title = report_data.get("title", "Report")

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

    # Convert explanation from Markdown to HTML
    explanation = report_data.get("explanation", "")
    explanation_html = _markdown_to_html(explanation)

    # Replace placeholders
    date_range_str = report_data.get("date_range", f"{start_date} to {end_date}")
    html_content = html_content.replace("{{ report_title }}", report_title)
    html_content = html_content.replace("{{ property_display_name }}", selected_property_info['display_name'])
    html_content = html_content.replace("{{ date_range }}", date_range_str)
    html_content = html_content.replace("<!-- REPORT_TABLE_PLACEHOLDER -->", table_html)
    html_content = html_content.replace("<!-- REPORT_EXPLANATION_PLACEHOLDER -->", explanation_html)

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

def save_report_to_file(report_data, filename):
    """Saves a formatted report to a single text file in the 'output' directory."""
    if not report_data or not report_data.get("rows"):
        print(f"  -> No data to save for {filename}.")
        return

    # Ensure output directory exists
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    headers = report_data.get("headers", [])
    rows = report_data.get("rows", [])
    title = report_data.get("title", "Report")
    date_range_str = report_data.get("date_range", "")

    # Format numbers for display
    formatted_rows = []
    for row in rows:
        formatted_rows.append([_format_value(cell) for cell in row])

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in formatted_rows:
        for i, cell in enumerate(row):
            if i < len(col_widths) and len(str(cell)) > col_widths[i]:
                col_widths[i] = len(str(cell))

    # Build the report string
    report_string = []
    report_string.append(f"--- {title} ---")
    if date_range_str:
        report_string.append(f"--- Date Range: {date_range_str} ---")
    report_string.append("\n")

    # Header line
    header_line = " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers)))
    report_string.append(header_line)
    report_string.append("-" * len(header_line))

    # Row lines
    for row in formatted_rows:
        row_line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row)))
        report_string.append(row_line)
    
    report_string.append("-" * len(header_line))

    explanation = report_data.get("explanation")
    if explanation:
        report_string.append(f"\n{explanation}")

    # Write to file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(report_string))
    except Exception as e:
        print(f"  -> Error saving text file: {e}")
