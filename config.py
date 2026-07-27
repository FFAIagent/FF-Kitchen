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
F_JOB_TYPE  = "fldoGTF6g5"         # Job Type (select: Campaign/Tactical/etc.)
F_CLIENT_LINK = "fld7MDHHJN"        # Client (link → Clients table) — agent-written
F_CLIENT_NAME = "fldzr8aih0"        # Client Name (select, form-filled) — source for bridge
F_BRIEF_LINK = "fldHwV7ihE"

# Deliverable pair fields (added 2026-07-08, Estimation Engine v2)
# Each slot = one select (Type) + one number (Qty). Up to 5 deliverables per job.
# Created via +form-questions-create so they appear on the Job Submission Form automatically.
F_DELIV_TYPE_1 = "fldrHoJ0Oy"
F_DELIV_QTY_1  = "fld70Lqvmr"
F_DELIV_TYPE_2 = "fldbg9TebR"
F_DELIV_QTY_2  = "flddrutb8Q"
F_DELIV_TYPE_3 = "fldO634Elc"
F_DELIV_QTY_3  = "fldOC09bj7"
F_DELIV_TYPE_4 = "fldZkr8w2S"
F_DELIV_QTY_4  = "fldfnkOcgg"
F_DELIV_TYPE_5 = "fldT54k98l"
F_DELIV_QTY_5  = "fldtKPrSAE"

# Parallel lists for easy iteration: zip(DELIV_TYPE_FIELDS, DELIV_QTY_FIELDS)
DELIV_TYPE_FIELDS = [F_DELIV_TYPE_1, F_DELIV_TYPE_2, F_DELIV_TYPE_3, F_DELIV_TYPE_4, F_DELIV_TYPE_5]
DELIV_QTY_FIELDS  = [F_DELIV_QTY_1,  F_DELIV_QTY_2,  F_DELIV_QTY_3,  F_DELIV_QTY_4,  F_DELIV_QTY_5]

# Per-discipline Estimated Hours fields in DAPUR (added 2026-07-08)
F_EST_HOURS_ART      = "fldLAXSE4w"
F_EST_HOURS_COPY     = "fldNpsF0TR"
F_EST_HOURS_GD       = "fldm6MYrqN"
F_EST_HOURS_MOTION   = "fldgYZd6U4"
F_EST_HOURS_STRATEGY = "fldHM18Z84"
F_EST_HOURS_FA       = "fldIclxCRS"

# Maps discipline name → F_EST_HOURS_* field ID
DISCIPLINE_EST_FIELDS = {
    "Art":       F_EST_HOURS_ART,
    "Copy":      F_EST_HOURS_COPY,
    "GD":        F_EST_HOURS_GD,
    "Motion":    F_EST_HOURS_MOTION,
    "Strategy":  F_EST_HOURS_STRATEGY,
    "FA Artist": F_EST_HOURS_FA,
}

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

# Creative Chat ID field IDs
C_CHAT_ID = "fldIZIhz9f"
C_TEAM_NAME = "fld2YQOPp6"

# FF Employees base (Flock People System — separate base)
EMPLOYEES_BASE_TOKEN = "SkrkbyaJwa3jxHsn619lG5a7g7f"
EMPLOYEES_TABLE = "tblNyIHGQb2jh0Iy"

# FF Employees field IDs
# Output Type Bobot field IDs (added 2026-07-08, Estimation Engine v2)
OB_NAME     = "fldRA8pYTD"   # Output type name (primary field)
OB_ART      = "fldG42IdmS"   # Base Hours (Art)
OB_COPY     = "fldxB6tgjC"   # Base Hours (Copy)
OB_GD       = "fldWA9URGF"   # Base Hours (GD)
OB_MOTION   = "fldd4Npqqj"   # Base Hours (Motion)
OB_STRATEGY = "fldZIbOpSy"   # Base Hours (Strategy)
OB_FA       = "fldsSJhuxZ"   # Base Hours (FA Artist)
OB_ACCOUNT  = "fldNwAkcJY"   # Base Hours (Account)

# Maps discipline name → OB_* field ID (for bobot reads + EMA writes)
DISCIPLINE_OB_FIELDS = {
    "Art":       OB_ART,
    "Copy":      OB_COPY,
    "GD":        OB_GD,
    "Motion":    OB_MOTION,
    "Strategy":  OB_STRATEGY,
    "FA Artist": OB_FA,
    "Account":   OB_ACCOUNT,
}

E_NAME             = "fldvCb5Ttp"
E_OPEN_ID          = "fldiR5gXWt"
E_CURRENT_PROJECTS = "fldGU5CHbk"
E_ACTIVE_JOBS      = "fldCAAIm3o"
E_LOAD_SCORE       = "fldoicLIgp"   # hours — sum of Estimated Hours across active jobs
E_LAST_UPDATED     = "fldYwLot0z"
E_WEEKLY_HOURS     = "fld558vxIV"   # agent-written: sum of Timesheet hours this ISO week
E_MONTHLY_HOURS    = "fld31ku7RX"   # agent-written: sum of Timesheet hours this calendar month
E_OVERLOADED       = "fldBUSPCvv"   # agent sets True if Weekly Hours > 40

# Timesheet table — FF Employees Base (Step 1, added 2026-07-07)
TIMESHEET_TABLE = "tbl26FxJ1Gi0U0zR"
TS_DATE         = "fldcow5K7g"     # Date (datetime yyyy-MM-dd)
TS_PERSON       = "fld0kWWCIO"     # Person (link → Employees)
TS_JOB_TITLE    = "fldOXdrmxV"     # Job Title (text)
TS_JOB_REC_ID   = "fldki43TLW"     # Job Record ID (text — recXXX from DAPUR)
TS_DISCIPLINE   = "fld4epFXr4"     # Discipline (select)
TS_HOURS        = "fldYKRyJxM"     # Hours (number)
TS_WEEK         = "fld9sUX2gU"     # Week (formula — read-only)

# Feature flags
DAILY_HOURS_ENABLED = False   # set True when ready to go live with daily check-in

# Polling
POLLING_INTERVAL_MINUTES = 30
POLL_START_HOUR = 8   # 08:00 WIB
POLL_END_HOUR = 22    # 22:00 WIB
TIMEZONE = "Asia/Jakarta"

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
