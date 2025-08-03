###  File to generate a garmin analysis report for a user
import os
import sys

import pandas as pd
import pwinput
from client.garminConnect import GarminClient, plot_average_time_in_zones, plot_activity_breakdown, \
    plot_training_load_with_metric, plot_zones_and_hr, get_weekly
from utilities.emailSender import EmailSender
from utilities import constants as ct
from datetime import datetime, timedelta
from agents.baseAgent import UserProfile
from agents.runningCoachAgent import AICoach
from typing import List


def get_date_input(prompt: str, default: str, date_format: str = "%Y-%m-%d") -> datetime:
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
    ## Ask user for input
    default_username = os.getenv(ct.GARMINCONNECT_MAIL)
    default_password = os.getenv(ct.GARMINCONNECT_PASSWORD)
    default_sd = "2025-06-15"
    default_ed = datetime.today().strftime("%Y-%m-%d")
    garminUsername = input("Please enter your garmin username: ") or default_username
    garminPassword = pwinput.pwinput("Please enter your garmin password: ")
    if not garminPassword:
        garminPassword = default_password
    garminClient = GarminClient(username=garminUsername, password=garminPassword)

    #  Mock user profile for now
    userProfile = UserProfile(age=25, height=171, weight=67, sex='M', ambitions='Hyrox Open Podium and overall high fitness',
                              current_job='Quantitative Developer for Investment Bank')

    ## Get user garmin data
    fetch = False
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
    vo2_against_load = plot_training_load_with_metric(vo2_series_df, metric="vo2Max", metric_label="Vo2 Max",
                                                      metric_color="darkgreen",
                                                      output_path="assets/garmin_images/vo2_vs_trainingload.png")
    rhr_against_load = plot_training_load_with_metric(vo2_series_df, metric="restingHR", metric_label="Resting HR",
                                                      metric_color="crimson",
                                                      output_path="assets/garmin_images/rhr_vs_trainingload.png")
    weekly = get_weekly(vo2_series_df, activitiesDf)
    zones_and_hr_trends = plot_zones_and_hr(weekly)

    ##  AI Coach
    aiCaoch = AICoach(model=ct.GROK3_MINI, temperature=0.7, max_tokens=5000)
    garminClient.logger.info(
        f"Have created the AI Agent - will now pass user input training data and profile and ask for feedback")
    feedback = aiCaoch.generate_feedback(weekly, userProfile)
    garminClient.logger.info(f"See below feedback Returned")
    garminClient.logger.info(feedback)

    # after you get `feedback` back:
    feedbackHtml = f"""
    <h2>Coach Feedback</h2>
    <p><strong>Feedback:</strong> {feedback.feedback}</p>
    <p><strong>Reasoning:</strong> {feedback.reasoning}</p>
    <p><strong>Confidence:</strong> {feedback.confidence:.1f}%</p>
    """

    ##  Send Email
    sendToMail = input("Please enter the email you want to receive the report to: ")
    if not sendToMail:
        garminClient.logger.info(f"No mail entered ... will now exit without sending the report.")
        sys.exit()
    mailSender = EmailSender(os.getenv('GMAIL_EMAIL'))
    htmlTable = weekly.tail(4).to_html(float_format="%.2f", border=0, justify="center", classes="dataframe")
    htmlBody = (
            "<h1>Your Garmin Report</h1>"
            + htmlTable
            + feedbackHtml
    )

    mailSender.send_email(sendToMail, f"Garmin Report - {startDate} - {endDate}",
                          "Below is your garmin report for the requested period.", htmlBody,
                          [time_in_zones_fig, activity_breakdown_fig, vo2_against_load, rhr_against_load,
                           zones_and_hr_trends])


if __name__ == '__main__':
    run_report()
