ALL_RACES = "All races"

WORK_LABELS = []
RUN_LABELS = []
RACE_ORDER_LABELS = []
ROXZONE_LABELS = []
ROXZONE_TIME = "roxzone_time"
RUN_TIME = "run_time"
WORK_TIME = "work_time"
TOTAL_TIME = "total_time"

STATIONS = ['SkiErg', 'SledPush', 'Sled Pull', 'Burpee Broad Jump', 'Rowing', 'Farmers Carry',
            'Sandbag Lunges', 'Wall Balls']
for i in range(1, 9):
    WORK_LABELS.append('work_' + str(i))
    RUN_LABELS.append('run_' + str(i))
    ROXZONE_LABELS.append('roxzone_' + str(i))
    RACE_ORDER_LABELS.append('run_' + str(i))
    RACE_ORDER_LABELS.append('work_' + str(i))
# options used in user-display and then filtering the dataframe
REQUEST_ALL_VALUES = 'all'

USER_RUN_1 = "user_run_1"
USER_RUN_2 = "user_run_2"
USER_RUN_3 = "user_run_3"
USER_RUN_4 = "user_run_4"
USER_RUN_5 = "user_run_5"
USER_RUN_6 = "user_run_6"
USER_RUN_7 = "user_run_7"
USER_RUN_8 = "user_run_8"

USER_SKI_ERG = "user_ski_erg"
USER_SLED_PUSH = "user_sled_push"
USER_SLED_PULL = "user_sled_pull"
USER_BURPEE_BROAD_JUMP = "user_burpee_broad_jump"
USER_ROW_ERG = "user_row_erg"
USER_FARMERS_CARRY = "user_farmers_carry"
USER_SANDBAG_LUNGES = "user_sandbag_lunges"
USER_WALL_BALLS = "user_wall_balls"


ALL_USER_INPUTS = [USER_RUN_1, USER_RUN_2, USER_RUN_3, USER_RUN_4, USER_RUN_5, USER_RUN_6, USER_RUN_7, USER_RUN_8,
                   USER_SKI_ERG, USER_SLED_PUSH, USER_SLED_PULL, USER_BURPEE_BROAD_JUMP, USER_ROW_ERG, USER_FARMERS_CARRY, USER_SANDBAG_LUNGES, USER_WALL_BALLS]

WORK_2_RUN = "work_to_run_ratio"
RUN_2_TOTAL = "run_to_total"
ROXZONE_2_TOTAL = "roxzone_to_total_ratio"
SLEDPULL_2_BURPEE = "sledpull_to_burpee_ratio"
RUN_1_TO_8 = "run1_to_run8_ratio"
RUN_2_TO_8 = "run2_to_run8_ratio"
SKI_ERG_TO_ROW_ERG = "ski_erg_to_row_ratio"
SLED_PUSH_2_PULL = "sled_push_to_sled_pull_ratio"
FIRST_HALF_TO_SECOND_HALF_RATIO = "first_half_to_second_half_ratio"
AVG_RUN_PACING_CHANGE = "avg_run_pacing_change"
STRENGTH_SCORE = "strength_score"
ENDURANCE_SCORE = "endurance_score"
SKI_ERG_TO_WALL_BALL = "ski_erg_to_wall_ball_ratio"
STRENGTH_TO_ENDURANCE_BALANCE = "strength_to_endurance_balance"

NETWORK_ANALYSIS_METRICS = [WORK_2_RUN, FIRST_HALF_TO_SECOND_HALF_RATIO, SLEDPULL_2_BURPEE,
                            SKI_ERG_TO_WALL_BALL]


### WEB SCRAPING CONSTANTS!
HTML_PARSER = 'html.parser'


### GARMIN CONNECT API CONSTANTS
HR_TIME_Z1 = "hrTimeInZone_1"
HR_TIME_Z2 = "hrTimeInZone_2"
HR_TIME_Z3 = "hrTimeInZone_3"
HR_TIME_Z4 = "hrTimeInZone_4"
HR_TIME_Z5 = "hrTimeInZone_5"
ZONE_COLS = ["time_in_z1", "time_in_z2", "time_in_z3", "time_in_z4", "time_in_z5"]
CALORIES = "calories"
AVERAGEHR = "averageHR"
NAME = "activityName"
START_TIME_GMT = "startTimeGMT"
DURATION = "duration"
MAXHR = "maxHR"
DISTANCE = "distance"
MAXSPEED = "maxSpeed"
AVERAGESPEED = "averageSpeed"
ACTIVITY_TYPE = "activityType"
TYPEKEY = "typeKey"
MINUTES_IN_HOUR = 60
#  blue to red -- increasing as heart rate increases
colors = ['#1f77b4', '#2ca02c', '#ffdd57', '#ff7f0e', '#d62728']

###  ENV VAR NAMES
OPENAI_API_KEY = "OPENAI_API_KEY"
GARMINCONNECT_PASSWORD = "GARMINCONNECT_PASSWORD"
GARMINCONNECT_MAIL = "GARMINCONNECT_MAIL"


#  STRAVA ACCESS
STRAVA_CLIENT_SECRET = "STRAVA_CLIENT_SECRET"
STRAVA_ACCESS_TOKEN = "STRAVA_ACCESS_TOKEN"
STRAVA_REFRESH_TOKEN = "STRAVA_REFRESH_TOKEN"
STRAVA_CLIENT_ID = "STRAVA_CLIENT_ID"
STRAVA_REDIRECT_URI = 'http://localhost:5000/callback'

#   LLM MODELS
GROK3_MINI = 'grok-3-mini'


TRAINING_STATUS_COLORS = {
    0: "grey", 1: "blue", 2: "cyan", 3: "orange",
    4: "gold", 5: "cornflowerblue", 6: "green", 7: "orangered"
}

# mapping created by analysis personal data
GARMIN_TRAINING_STATUS_MAP = {
    1: "Overreaching",
    2: "Unproductive",
    3: "Strained",
    4: "Maintaining",
    5: "Recovery",
    6: "Peaking",
    7: "Productive",
    8: "Detraining"
}
