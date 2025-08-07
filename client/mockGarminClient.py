# mocks.py
import os, numpy as np, pandas as pd
from datetime import datetime, timedelta
from typing import List
from utilities import constants as _ct

_RNG = np.random.default_rng(7)
import logging

class MockGarminClient:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,  # or DEBUG for more verbose output
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

    def login(self, fetch: bool):
        # no-op
        return None

    def fetch_activities(self, start: datetime, end: datetime, fetch: bool) -> List[dict]:
        days = pd.date_range(start, end, freq="D")
        out = []
        for d in days:
            # 0–2 activities/day
            for _ in range(_RNG.integers(0, 3)):
                atype = _RNG.choice(
                    ["run", "cycling", "other", "strength_training", "walking", "swimming"],
                    p=[0.45, 0.2, 0.15, 0.1, 0.07, 0.03]
                )
                dur_min = max(10, float(_RNG.normal(50 if atype == "run" else 40, 12)))
                avg_hr = int(np.clip(_RNG.normal(140, 15), 95, 180))
                max_hr = int(np.clip(avg_hr + _RNG.normal(35, 6), 110, 205))
                # make zone seconds summing ~ duration
                zsplit = _zone_split(avg_hr, dur_min)
                start_iso = (d + timedelta(minutes=int(_RNG.integers(360, 1200)))).strftime("%Y-%m-%dT%H:%M:%S")

                out.append({
                    _ct.NAME: f"{atype.capitalize()} {_RNG.integers(1_000, 99_999)}",
                    _ct.START_TIME_GMT: start_iso,
                    _ct.DURATION: dur_min * 60.0,  # seconds
                    _ct.MAXHR: max_hr,
                    _ct.AVERAGEHR: avg_hr,
                    _ct.MAXSPEED: float(max(2.0, _RNG.normal(5.0, 1.0))),
                    _ct.AVERAGESPEED: float(max(1.5, _RNG.normal(3.5, 0.8))),
                    _ct.HR_TIME_Z1: zsplit[0], _ct.HR_TIME_Z2: zsplit[1],
                    _ct.HR_TIME_Z3: zsplit[2], _ct.HR_TIME_Z4: zsplit[3],
                    _ct.HR_TIME_Z5: zsplit[4],
                    _ct.ACTIVITY_TYPE: {_ct.TYPEKEY: atype},  # matches your process_activities
                    "activityId": int(_RNG.integers(10_000_000, 99_999_999)),
                })
        return out

    def get_vo2max_and_training_status_series(self, start: datetime, end: datetime, fetch: bool) -> List[dict]:
        dates = pd.date_range(start, end, freq="D")
        n = len(dates)
        # synthetic load & metrics
        baseline = 1400
        drift = np.cumsum(_RNG.normal(0, 10, n))     # smaller std for smooth changes
        noise = _RNG.normal(0, 50, n)                # mild daily variability
        load = np.clip(baseline + drift + noise, 1000, 1600)
        # proportions for each step: 40%, 30%, 15%, 15%
        i1 = int(0.40 * n)
        i2 = int(0.70 * n)
        i3 = int(0.85 * n)

        # VO2: 50 → 51 → 51.5 → 52 (very slow, fixed steps)
        vo2 = np.empty(n, dtype=float)
        vo2[:i1]      = 50.0
        vo2[i1:i2]    = 51.0
        vo2[i2:i3]    = 51.5
        vo2[i3:]      = 52.0
        vo2 += _RNG.normal(0, 0.03, n)           # tiny jitter
        vo2 = np.clip(vo2, 50.0, 52.0)

        # RHR: slow step-up too (tweak levels as you like)
        rhr = np.empty(n, dtype=float)
        rhr[:i1]      = 48.0
        rhr[i1:i2]    = 48.5
        rhr[i2:i3]    = 49.0
        rhr[i3:]      = 49.5
        rhr += _RNG.normal(0, 0.2, n)            # tiny jitter
        rhr = np.clip(rhr, 42.0, 70.0)

        # tunnel bounds around load for plotting
        lmin = np.clip(load - 150, 900, 1400)
        lmax = np.clip(load + 150, 1100, 1700)
        main_status = 4
        alt_statuses = [5, 6]
        out = []
        for i, dt in enumerate(dates):
            if _RNG.random() < 0.1:  # 10 % of times
                status = _RNG.choice(alt_statuses)
            else:
               status = main_status
            out.append({
                "date": dt.strftime("%Y-%m-%d"),
                "vo2Max": float(vo2[i]),
                "fitnessAge": None,
                "weeklyTrainingLoad": float(load[i]),
                "trainingStatus": status,
                "loadMin": float(lmin[i]),
                "loadMax": float(lmax[i]),
                "fitnessTrend": None,
                "sport": "running",
                "deviceId": "MOCK",
                "restingHR": float(rhr[i]),
            })
        return out


def _zone_split(avg_hr: int, dur_min: float):
    # heuristic based on avg HR; returns **seconds**
    if avg_hr < 120:
        p = [0.7, 0.2, 0.08, 0.02, 0.0]
    elif avg_hr < 135:
        p = [0.45, 0.35, 0.15, 0.05, 0.0]
    elif avg_hr < 150:
        p = [0.25, 0.35, 0.25, 0.12, 0.03]
    elif avg_hr < 165:
        p = [0.15, 0.25, 0.30, 0.22, 0.08]
    else:
        p = [0.05, 0.15, 0.25, 0.32, 0.23]
    secs = (np.array(p) * dur_min * 60.0).astype(float)
    return secs.tolist()
