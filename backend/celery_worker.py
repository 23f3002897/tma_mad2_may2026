from celery.schedules import crontab
from app import create_app
from extensions import celery
import tasks  # Register tasks with celery

# Create Flask app instance so Celery knows how to load context
app = create_app()

# Configure Scheduled Beat Jobs (Daily Reminders and Monthly Activity Report)
celery.conf.beat_schedule = {
    'daily-reminders-job': {
        'task': 'tasks.daily_reminders',
        # Runs every morning at 8:00 AM
        'schedule': crontab(hour=8, minute=0),
    },
    'monthly-activity-report-job': {
        'task': 'tasks.monthly_activity_report',
        # Runs on the 1st of every month at 9:00 AM
        'schedule': crontab(day_of_month=1, hour=9, minute=0),
    },
}

if __name__ == '__main__':
    print("--> To run Celery worker: celery -A celery_worker.celery worker --loglevel=info")
    print("--> To run Celery beat: celery -A celery_worker.celery beat --loglevel=info")
