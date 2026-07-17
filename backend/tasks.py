import os
import csv
import urllib.request
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime, timedelta
from extensions import celery, db
from models import User, Trek, Booking

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, 'generated_reports')
EXPORTS_DIR = os.path.join(BASE_DIR, 'static', 'exports')
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(EXPORTS_DIR, exist_ok=True)


def send_email(to_email, subject, body_text, html_content=None):
    """
    Sends an email using SMTP if environment variables SMTP_EMAIL and SMTP_PASSWORD are set.
    Otherwise, logs that SMTP credentials are not configured and simulates delivery.
    """
    smtp_email = os.environ.get('SMTP_EMAIL')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', 587))

    if not smtp_email or not smtp_password:
        print(f"[SMTP SIMULATION] Would send email to {to_email} | Subject: {subject} (Set SMTP_EMAIL & SMTP_PASSWORD env variables to enable real SMTP sending)")
        return False

    try:
        if html_content:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        else:
            msg = MIMEText(body_text, 'plain', 'utf-8')

        msg['Subject'] = subject
        msg['From'] = smtp_email
        msg['To'] = to_email

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        print(f"[SMTP SUCCESS] Sent real email to {to_email} | Subject: {subject}")
        return True
    except Exception as e:
        print(f"[SMTP ERROR] Could not send email to {to_email}: {e}")
        return False



@celery.task(name='tasks.daily_reminders')
def daily_reminders():
    """
    Scheduled Job A: Daily Reminders
    Checks for upcoming treks starting within the next 3 days and sends reminders
    via Google Chat Webhook (if set), email simulation, and terminal logs.
    """
    today = date.today()
    target_date = today + timedelta(days=3)

    # Find treks starting between today and 3 days from now
    upcoming_treks = Trek.query.filter(
        Trek.start_date >= today,
        Trek.start_date <= target_date,
        Trek.status == 'Open'
    ).all()

    reminders_sent = 0
    log_file_path = os.path.join(REPORTS_DIR, f'daily_reminders_{today.strftime("%Y_%m_%d")}.log')

    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.write(f"\n--- DAILY REMINDER RUN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        
        for trek in upcoming_treks:
            bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').all()
            for booking in bookings:
                user = booking.trekker
                if not user or not user.is_active:
                    continue

                message = (
                    f"Reminder for {user.full_name} ({user.email}):\n"
                    f"Your upcoming trek '{trek.name}' starts on {trek.start_date.strftime('%B %d, %Y')} at {trek.location}.\n"
                    f"Difficulty: {trek.difficulty} | Duration: {trek.duration_days} days.\n"
                    f"Please arrive on time and carry valid identification and trekking gear!"
                )

                # Log to terminal and file
                print(f"[CELERY REMINDER] {message}")
                log_file.write(message + "\n----------------------------------------\n")
                reminders_sent += 1

                # Send email reminder
                subject = f"Trek Reminder: {trek.name} starts on {trek.start_date.strftime('%B %d, %Y')}"
                send_email(user.email, subject, message)

                # Optional: Send via Google Chat Webhook if environment variable is configured
                gchat_webhook = os.environ.get('GCHAT_WEBHOOK_URL')
                if gchat_webhook:
                    try:
                        payload = {'text': f"*Trek Reminder:* {message}"}
                        req = urllib.request.Request(
                            gchat_webhook,
                            data=json.dumps(payload).encode('utf-8'),
                            headers={'Content-Type': 'application/json'}
                        )
                        urllib.request.urlopen(req)
                    except Exception as e:
                        print(f"[CELERY WARNING] Failed to send G-Chat notification: {e}")

    summary = f"Daily reminders job completed. Sent {reminders_sent} reminder(s) across {len(upcoming_treks)} upcoming trek(s)."
    print(summary)
    return summary


@celery.task(name='tasks.monthly_activity_report')
def monthly_activity_report():
    """
    Scheduled Job B: Monthly Activity Report
    generates a beautifully formatted HTML report on the 1st of every month
    and saves it to generated_reports/ while logging to console.
    """
    today = date.today()
    # Calculate previous month stats or all-time stats for summary
    total_treks = Trek.query.count()
    total_bookings = Booking.query.filter_by(status='Booked').count()
    completed_treks = Trek.query.filter_by(status='Completed').count()
    total_users = User.query.filter_by(role='user').count()

    # Top popular treks
    popular_query = db.session.query(
        Trek.name, Trek.location, db.func.count(Booking.id).label('b_count')
    ).outerjoin(Booking, Trek.id == Booking.trek_id).group_by(Trek.id).order_by(db.desc('b_count')).limit(5).all()

    popular_rows_html = ""
    for name, loc, count in popular_query:
        popular_rows_html += f"""
        <tr>
            <td style="padding: 10px; border: 1px solid #ddd;">{name}</td>
            <td style="padding: 10px; border: 1px solid #ddd;">{loc}</td>
            <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; color: #2e6c80;">{count}</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>TMA Monthly Activity Report - {today.strftime('%B %Y')}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 700px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .header {{ background: #2c3e50; color: #ffffff; padding: 20px; text-align: center; border-radius: 6px 6px 0 0; margin: -30px -30px 25px -30px; }}
        .metric-card {{ display: inline-block; width: 45%; background: #e8f4f8; padding: 15px; margin: 5px; border-radius: 6px; text-align: center; }}
        .metric-number {{ font-size: 28px; font-weight: bold; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #34495e; color: #ffffff; padding: 10px; text-align: left; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #7f8c8d; text-align: center; border-top: 1px solid #eee; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0;">Trekking Management System</h1>
            <p style="margin: 5px 0 0 0;">Monthly Activity Report - {today.strftime('%B %Y')}</p>
        </div>
        
        <h2>Monthly Summary Metrics</h2>
        <div>
            <div class="metric-card">
                <div class="metric-number">{total_treks}</div>
                <div>Total Trek Routes</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{total_bookings}</div>
                <div>Active Bookings</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{completed_treks}</div>
                <div>Completed Treks</div>
            </div>
            <div class="metric-card">
                <div class="metric-number">{total_users}</div>
                <div>Registered Trekkers</div>
            </div>
        </div>

        <h2>Top Popular Treks</h2>
        <table>
            <thead>
                <tr>
                    <th>Trek Name</th>
                    <th>Location</th>
                    <th>Bookings Count</th>
                </tr>
            </thead>
            <tbody>
                {popular_rows_html or '<tr><td colspan="3" style="padding: 10px; text-align: center;">No booking activity recorded yet.</td></tr>'}
            </tbody>
        </table>

        <div class="footer">
            Generated programmatically by TMA Celery Batch Worker on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.<br>
            Sent to Institute Admin (admin@tma.com).
        </div>
    </div>
</body>
</html>
"""

    report_filename = f'monthly_activity_report_{today.strftime("%B_%Y").lower()}.html'
    report_path = os.path.join(REPORTS_DIR, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Send email to Admin
    admin_user = User.query.filter_by(role='admin').first()
    admin_email = admin_user.email if admin_user else 'admin@tma.com'
    send_email(
        to_email=admin_email,
        subject=f"TMA Monthly Activity Report - {today.strftime('%B %Y')}",
        body_text=f"Please find the monthly activity report for {today.strftime('%B %Y')} attached or generated on server.",
        html_content=html_content
    )

    msg = f"[CELERY REPORT] Monthly Activity Report successfully generated and saved to: {report_path}"
    print(msg)
    return {'status': 'SUCCESS', 'report_path': report_path, 'filename': report_filename}


@celery.task(name='tasks.export_user_bookings_csv')
def export_user_bookings_csv(user_id, user_email):
    """
    User Triggered Async Job C: Export Bookings History as CSV
    Generates a CSV file inside static/exports/ with all historical bookings of the user.
    """
    user = User.query.get(user_id)
    if not user:
        return {'status': 'FAILURE', 'error': 'User not found.'}

    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()

    filename = f"user_{user_id}_booking_history.csv"
    file_path = os.path.join(EXPORTS_DIR, filename)

    with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        # CSV Headers as specified by rule: User ID, Trek Name, Location, Booking Status, Dates
        writer.writerow(['User ID', 'Trek Name', 'Location', 'Difficulty', 'Booking Status', 'Tickets Booked', 'Booking Date', 'Trek Start Date', 'Trek End Date'])

        for b in bookings:
            trek = b.trek
            writer.writerow([
                user_id,
                trek.name if trek else 'Unknown Trek',
                trek.location if trek else 'Unknown Location',
                trek.difficulty if trek else 'N/A',
                b.status,
                b.tickets_booked,
                b.booking_date.strftime('%Y-%m-%d %H:%M:%S') if b.booking_date else 'N/A',
                trek.start_date.strftime('%Y-%m-%d') if trek and trek.start_date else 'N/A',
                trek.end_date.strftime('%Y-%m-%d') if trek and trek.end_date else 'N/A'
            ])

    download_url = f"/api/exports/{filename}"
    msg = f"[CELERY EXPORT] CSV Export completed for user {user_email}. File ready at: {download_url}"
    print(msg)

    return {
        'status': 'SUCCESS',
        'filename': filename,
        'download_url': download_url,
        'message': 'Your booking history CSV is ready for download!'
    }
