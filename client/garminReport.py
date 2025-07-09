###  File to generate a garmin analysis report for a user
import os
import sys

import pandas as pd
import pwinput
from client.garminConnect import GarminClient, plot_average_time_in_zones, plot_activity_breakdown, plot_training_load_with_metric, plot_zones_and_hr, get_weekly
from utilities.emailSender import EmailSender
from utilities import constants as ct
from datetime import datetime, timedelta
from typing import List

def get_date_input(prompt: str, default:str, date_format: str = "%Y-%m-%d") -> datetime:
    """
    Function to process user input and ensure return is in the right format
    :param prompt:
    :param date_format:
    :return:
    """
    while True:
        user_input = input(prompt).strip() or default
        try:
            return datetime.strptime(user_input, date_format)
        except Exception as e:
            print(
                f"Encountered error: {e} while processing date input. Please ensure date is in the {date_format} format.")

def run_report():
    ## 1. Ask user for input
    default_username = os.getenv(ct.GARMINCONNECT_MAIL)
    default_password = os.getenv(ct.GARMINCONNECT_PASSWORD)
    default_sd = "2025-06-15"
    default_ed = datetime.today().strftime("%Y-%m-%d")
    garminUsername = input("Please enter your garmin username: ") or default_username
    garminPassword = pwinput.pwinput("Please enter your garmin password: ")
    if not garminPassword:
        garminPassword = default_password
    garminClient = GarminClient(username=garminUsername, password=garminPassword)

    ## 2. Get user garmin data
    fetch = True
    garminClient.login(fetch=fetch)
    startDate = get_date_input("Please enter start date for analysis: (Year-month-date): ", default=default_sd)
    endDate = get_date_input("Please enter end date for analysis: (Year-month-end): ", default=default_ed)
    vo2_series = garminClient.get_vo2max_and_training_status_series(startDate, endDate, fetch=fetch)
    vo2_series = pd.DataFrame(vo2_series)
    activities = garminClient.fetch_activities(startDate, endDate, fetch=fetch)
    activities = garminClient.process_activities(activities)
    activitiesDf = pd.DataFrame(activities)
    time_in_zones_fig = plot_average_time_in_zones(activities)
    activity_breakdown_fig = plot_activity_breakdown(activities)
    vo2_series_df = pd.DataFrame(vo2_series)
    vo2_against_load = plot_training_load_with_metric(vo2_series_df, metric="vo2Max", metric_label="Vo2 Max", metric_color="darkgreen", output_path="assets/garmin_images/vo2_vs_trainingload.png")
    rhr_against_load = plot_training_load_with_metric(vo2_series_df, metric="restingHR", metric_label="Resting HR", metric_color="crimson", output_path="assets/garmin_images/rhr_vs_trainingload.png")
    weekly = get_weekly(vo2_series_df, activitiesDf)
    zones_and_hr_trends = plot_zones_and_hr(weekly)

    ## 3. Send Email
    sendToMail = input("Please enter the email you want to receive the report to: ")
    if not sendToMail:
        garminClient.logger.info(f"No mail entered ... will now exit without sending the report.")
        sys.exit()
    mailSender = EmailSender(os.getenv('GMAIL_EMAIL'))
    htmlBody = weekly.tail(4).to_html(float_format="%.2f", border=0, justify="center", classes="dataframe")
    mailSender.send_email(sendToMail, "Garmin Report", "Please see your garmin report", htmlBody,
                          [time_in_zones_fig, activity_breakdown_fig, vo2_against_load, rhr_against_load, zones_and_hr_trends])


if __name__ == '__main__':
    run_report()
