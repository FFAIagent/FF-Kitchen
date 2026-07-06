from dotenv import load_dotenv
import os

load_dotenv()

LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
BASE_TOKEN = os.environ.get("BASE_TOKEN", "HH0qb3myka5wPmsyInGlH6l3grd")
ECD_OPEN_ID = os.environ.get("ECD_OPEN_ID", "")
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "5001"))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Table IDs
DAPUR_TABLE = "tblpNqjumvstYOnj"
ROSTER_TABLE = "tblmeLyHTfAWvCm3"
CHAT_ID_TABLE = "tbl74dnKu2q6o8nQ"
BOBOT_TABLE      = "tblV0tT690HxKQwT"
ROLE_BOBOT_TABLE = "tbl6vvRtr7MXiZvR"
FEEDBACK_TABLE = "tblqT81eifqSvVqN"
REVISION_TABLE = "tblJwpd41jumoLk8"

# DAPUR field IDs
# NOTE: IDs below were updated 2026-07-06 after +form-questions-delete incident
# that deleted table fields. Fields were recreated; these are the new IDs.
F_STAGE_STATUS = "fldrfgbNwP"       # was fldNwVKYVH
F_APPROVAL_STATUS = "fld7NiL5es"    # was fld5ci4q1p
F_JOB_BRIEF_DATE = "flddtec2nd"     # was fldZvsitPG
F_FIRST_REVIEW_DATE = "fldBpnMhNy"  # was fldFcsIm6z
F_CLIENT_PRES_DATE = "fld5eCqBAP"   # was fldJQ9yhx0
F_SECOND_REVIEW_DATE = "fldYUT0V1Q" # was fldD9v82lp
F_THIRD_REVIEW_DATE = "fldXPjHJGc"  # was fldfIayvrI
F_NEXT_MILESTONE = "fld9s3v6yW"     # unchanged
F_ESTIMATED_HOURS = "fldO9ZtCop"    # was fldCBCnuQu
F_LAST_AGENT_SYNC = "fldMagUyrX"    # was fldOxFaNTn
F_BRIEF_ANNOUNCED = "fld7PcmubU"
F_JOB_BRIEF_REMINDER = "fldILWcToS"
F_FIRST_REVIEW_REMINDER = "fld8gu09fN"
F_CLIENT_PRES_REMINDER = "fldTECKIZi"
F_SECOND_REVIEW_REMINDER = "fldBOfqiLk"
F_POST_PRES_CARD_SENT = "fld4zp29Z7"
F_PM_PIC = "fldH4QtERK"
F_REVISION_COUNT = "fld2iY2pK1"     # was fld0dWannS
F_ACCOUNT_STATUS = "fldAPwgV9w"     # was fldxhKL0x0
F_ACCOUNT_PIC = "fldPJRWdSW"        # was fldylh3KLO
F_ACTUAL_HOURS = "fldG2NUYK6"       # was fldF3smRP5
F_AI_CONFIDENCE = "fldS8qx4F3"      # was fldcrCj6LT
F_ART_ASSIGNED = "fldEX4xvDL"
F_COPY_ASSIGNED = "fldqZGdn7Z"
F_GD_ASSIGNED = "fldUFuqlPa"
F_MOTION_ASSIGNED = "fldE5yJTeM"
F_STRATEGY_ASSIGNED = "fldc8ikiB1"
F_FA_ASSIGNED = "fldrM1lwar"
F_CREATIVE_TEAM = "fldjflMn2N"      # was fldDXtWPj0
F_JOB_TITLE = "fld6elh0J7"
F_CLIENT_LINK = "fld7MDHHJN"
F_BRIEF_LINK = "fldHwV7ihE"

# Per-role actual hours (agent writes when person reports via DM card)
F_ACTUAL_HOURS_ART      = "fldi1bk0Ho"
F_ACTUAL_HOURS_COPY     = "fldU3iD1Ot"
F_ACTUAL_HOURS_GD       = "fldR2bRm2T"
F_ACTUAL_HOURS_MOTION   = "fldaB9xREh"
F_ACTUAL_HOURS_STRATEGY = "flducMfZU7"
F_ACTUAL_HOURS_FA       = "fldURgIsWt"

# Dedup flags — agent sets True after sending the DM hours request
F_HOURS_REQUESTED_ART      = "fld0XTTJ28"
F_HOURS_REQUESTED_COPY     = "fld8bHSZag"
F_HOURS_REQUESTED_GD       = "flddX3V6xc"
F_HOURS_REQUESTED_MOTION   = "fldlEeAgkL"
F_HOURS_REQUESTED_STRATEGY = "fldRuiWJeM"
F_HOURS_REQUESTED_FA       = "fldTGPONZH"

# Maps discipline name → (actual_hours_field_id, hours_requested_flag_id)
DISCIPLINE_HOURS_FIELDS = {
    "Art":      (F_ACTUAL_HOURS_ART,      F_HOURS_REQUESTED_ART),
    "Copy":     (F_ACTUAL_HOURS_COPY,     F_HOURS_REQUESTED_COPY),
    "GD":       (F_ACTUAL_HOURS_GD,       F_HOURS_REQUESTED_GD),
    "Motion":   (F_ACTUAL_HOURS_MOTION,   F_HOURS_REQUESTED_MOTION),
    "Strategy": (F_ACTUAL_HOURS_STRATEGY, F_HOURS_REQUESTED_STRATEGY),
    "FA Artist":(F_ACTUAL_HOURS_FA,       F_HOURS_REQUESTED_FA),
}

# Team Roster field IDs
R_NAME = "fldLy0sa0j"
R_DISCIPLINE = "fld0eDLpb8"
R_ROLE = "fldVQkaiOa"
R_OPEN_ID = "fldFrxViIu"
R_LOAD_SCORE = "fldlKvk26j"   # was fldicOdUnJ (formula); now agent-written number (hours)
R_AVAILABLE = "fld6WLvIHk"
R_CURRENT_JOBS = "fldRbrkboh"
R_NEXT_DEADLINE = "fldaAvILjb"
R_SPEED_INDEX = "fldIQjTuZi"
R_FEEDBACK_COUNT = "fldOi3LAg8"
R_SPEED_TREND = "flds0X9F37"

# Creative Chat ID field IDs
C_CHAT_ID = "fldIZIhz9f"
C_TEAM_NAME = "fld2YQOPp6"

# FF Employees base (Flock People System — separate base)
EMPLOYEES_BASE_TOKEN = "SkrkbyaJwa3jxHsn619lG5a7g7f"
EMPLOYEES_TABLE = "tblNyIHGQb2jh0Iy"

# FF Employees field IDs
# Role Bobot field IDs
RB_JOB_TYPE      = "fldQgZFH6p"
RB_DISCIPLINE    = "flddOyrvPH"
RB_BASE_HOURS    = "fldXcbCf2T"
RB_SAMPLE_COUNT  = "fldYO2fYNX"
RB_CONFIDENCE    = "fldAuAfAch"
RB_LAST_CAL      = "fldPGv5ePz"
RB_REASONING     = "fldhsZJzCN"

E_NAME             = "fldvCb5Ttp"
E_OPEN_ID          = "fldiR5gXWt"
E_CURRENT_PROJECTS = "fldGU5CHbk"
E_ACTIVE_JOBS      = "fldCAAIm3o"
E_LOAD_SCORE       = "fldoicLIgp"   # hours — sum of Estimated Hours across active jobs
E_LAST_UPDATED     = "fldYwLot0z"

# Polling
POLLING_INTERVAL_MINUTES = 30
POLL_START_HOUR = 8   # 08:00 WIB
POLL_END_HOUR = 22    # 22:00 WIB
TIMEZONE = "Asia/Jakarta"

# Learning engine
FEEDBACK_CALIBRATION_THRESHOLD = 5  # calibrate after N new feedbacks
SUPERVISOR_ASK_DELAY_DAYS = 3
ECD_ASK_DELAY_DAYS = 7
MAX_FEEDBACK_QUESTIONS_PER_DAY = 2

# Stage Status values
STAGE_AWAITING_APPROVAL = "Awaiting Approval"
STAGE_BRIEFING_SCHEDULED = "Briefing Scheduled"
STAGE_FIRST_REVIEW = "1st Internal Review"
STAGE_SECOND_REVIEW = "2nd Internal Review"
STAGE_THIRD_REVIEW = "3rd Internal Review"
STAGE_CLIENT_PRES = "Client Presentation"
STAGE_CLIENT_REVISION = "Client Revision Received"
STAGE_ON_REVISION = "On Revision"
STAGE_REVISION_REVIEW = "Revision Internal Review"
STAGE_RE_PRESENTATION = "Re-Presentation"
STAGE_PRODUCTION = "Production"
STAGE_DONE = "Done"

INTERNAL_REVIEW_STAGES = {
    STAGE_FIRST_REVIEW, STAGE_SECOND_REVIEW,
    STAGE_THIRD_REVIEW, STAGE_REVISION_REVIEW
}

# Milestone reminder flags — maps stage to (date_field_id, flag_field_id)
MILESTONE_REMINDERS = {
    "Job Brief": (F_JOB_BRIEF_DATE, F_JOB_BRIEF_REMINDER),
    "1st Internal Review": (F_FIRST_REVIEW_DATE, F_FIRST_REVIEW_REMINDER),
    "Client Presentation": (F_CLIENT_PRES_DATE, F_CLIENT_PRES_REMINDER),
    "2nd Internal Review": (F_SECOND_REVIEW_DATE, F_SECOND_REVIEW_REMINDER),
}

# Maps DAPUR assignment field ID → Discipline name (for Role Bobot lookup)
ASSIGNMENT_FIELD_TO_DISCIPLINE = {
    F_ART_ASSIGNED:      "Art",
    F_COPY_ASSIGNED:     "Copy",
    F_GD_ASSIGNED:       "GD",
    F_MOTION_ASSIGNED:   "Motion",
    F_STRATEGY_ASSIGNED: "Strategy",
    F_FA_ASSIGNED:       "FA Artist",
}

# Complexity multipliers by Job Type
COMPLEXITY = {
    "Campaign": 1.5,
    "Tactical": 1.0,
    "Always-On": 0.8,
    "Pitch": 2.0,
    "Event": 1.3,
    "Production": 1.0,
    "Internal": 0.6,
}
