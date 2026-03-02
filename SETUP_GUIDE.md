# GA4 API Explorer Setup Guide

This guide will walk you through the process of setting up the necessary credentials to use the Google Analytics 4 (GA4) API.

## 1. Enable the Google Analytics Data API

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Select your project from the project dropdown menu at the top of the page, or create a new one if you don't have one already.
3.  In the navigation menu, go to **APIs & Services > Enabled APIs & services**.
4.  Click on **+ ENABLE APIS AND SERVICES**.
5.  Search for "Google Analytics Data API" and "Google Analytics Admin API".
6.  Enable both APIs for your project.

## 2. Create a Service Account

A service account is a special type of Google account intended to represent a non-human user that needs to authenticate and be authorized to access data in Google APIs.

1.  In the Google Cloud Console, navigate to **IAM & Admin > Service Accounts**.
2.  Click **+ CREATE SERVICE ACCOUNT**.
3.  Fill in the service account details:
    *   **Service account name:** A descriptive name, e.g., "ga4-api-explorer".
    *   **Service account ID:** This will be automatically generated based on the name.
    *   **Description:** A brief description of what this service account will be used for.
4.  Click **CREATE AND CONTINUE**.
5.  **Grant this service account access to the project** by adding the "Viewer" role. This allows the service account to see the GA4 properties within the project.
6.  Click **CONTINUE**.
7.  You can skip the "Grant users access to this service account" step for now. Click **DONE**.

## 3. Grant Service Account Access in Google Analytics

You now need to grant the newly created service account access to your Google Analytics 4 properties. You can do this at either the **Account level** (granting access to all properties within that account) or at the individual **Property level**. Granting access at the Account level is recommended if you want the service account to access all properties within it.

### To Grant Access at the Account Level (Recommended)
1.  Go to your [Google Analytics](https://analytics.google.com/) account.
2.  Navigate to the **Admin** section.
3.  In the "Account" column (the leftmost column), click on **Account Access Management**.
4.  Click the **+** button to add a new user.
5.  In the "Email address" field, paste the email address of the service account you created in the previous step (you can find this in the "Service Accounts" section of the Google Cloud Console).
6.  Select the desired permissions. **"Viewer"** is sufficient for reading data.
7.  Click **Add**.

### To Grant Access at the Property Level
1.  Go to your [Google Analytics](https://analytics.google.com/) account.
2.  Navigate to the **Admin** section of your GA4 property.
3.  In the "Property" column, click on **Property Access Management**.
4.  Click the **+** button to add a new user.
5.  In the "Email address" field, paste the email address of the service account.
6.  Select the desired permissions. **"Viewer"** is sufficient.
7.  Click **Add**.

## 4. Set Up Your Local Environment

1.  Find the JSON key file you downloaded in the previous step.
2.  Rename the file to `client_secret.json`.
3.  Move the `client_secret.json` file into the `config` directory of this project.

That's it! The scripts in this project are configured to automatically find and use this file.

You are now ready to run the Python scripts in this project to interact with the GA4 API.
