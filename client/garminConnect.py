import matplotlib.pyplot as plt
from garminconnect import Garmin
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import os
from dataclasses import dataclass
from typing import List
from utilities import constants as _ct
import numpy as np
import seaborn as sns

sns.set_style('whitegrid')
from collections import Counter

load_dotenv()
from utilities.helpers import load_json_cache, build_cache_path, save_json_cache
import pandas as pd
import matplotlib.patches as mpatches
import matplotlib.dates as mdates


class GarminClient:
    """
    A client for interacting with the Garmin Connect API
    """

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = None
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,  # or DEBUG for more verbose output
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def login(self, fetch: bool):
        """
        Login to Garmin connect and initialise the client variable
        :return:
        """
        if not fetch:
            self.logger.info(
                f"Login function of the garmin client called with fetch= {fetch}. Returning None early to avoid too many requests ...")
            return None
        try:
            self.client = Garmin(self.username, self.password)
            self.client.login()
            self.logger.info("Successfully logged in to Garmin Connect!")
        except Exception as e:
            self.logger.error(f"Login failed with error: {e}")
            raise

    def logout(self):
        if self.client:
            self.client.logout()
            self.logger.info(f"Logged out successfully!")

    def get_user_metrics(self):
        try:
            metrics = self.client.get_user_metrics()
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to get user metrics with error: {e}")

    def get_training_status(self, date: datetime):
        try:
            training_status = self.client.get_training_status(date)
            return training_status
        except Exception as e:
            self.logger.error(f"Failed to retrieve training status with error: {e}")

    def get_rhr_data(self, date: datetime):
        try:
            rhr_data = self.client.get_rhr_day(date)
            return rhr_data
        except Exception as e:
            self.logger.error(f"Failed to retrieve training status with error: {e}")

    def get_vo2max_and_training_status_series(self, start: datetime, end: datetime, fetch: bool) -> List[dict]:
        """
        Retrieves VO2 max, fitness age, and training load/status across a date range.
        Returns a list of daily records with cleaned data.
        Fetch --
        """
        self.logger.info(f"Getting vo2 max and training status data for: {start} - {end}")
        cache_path = build_cache_path("vo2_max_and_load", start, end)
        cache = load_json_cache(cache_path)
        if cache and not fetch:
            self.logger.info(f"Find file in cache at: {cache_path}. Returning this instead")
            return cache
        date_range = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        status_series = []
        for dt in date_range:
            try:
                self.logger.info(f"Extracting training status and RHR data for date: {dt}")
                status_data = self.get_training_status(dt)
                rhr_data = self.get_rhr_data(dt)
                rhr_value = (rhr_data.get("allMetrics", {})
                             .get("metricsMap", {})
                             .get("WELLNESS_RESTING_HEART_RATE", [{}])[0]
                             .get("value", None))
                vo2_raw = status_data.get("mostRecentVO2Max", {}).get("generic", {})
                vo2_max = vo2_raw.get("vo2MaxPreciseValue")
                fitness_age = vo2_raw.get("fitnessAge")

                latest_status = status_data.get("mostRecentTrainingStatus", {}).get("latestTrainingStatusData", {})
                if not latest_status:
                    continue
                #  break below as only want to get the first one (hypothethically there could be multiple training devices)
                for _, ts in latest_status.items():
                    status_series.append({
                        "date": ts.get("calendarDate"),
                        "vo2Max": vo2_max,
                        "fitnessAge": fitness_age,
                        "weeklyTrainingLoad": ts.get("weeklyTrainingLoad"),
                        "trainingStatus": ts.get("trainingStatus"),
                        "loadMin": ts.get("loadTunnelMin"),
                        "loadMax": ts.get("loadTunnelMax"),
                        "fitnessTrend": ts.get("fitnessTrend"),
                        "sport": ts.get("sport"),
                        "deviceId": ts.get("deviceId"),
                        "restingHR": rhr_value
                    })
                    break
            except Exception as e:
                self.logger.warning(f"Error on {dt.date()}: {e}")
                continue

        save_json_cache(cache_path, status_series)
        self.logger.info(f"Saved to cache: {cache_path}")
        return status_series

    def fetch_activities(self, start: datetime, end: datetime, fetch: bool):
        try:
            cache_path = build_cache_path("garmin_activities", start, end)
            cache = load_json_cache(cache_path)
            #  as above -- even if something is in cache -- for testing we might want to fetch the data --> hence have the options
            if cache and not fetch:
                return cache
            start_date = start.date()
            end_date = end.date()
            batch = self.client.get_activities_by_date(
                start_date.isoformat(),
                end_date.isoformat(),
                activitytype=""  # to get al activities
            )
            self.logger.info(f"Fetched {len(batch)} activities")
            save_json_cache(cache_path, batch)
            return batch
        except Exception as e:
            self.logger.error(f" Failed to fetch activities with error: {e}")
            raise

    def process_activities(self, activities: List) -> List:
        garminActivities = []
        for activity in activities:
            garminActivity = GarminActivity(
                id=activity.get('activityId', 0),
                name=activity.get(_ct.NAME, "Unknown"),
                startDate=datetime.fromisoformat(activity.get(_ct.START_TIME_GMT, "1970-01-01T00:00:00")),
                duration=activity.get(_ct.DURATION, 0.0),
                max_hr=activity.get(_ct.MAXHR, 0),
                average_hr=activity.get(_ct.AVERAGEHR, 0),
                max_speed=activity.get(_ct.MAXSPEED, 0.0),  # Default to 0.0 if missing
                average_speed=activity.get(_ct.AVERAGESPEED, 0.0),  # Fix: access activity, default to 0.0
                time_in_zones=[
                    activity.get(_ct.HR_TIME_Z1, 0.0),
                    activity.get(_ct.HR_TIME_Z2, 0.0),
                    activity.get(_ct.HR_TIME_Z3, 0.0),
                    activity.get(_ct.HR_TIME_Z4, 0.0),
                    activity.get(_ct.HR_TIME_Z5, 0.0)
                ],
                activity_type=activity.get(_ct.ACTIVITY_TYPE, {}).get(_ct.TYPEKEY, 'unknown')
            )
            # Overwrite -- specific for my own case so far as I use 'other' when I am doing conditioning
            if garminActivity.activity_type == "other":
                garminActivity.activity_type = "Conditioning"
            garminActivities.append(garminActivity)
        return garminActivities


@dataclass
class GarminActivity:
    id: int
    name: str
    startDate: datetime
    duration: float
    max_hr: int
    activity_type: str
    average_hr: int
    max_speed: float
    average_speed: float
    time_in_zones: List[float]

    def time_in_zone(self, zone: int) -> float:
        """
        Returns the time spent in a specifc training zone
        :param zone:
        :return:
        """
        if 1 <= zone <= len(self.time_in_zones):
            return self.time_in_zones[zone - 1]  # index is 0 -> len-1
        raise ValueError("Please make sure the zone is between 1 and 5")


def run(fetch: bool = True, sd: datetime = datetime(2025, 6, 1), ed: datetime = datetime(2025, 7, 7)):
    """
    Main function to run the script
    :return:
    """
    garminconnection = GarminClient(username="vladmatei432@gmail.com", password=os.getenv(_ct.GARMINCONNECT_PASSWORD))
    garminconnection.login(fetch=fetch)
    useractivities = garminconnection.fetch_activities(start=sd, end=ed, fetch=fetch)
    garminActivities = garminconnection.process_activities(useractivities)
    garminActivitiesDf = pd.DataFrame(garminActivities)
    vo2data = garminconnection.get_vo2max_and_training_status_series(start=sd, end=ed, fetch=fetch)
    vo2data = pd.DataFrame(vo2data)
    plot_training_load_with_metric(vo2data, metric="vo2Max", metric_label="Vo2 Max", metric_color="darkgreen",
                                   output_path="assets/garmin_images/load_v02.png")
    plot_training_load_with_metric(vo2data, metric="restingHR", metric_label="Resting HR", metric_color="crimson",
                                   output_path="assets/garmin_images/load_rhr.png")
    weekly = get_weekly(vo2data, activitiesDf=garminActivitiesDf)
    weekly_corr(weekly)
    plot_zones_and_hr(weekly_df=weekly)


def get_weekly(vo2df, activitiesDf):
    # expand zones and compute week
    activitiesDf[_ct.ZONE_COLS] = activitiesDf["time_in_zones"].apply(pd.Series)
    activitiesDf["week"] = activitiesDf["startDate"].dt.to_period("W").apply(lambda r: r.start_time)
    # base aggregation
    weekly = activitiesDf.groupby("week").agg({
        "average_hr": "mean",
        "duration": "sum",
        "max_hr": "max",
        "max_speed": "max",
        **{col: "sum" for col in _ct.ZONE_COLS}
    })
    # count activities per type
    counts = (
        activitiesDf
        .groupby(["week", "activity_type"])
        .size()
        .unstack(fill_value=0)
    )
    # merge counts into weekly
    weekly = weekly.join(counts, how="left")
    # VO2 and resting HR
    vo2df["date"] = pd.to_datetime(vo2df["date"])
    vo2df["week"] = vo2df["date"].dt.to_period("W").apply(lambda r: r.start_time)
    vo2weekly = (
        vo2df.groupby("week")
        .agg({"vo2Max": "mean", "restingHR": "mean"})
    )
    # combine everything
    weekly = weekly.merge(vo2weekly, left_index=True, right_index=True, how="inner")
    return weekly


def weekly_corr(weeklyDf):
    #  plot correlations
    plt.figure(figsize=(10, 6))
    corr = weeklyDf.corr(numeric_only=True)
    sns.heatmap(corr, annot=True, cmap="coolwarm")
    plt.title("VO2 Max Correlation Matrix (aggregated weekly)")
    plt.tight_layout()
    plt.show()
    plot_zones_and_hr(weekly_df=weeklyDf)


def plot_zones_and_hr(weekly_df, output_path="assets/garmin_images/zones_vs_hr.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    zone_cols = _ct.ZONE_COLS
    colors = plt.get_cmap("tab10").colors[:5]
    fig, ax1 = plt.subplots(figsize=(20, 10))
    x = np.arange(len(weekly_df))
    width = 0.13
    # Plot side-by-side bars for zones
    for i, col in enumerate(zone_cols):
        bars = ax1.bar(x + i * width, (weekly_df[col] / 60), width=width, label=col.upper(), color=colors[i])
        for rect in bars:
            height = rect.get_height()
            ax1.text(
                rect.get_x() + rect.get_width() / 2,
                height + 1,
                f"{height:.0f}",
                ha="center",
                va="bottom",
                fontsize=8
            )
        ax1.set_ylabel("Time in Zones (mins)")
    ax1.set_xticks(x + (width * len(zone_cols) / 2))
    ax1.set_xticklabels([d.strftime("%b %d") for d in weekly_df.index])
    ax1.tick_params(axis="y")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.7)
    # HR lines (secondary axis)
    ax2 = ax1.twinx()
    ax2.plot(x + width * 2, weekly_df["average_hr"], color="red", marker="o", label="Avg HR")
    ax2.plot(x + width * 2, weekly_df["max_hr"], color="darkred", marker="x", linestyle="--", label="Max HR")
    ax2.set_ylabel("Heart Rate (bpm)")
    ax2.tick_params(axis="y", labelcolor="red")

    # Legend
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", bbox_to_anchor=(1.02, 1), title="Legend")

    ax1.set_title("Time in HR Zones vs Heart Rate (Weekly)")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return output_path


def get_date_range(activities: List[GarminActivity]):
    sds = [a.startDate for a in activities]
    return min(sds), max(sds)


def plot_average_time_in_zones(
        activities: List[GarminActivity],
        output_path: str = "assets/garmin_images/zone_distribution.png"
):
    # Create folder if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    zone_matrix = np.array([a.time_in_zones for a in activities])
    cumulative_zone_time = zone_matrix.sum(axis=0)
    cumulative_zone_time_hours = cumulative_zone_time / 3600.0  # convert mins to hours
    zones = [f"Zone {i + 1}" for i in range(len(cumulative_zone_time_hours))]
    sd, ed = get_date_range(activities)
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(zones, cumulative_zone_time_hours, color=_ct.colors)
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 0.1,
            f"{height:.1f}",
            ha='center',
            va='bottom',
            fontsize=8
        )
    ax.set_ylabel('Time in hours')
    ax.set_title(f"Time spent across each zone from: {sd.date()} to {ed.date()}")
    ax.grid(axis='y', alpha=0.6, linestyle='--')
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)

    return output_path


def plot_activity_breakdown(activities: List[GarminActivity],
                            output_path: str = "assets/garmin_images/activity_breakdown.png"):
    activity_types = [a.activity_type for a in activities]
    counts = Counter(activity_types)
    labels = list(counts.keys())
    sizes = list(counts.values())
    # ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=plt.cm.tab10.colors
    )

    ax.set_title("Distribution of Garmin Activities")

    # Save the figure before closing or showing
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches='tight')
    plt.close(fig)  # close to avoid duplicate plots if running in notebooks or scripts
    return output_path


def plot_training_load_with_metric(
        df: pd.DataFrame,
        metric: str = "vo2Max",  # or "restingHR"
        metric_label: str = "VO₂ Max",
        metric_color: str = "darkgreen",
        metric_style: dict = None,
        output_path: str = "assets/garmin_images/load_metric.png"
) -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    bar_colors = df["trainingStatus"].map(_ct.TRAINING_STATUS_COLORS).fillna("lightgrey")
    metric_style = metric_style or {"marker": "o", "linestyle": "-", "linewidth": 2}

    fig, ax1 = plt.subplots(figsize=(14, 8))
    ax1.bar(df.index, df["weeklyTrainingLoad"], color=bar_colors)
    ax1.plot(df.index, df["loadMin"], linestyle="-", color="maroon", label="Load Min")
    ax1.plot(df.index, df["loadMax"], linestyle="-", color="lime", label="Load Max")
    ax1.set_ylabel("Training Load", color="skyblue")
    ax1.tick_params(axis="y", labelcolor="skyblue")
    ax2 = ax1.twinx()
    ax2.plot(df.index, df[metric], color=metric_color, label=metric_label, **metric_style)
    ax2.set_ylabel(metric_label, color=metric_color)
    ax2.tick_params(axis="y", labelcolor=metric_color)
    ax1.set_title(f"{metric_label} vs Training Load")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.7)
    fig.autofmt_xdate()
    fig.tight_layout()
    # Legend
    status_handles = [
        mpatches.Patch(color=color, label=_ct.GARMIN_TRAINING_STATUS_MAP[status])
        for status, color in _ct.TRAINING_STATUS_COLORS.items()
        if status in df["trainingStatus"].unique()
    ]
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(handles=status_handles + h1 + h2, loc="upper left", title="Legend")
    fig.savefig(output_path, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    return output_path


if __name__ == '__main__':
    run(fetch=False)
