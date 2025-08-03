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
import argparse


def prompt_if_interactive(prompt, default=None):
    # only prompt if stdin is a tty
    if sys.stdin.isatty():
        return input(f"{prompt}{' [' + default + ']' if default else ''}: ").strip() or default
    # non-interactive → just return default (or None)
    return default


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


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--interactive', action='store_true', help='force interactive prompts')
    p.add_argument('--username')
    p.add_argument('--password')
    p.add_argument('--start-date')
    p.add_argument('--end-date')
    p.add_argument('--to-email')
    p.add_argument('--fetch')
    p.add_argument('--run_from_terminal')
    return p.parse_args()


def run_report(fetch=True):
    args = parse_args()
    username = args.username or  prompt_if_interactive("Garmin username: ") or os.getenv('GARMINCONNECT_MAIL')
    password = args.password or  (
        pwinput.pwinput("Garmin password: ") if sys.stdin.isatty() else None) or os.getenv('GARMINCONNECT_PASSWORD')
    if not username or not password:
        raise RuntimeError(f"Missing Garming credentials: username={bool(username)}, password={bool(password)}")
    # Dates
    default_sd = datetime(2025, 1, 1)
    default_ed = datetime.today()
    sd = args.start_date or (get_date_input("Please enter start date for analysis: (Year-month-date)",
                                            default=default_sd) if sys.stdin.isatty() else default_sd)
    ed = args.end_date or (get_date_input("Please enter the end date for analysis: (Year-month-date)",
                                          default=default_ed) if sys.stdin.isatty() else default_ed)
    fetch = args.fetch or fetch
    # Recipient
    sendToMail = prompt_if_interactive("Send report to email: ") or os.getenv('REPORT_RECIPIENT')

    garminClient = GarminClient(username=username, password=password)

    #  Mock user profile for now
    age =  prompt_if_interactive('User age: ') or os.getenv('USER_AGE')
    height = prompt_if_interactive('User Height: ') or os.getenv('USER_HEIGHT')
    weight =  prompt_if_interactive('User Weight: ') or os.getenv('USER_WEIGHT')
    sex =prompt_if_interactive('User sex: ') or os.getenv('USER_SEX')
    ambitions =  prompt_if_interactive('User ambitions: ') or os.getenv('USER_AMBITIONS')
    current_job = prompt_if_interactive('User current job: ') or os.getenv('CURRENT_JOB')
    userProfile = UserProfile(age=age, height=height, weight=weight, sex=sex, current_job=current_job,
                              ambitions=ambitions)

    ## Get user garmin data
    garminClient.login(fetch=fetch)
    vo2_series = garminClient.get_vo2max_and_training_status_series(sd, ed, fetch=fetch)
    vo2_series = pd.DataFrame(vo2_series)
    activities = garminClient.fetch_activities(sd, ed, fetch=fetch)
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
    # only plot last 8 weeks
    zones_and_hr_trends = plot_zones_and_hr(weekly.tail(8))

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

    mailSender.send_email(sendToMail, f"Garmin Report - {sd} - {ed}",
                          "Below is your garmin report for the requested period.", htmlBody,
                          [time_in_zones_fig, activity_breakdown_fig, vo2_against_load, rhr_against_load,
                           zones_and_hr_trends])


if __name__ == '__main__':
    run_report(fetch=True)
