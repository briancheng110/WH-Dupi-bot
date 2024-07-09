import Work_queue_manager as wqm
import Subject_Management as sm
from freezegun import freeze_time
from datetime import datetime, timedelta

offset_days = 0  # for example, 10 days from today
if offset_days > 0:
    target_date = datetime.now() + timedelta(days=offset_days)
    freezer = freeze_time(target_date)
    freezer.start()


if __name__ == "__main__":
    # Load subjects file
    sdf = sm.load_subjects()

    wqm.add_weekly_nag(sdf)
    #wqm.collect_todo(sdf)
    wqm.add_dupi_reminder(sdf)
    #wqm.add_visit_reminders()
    #wqm.add_incomplete_survey_nag()
