# GA4 API Explorer

This project provides an interactive command-line interface to explore and generate reports from the Google Analytics 4 (GA4) API.

It allows you to interactively select a GA4 property, choose from a list of available reports, and generate the output in your console or as a CSV or HTML file.

## Project Structure

-   `run_report.py`: The main entry point for the application. This script orchestrates the user interaction, report discovery, and output generation. It also handles command-line arguments for non-interactive use.
-   `ga4_client.py`: Handles all authentication and Google API client instantiation. It finds the `client_secret.json` file and creates the necessary clients for the Admin and Data APIs.
-   `output_manager.py`: Contains functions to format and save report data into different formats (Console, CSV, HTML).
-   `list_properties.py`: A utility script to quickly list all accessible accounts and properties.
-   `settings.py`: Centralized configuration file for parameters like `CACHE_DURATION`.
-   `/config`: This directory should contain your `client_secret.json` service account key file.
-   `/cache`: Stores cached API responses to reduce redundant calls. This directory is ignored by Git.
-   `/output`: The default directory where generated CSV and HTML reports are saved. This directory is ignored by Git.
-   `/reports`: This directory contains all the available report modules. Each Python file in here is a self-contained report that can be discovered and run by `run_report.py`.
-   `/templates`: Contains HTML templates for report generation.

## Getting Started

### 1. Initial Setup

Follow the **[SETUP_GUIDE.md](SETUP_GUIDE.md)** to configure your Google Cloud project, create a service account, and download your `client_secret.json` key file.

### 2. Install Dependencies

It is highly recommended to use a Python virtual environment to keep your project dependencies isolated.

```bash
# Create a virtual environment (do this once)
py -m venv venv

# Activate the virtual environment
# On Windows (Git Bash):
source venv/Scripts/activate
# On Windows (PowerShell):
# .\venv\Scripts\activate

# Install the required libraries
pip install -r requirements.txt
```

### 3. Run the Reporter

The `run_report.py` script can be used in two main modes: interactive or non-interactive via command-line flags.

#### Interactive Mode

Once your virtual environment is activated, run the main script without any arguments:

```bash
py run_report.py
```

You will be guided through a series of interactive menus to:
1.  Select a GA4 property (accounts and properties are sorted).
2.  Select an available report (reports are sorted, e.g., "Top Cities Report", "Top Pages Report", "Session Source / Medium Report", or "All Reports").
3.  Select a date range (e.g., "Last Calendar Month", "Custom Date Range").
4.  Choose your desired output format (Console, CSV, HTML, CSV & HTML - options are sorted alphabetically).

The script will loop, allowing you to run multiple reports without restarting.

#### Non-Interactive Mode (Command-Line Flags)

You can bypass the interactive menus by providing arguments directly on the command line. If you provide some flags but not all, the script will prompt you interactively for the missing pieces.

**Available Flags:**

*   `-p`, `--property-id <PROPERTY_ID>`: Specify a GA4 property ID (e.g., `309716917`).
*   `-r`, `--report <REPORT_NAME>`: Specify the report module name (e.g., `top_cities_report`, `top_pages_report`, or `all` to run all reports).
*   `-sd`, `--start-date <YYYY-MM-DD>`: Specify the start date for the report.
*   `-ed`, `--end-date <YYYY-MM-DD>`: Specify the end date for the report.
*   `-o`, `--output-format <FORMAT>`: Specify the output format. Choices: `console`, `csv`, `html`, `csv_html`.
*   `--refresh-properties`: Force a refresh of the available GA4 properties list (bypasses cache).
*   `--run-all-properties-report`: Generates a single, aggregated Session Source / Medium report (totalUsers, newUsers) for all available properties.
*   `--run-all-reports`: Run all available reports for a single specified property. Requires `--property-id`.

**Examples:**

*   **Generate a single aggregated Session Source / Medium report for all properties:**
    ```bash
    py run_report.py --run-all-properties-report
    ```
*   **Run all reports for a specific property:**
    ```bash
    py run_report.py --run-all-reports -p 309716917
    ```

*   **Fully Non-Interactive Report (CSV for November 2025):**
    ```bash
    py run_report.py -p 309716917 -r top_cities_report -sd 2025-11-01 -ed 2025-11-30 -o csv
    ```
*   **Generate an HTML report for "Top Pages" using a property ID, then interactively choose date and output:**
    ```bash
    py run_report.py -p 309716917 -r top_pages_report
    ```
*   **Generate a console output for "Top Cities" for the last calendar month, interactively choosing the property:**
    ```bash
    py run_report.py -r top_cities_report -o console
    ```
    (Note: For date ranges like "Last Calendar Month", you would need to implement specific flags or use `--start-date` and `--end-date` with calculated values for full non-interactivity).

#### Available Reports

Here is a list of the reports currently available and what they provide:

*   **AI Traffic Acquisition Report:** Isolates and details traffic from known AI discovery tools and chatbots (e.g., ChatGPT, Gemini, Perplexity), helping you measure your visibility in generative search.
*   **Channel Performance Trends:** An interactive HTML report that uses the `yearMonth` dimension to track traffic and leads for each channel over time, featuring a built-in line chart.
*   **Channel Traffic by Hour Report:** Provides a breakdown of traffic distribution by hour of the day (00-23) for different acquisition channels, including sessions, active users, and engagement rate.
*   **Channel Overview Report:** Shows sessions, engaged sessions, engagement rate, active users, and leads, broken down by GA4 default channel groupings.
*   **Cohort Retention Report:** Measures how well you retain users over time, showing the percentage of users who return to your site in the weeks following their first visit.
*   **Device Type Historical Report:** A multi-month trend report for device categories, allowing you to see how your audience's technology mix is evolving over time.
*   **Device Type Report:** Provides a snapshot of performance (users, engagement, bounce rate) across different device categories.
*   **File Downloads Report:** Tracks downloads of various file types (PDF, DOCX, ZIP, etc.) to understand which resources are most popular with your users.
*   **High Engagement Pages Report:** Identifies pages with above-average engagement rates among those with significant traffic, highlighting your most "sticky" content.
*   **Landing Pages Report:** Lists the top 25 landing pages by sessions, including active users, new users, and engagement rate.
*   **Lead Quality by Channel Report:** Focuses on lead generation by combining total traffic (sessions, active users) with specific 'generate_lead' event counts and calculating a lead conversion rate for each channel.
*   **Low Engagement Pages Report:** Flags pages with below-average engagement despite having high traffic, identifying potential candidates for content or UX improvement.
*   **Monthly Acquisition Trend Report:** Provides a month-by-month view of total users, new users, sessions, conversions, and engagement rate, ideal for long-term trend analysis.
*   **New vs. Returning by Channel Report:** Breaks down the 'New vs. Returning' metrics by acquisition channel, showing which channels are better at bringing back users.
*   **New vs. Returning Engagement Report:** Compares engagement metrics (active users, sessions, duration) between new and returning visitors to see if you are successfully building an audience.
*   **Outbound Click Tracking Report:** Monitors clicks on links that lead users away from your site, helping you understand which external resources or partners you are driving traffic to.
*   **Screen Size Engagement Report:** Analyzes how different screen resolutions impact user engagement and bounce rate, highlighting potential responsive design issues.
*   **Session Source / Medium Report:** Details total users and new users based on the session's source and medium (e.g., "google / organic", "facebook / cpc").
*   **Top 5 Channels Comparison:** An interactive HTML report that ranks all channels by a selectable metric (Sessions, Leads, etc.) and trends the top 5 performers over time in a multi-line chart.
*   **Top 5 Cities by Active Users:** Ranks the top 5 cities based on active users, providing geographical insights into your audience.
*   **Top 25 Pages by Views:** Lists the top 25 most viewed pages on your site, indicating popular content.
*   **Traffic Acquisition Report:** A detailed report showing session default channel group, session source/medium, total users, new users, engaged sessions, engagement rate, and conversions, providing a comprehensive view of traffic quality.
*   **Traffic by Country and Hour Report:** Provides a breakdown of traffic distribution by hour of the day for different countries, including an interactive stacked bar chart.
*   **User Technology Report:** Provides insights into your audience's technology, including device category, operating system, browser, total users, engaged sessions, engagement rate, and bounce rate, useful for optimising compatibility and user experience.
*   **UTM Campaign Performance Report:** Details sessions, engaged sessions, and conversions for each of your UTM campaign names.
*   **UTM Full Content & Landing Page Report:** A highly cleaned report that strips common tracking parameters (gclid, msclkid, fbclid, Marketo/HubSpot IDs) from landing page URLs and re-aggregates the data for a consolidated view of campaign paths.

## How to Add a New Report

This project is designed to be easily extensible. To add a new report:

1.  Create a new Python file in the `/reports` directory (e.g., `my_new_report.py`).
2.  In that file, create a function named `run_report(property_id, data_client, start_date, end_date)`.
3.  Inside your function, use the `data_client` to build and run your `RunReportRequest`.
4.  Your function **must** return the data in a standardized dictionary format:

    ```python
    {
        "title": "My Awesome Report",
        "headers": ["Dimension 1", "Metric 1"],
        "rows": [
            ["Row 1 Dim", "Row 1 Met"],
            ["Row 2 Dim", "Row 2 Met"]
        ]
    }
    ```

That's it! The `run_report.py` script will automatically discover your new file and add it to the list of available reports.
