from dotenv import load_dotenv
import os

load_dotenv()

LARK_APP_ID = os.environ.get("LARK_APP_ID", "")
LARK_APP_SECRET = os.environ.get("LARK_APP_SECRET", "")
BASE_TOKEN = os.environ.get("BASE_TOKEN", "A6GVbQ6sRaYJkZsGpVZlVDJ8gmf")
ECD_OPEN_ID = os.environ.get("ECD_OPEN_ID", "")
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", "5001"))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Table IDs — [BETA] FF Task - Kitchen (A6GVbQ6sRaYJkZsGpVZlVDJ8gmf)
DAPUR_TABLE = "tbl358o9AWPkbAoK"
ROSTER_TABLE = "tblysyNZXISK9vF2"
CHAT_ID_TABLE = "tbloWqFv6UIrUXE0"
BOBOT_TABLE      = "tblAMV4AqwPvWj1C"

# DAPUR field IDs — migrated 2026-07-27 (new base has new field IDs)
F_STAGE_STATUS = "fldrfgbNwP"       # stale — field doesn't exist in new base; handlers will no-op
F_APPROVAL_STATUS = "fld7NiL5es"    # stale — no-op
F_JOB_BRIEF_DATE = "flddtec2nd"     # stale — no-op
F_FIRST_REVIEW_DATE = "fldBpnMhNy"  # stale — no-op
F_CLIENT_PRES_DATE = "fld5eCqBAP"   # stale — no-op
F_SECOND_REVIEW_DATE = "fldYUT0V1Q" # stale — no-op
F_THIRD_REVIEW_DATE = "fldXPjHJGc"  # stale — no-op
F_NEXT_MILESTONE = "fld9s3v6yW"     # stale — no-op
F_ESTIMATED_HOURS = "fldO9ZtCop"    # stale — no-op
F_LAST_AGENT_SYNC = "fldMagUyrX"    # stale — no-op
F_BRIEF_ANNOUNCED = "fld7PcmubU"    # stale — no-op
F_JOB_BRIEF_REMINDER = "fldILWcToS" # stale — no-op
F_FIRST_REVIEW_REMINDER = "fld8gu09fN"  # stale — no-op
F_CLIENT_PRES_REMINDER = "fldTECKIZi"   # stale — no-op
F_SECOND_REVIEW_REMINDER = "fldBOfqiLk" # stale — no-op
F_POST_PRES_CARD_SENT = "fld4zp29Z7"    # stale — no-op
F_PM_PIC = "fld0NI0H9k"            # updated
F_REVISION_COUNT = "fld0dWannS"     # updated
F_ACCOUNT_STATUS = "fldxhKL0x0"    # updated
F_ACCOUNT_PIC = "fldylh3KLO"       # updated
F_ACTUAL_HOURS = "fldF3smRP5"      # updated
F_AI_CONFIDENCE = "fldS8qx4F3"     # stale — no-op
F_ART_ASSIGNED = "fldEX4xvDL"
F_COPY_ASSIGNED = "fldqZGdn7Z"
F_GD_ASSIGNED = "fldUFuqlPa"
F_MOTION_ASSIGNED = "fldE5yJTeM"
F_STRATEGY_ASSIGNED = "fldc8ikiB1"
F_FA_ASSIGNED = "fldrM1lwar"
F_CREATIVE_TEAM = "fldDXtWPj0"     # updated
F_JOB_TITLE = "fld6elh0J7"
F_JOB_TYPE  = "fldoGTF6g5"         # Job Type (select: Campaign/Tactical/etc.)
F_CLIENT_LINK = "fld7MDHHJN"        # Client (link → Clients table) — agent-written
F_CLIENT_NAME = "fldzr8aih0"        # Client Name (select, form-filled) — source for bridge
F_BRIEF_LINK = "fldHwV7ihE"
F_LARK_TASK_ID = "fldA6mSsZy"      # Lark Task ID — used by load_sync

# Deliverable pair fields (stale IDs — field doesn't exist in new base; handlers no-op)
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

# Per-discipline Estimated Hours fields in DAPUR (stale — no-op in new base)
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

# Team Roster field IDs — [BETA] FF Task - Kitchen
R_NAME = "fldLy0sa0j"
R_DISCIPLINE = "fld0eDLpb8"
R_ROLE = "fldVQkaiOa"
R_OPEN_ID = "fldFrxViIu"
R_LOAD_SCORE = "fldpswoAH1"        # Task Load Score (number, agent-written from Lark Tasks)
R_TASK_COUNT = "fldv8WjTog"        # Task Count (number of active subtasks assigned)
R_TASK_LINKS = "fldkS90nsC"        # Lark Task Links (URL field — applinks to active tasks)
R_AVAILABLE = "fld6WLvIHk"
R_CURRENT_JOBS = "fldieV3QYi"      # Current Jobs (text)
R_NEXT_DEADLINE = "fldxVIm90A"     # Next Deadline (datetime)

# Creative Chat ID field IDs
C_CHAT_ID = "fldIZIhz9f"
C_TEAM_NAME = "fld2YQOPp6"

# Account Roster table — [BETA] FF Task - Kitchen
ACCOUNT_ROSTER_TABLE = "tblBYVXullrkrebn"
AR_NAME         = "fld5AnD5Tc"   # Name (text)
AR_OPEN_ID      = "fldNBAogFE"   # Lark Open ID (text)
AR_DISCIPLINE   = "fld1dJtMr2"   # Discipline (select)
AR_ROLE         = "fldt8rYf1t"   # Role (select)
AR_TEAM         = "fldBX00aKw"   # Team (select)
AR_LOAD_SCORE   = "fldMJCnOjn"   # Task Load Score (number)
AR_TASK_COUNT   = "fldQ5RIBke"   # Task Count (number)
AR_CURRENT_JOBS = "flddqDD1eJ"   # Current Jobs (text)
AR_TASK_LINKS   = "fldPKbbDkz"   # Lark Task Links (text)
AR_NEXT_DEADLINE= "fldR4aICjL"   # Next Deadline (datetime)

# FF Employees base (Flock People System — separate base)
EMPLOYEES_BASE_TOKEN = "SkrkbyaJwa3jxHsn619lG5a7g7f"
EMPLOYEES_TABLE = "tblNyIHGQb2jh0Iy"

# Output Type Bobot field IDs — [BETA] FF Task - Kitchen
OB_NAME     = "fldRA8pYTD"   # Output type name (primary field)
OB_ART      = "fldkp2b5Iw"   # Base Hours (Art)
OB_COPY     = "fldZlM1xMw"   # Base Hours (Copy)
OB_GD       = "fldL3cfoWC"   # Base Hours (GD)
OB_MOTION   = "fldEEbkF1i"   # Base Hours (Motion)
OB_STRATEGY = "fldoDJBj8T"   # Base Hours (Strategy)
OB_FA       = "fldR6HPSPs"   # Base Hours (FA Artist)
OB_AE       = "fld4v8njKS"   # Base Hours (Account Executive)
OB_AM       = "fldhg8Jkhi"   # Base Hours (Account Manager)
OB_AD       = "fldtLsLgB5"   # Base Hours (Account Director)
OB_CD       = "fld404DJ5u"   # Base Hours (Creative Director)
OB_CGH      = "fld4x9MNkU"   # Base Hours (Creative Group Head)
OB_ECD      = "fldUO7bg6M"   # Base Hours (Executive Creative Director)
OB_GAD      = "fldw5NDj1D"   # Base Hours (Group Account Director)
OB_STRATEGY = "fld4MTDGS3"   # Base Hours (Strategy)

# Maps discipline name → OB_* field ID (for bobot reads + EMA writes)
# Creative: Art, Copy, GD, Motion, FA, CGH, CD
# Account:  AE, AM, AD
# Leadership: ECD, GAD, Strategy, PM
DISCIPLINE_OB_FIELDS = {
    "Art":       OB_ART,
    "Copy":      OB_COPY,
    "GD":        OB_GD,
    "Motion":    OB_MOTION,
    "FA Artist": OB_FA,
    "Creative Group Head":        OB_CGH,
    "Creative Director":          OB_CD,
    "Account Executive":          OB_AE,
    "Account Manager":            OB_AM,
    "Account Director":           OB_AD,
    "Executive Creative Director": OB_ECD,
    "Group Account Director":     OB_GAD,
    "Strategy":                   OB_STRATEGY,
}

# FF Employees field IDs
E_NAME             = "fldvCb5Ttp"
E_OPEN_ID          = "fldiR5gXWt"
E_CURRENT_PROJECTS = "fldGU5CHbk"
E_ACTIVE_JOBS      = "fldCAAIm3o"
E_LOAD_SCORE       = "fldoicLIgp"   # hours — sum of Estimated Hours across active jobs
E_LAST_UPDATED     = "fldYwLot0z"
E_WEEKLY_HOURS     = "fld558vxIV"   # agent-written: sum of Timesheet hours this ISO week
E_MONTHLY_HOURS    = "fld31ku7RX"   # agent-written: sum of Timesheet hours this calendar month
E_OVERLOADED       = "fldBUSPCvv"   # agent sets True if Weekly Hours > 40

# Timesheet table — FF Employees Base
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
