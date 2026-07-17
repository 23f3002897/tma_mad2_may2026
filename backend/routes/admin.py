from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db, cache
from models import User, StaffProfile, Trek, Booking
from routes.auth import role_required
from routes.user import get_public_treks


admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/stats', methods=['GET'])
@role_required('admin')
def get_dashboard_stats(current_user):
    """
    Fetch comprehensive analytics for Admin Dashboard (Chart.js and metric cards).
    """
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()

    # Bookings by Status breakdown for Chart.js
    booked_count = Booking.query.filter_by(status='Booked').count()
    cancelled_count = Booking.query.filter_by(status='Cancelled').count()
    completed_count = Booking.query.filter_by(status='Completed').count()

    # Popular treks (top 5 by booking count)
    popular_treks_query = db.session.query(
        Trek.name, db.func.count(Booking.id).label('booking_count')
    ).outerjoin(Booking, Trek.id == Booking.trek_id).group_by(Trek.id).order_by(db.desc('booking_count')).limit(5).all()

    popular_treks = [
        {'name': item[0], 'count': item[1]} for item in popular_treks_query
    ]

    return jsonify({
        'metrics': {
            'total_treks': total_treks,
            'total_users': total_users,
            'total_staff': total_staff,
            'total_bookings': total_bookings
        },
        'charts': {
            'booking_status': {
                'labels': ['Booked', 'Cancelled', 'Completed'],
                'data': [booked_count, cancelled_count, completed_count]
            },
            'popular_treks': {
                'labels': [t['name'] for t in popular_treks],
                'data': [t['count'] for t in popular_treks]
            }
        }
    }), 200


@admin_bp.route('/treks', methods=['GET'])
@role_required('admin')
def get_all_treks(current_user):
    """
    Admin view of all treks regardless of status.
    """
    treks = Trek.query.order_by(Trek.start_date.asc()).all()
    return jsonify({'treks': [t.to_dict() for t in treks]}), 200


@admin_bp.route('/treks', methods=['POST'])
@role_required('admin')
def create_trek(current_user):
    """
    Admin creates a new trekking route.
    """
    data = request.get_json() or {}
    required_fields = ['name', 'location', 'difficulty', 'duration_days', 'total_slots', 'start_date', 'end_date']
    
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # Validation: start_date and end_date parsing
    try:
        start_date = datetime.strptime(str(data['start_date']).strip(), '%Y-%m-%d').date()
        end_date = datetime.strptime(str(data['end_date']).strip(), '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Dates must be in YYYY-MM-DD format.'}), 400

    if end_date < start_date:
        return jsonify({'error': 'End date cannot be earlier than start date.'}), 400

    total_slots = int(data['total_slots'])
    if total_slots <= 0:
        return jsonify({'error': 'Total slots must be greater than zero.'}), 400

    # Check unique trek name
    if Trek.query.filter_by(name=data['name'].strip()).first():
        return jsonify({'error': 'A trek with this name already exists.'}), 409

    assigned_staff_id = data.get('assigned_staff_id')
    if assigned_staff_id:
        staff_check = User.query.filter_by(id=assigned_staff_id, role='staff').first()
        if not staff_check:
            return jsonify({'error': 'Assigned staff ID must belong to a valid Staff member.'}), 400

    new_trek = Trek(
        name=data['name'].strip(),
        location=data['location'].strip(),
        difficulty=data['difficulty'].strip(),
        duration_days=int(data['duration_days']),
        total_slots=total_slots,
        available_slots=total_slots,  # Initially all slots available
        assigned_staff_id=assigned_staff_id or None,
        status=data.get('status', 'Open'),
        start_date=start_date,
        end_date=end_date,
        description=data.get('description', '').strip()
    )

    db.session.add(new_trek)
    db.session.commit()

    # Clear public treks cache so new trek appears instantly
    cache.delete_memoized(get_public_treks)

    return jsonify({
        'message': 'Trek created successfully!',
        'trek': new_trek.to_dict()
    }), 201


@admin_bp.route('/treks/<int:trek_id>', methods=['PUT'])
@role_required('admin')
def update_trek(current_user, trek_id):
    """
    Update existing trekking route details or assign/change staff.
    """
    trek = Trek.query.get_or_404(trek_id)
    data = request.get_json() or {}

    if 'name' in data and data['name'].strip():
        # Check duplicate name
        existing = Trek.query.filter(Trek.name == data['name'].strip(), Trek.id != trek_id).first()
        if existing:
            return jsonify({'error': 'Another trek with this name already exists.'}), 409
        trek.name = data['name'].strip()

    if 'location' in data and data['location'].strip():
        trek.location = data['location'].strip()
    if 'difficulty' in data and data['difficulty'].strip():
        trek.difficulty = data['difficulty'].strip()
    if 'duration_days' in data:
        trek.duration_days = int(data['duration_days'])
    if 'status' in data:
        trek.status = data['status'].strip()
    if 'description' in data:
        trek.description = data['description'].strip()

    if 'total_slots' in data:
        new_total = int(data['total_slots'])
        if new_total <= 0:
            return jsonify({'error': 'Total slots must be greater than zero.'}), 400
        # Adjust available slots based on slot difference
        slot_diff = new_total - trek.total_slots
        trek.total_slots = new_total
        trek.available_slots = max(0, trek.available_slots + slot_diff)

    if 'assigned_staff_id' in data:
        staff_id = data['assigned_staff_id']
        if staff_id:
            staff_check = User.query.filter_by(id=staff_id, role='staff').first()
            if not staff_check:
                return jsonify({'error': 'Assigned staff ID must belong to a valid Staff member.'}), 400
            trek.assigned_staff_id = staff_id
        else:
            trek.assigned_staff_id = None

    if 'start_date' in data and data['start_date']:
        trek.start_date = datetime.strptime(str(data['start_date']).strip(), '%Y-%m-%d').date()
    if 'end_date' in data and data['end_date']:
        trek.end_date = datetime.strptime(str(data['end_date']).strip(), '%Y-%m-%d').date()

    db.session.commit()
    cache.delete_memoized(get_public_treks)

    return jsonify({
        'message': 'Trek updated successfully.',
        'trek': trek.to_dict()
    }), 200


@admin_bp.route('/treks/<int:trek_id>', methods=['DELETE'])
@role_required('admin')
def delete_trek(current_user, trek_id):
    """
    Delete a trekking route and its associated bookings.
    """
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    cache.delete_memoized(get_public_treks)

    return jsonify({'message': 'Trek deleted successfully.'}), 200


@admin_bp.route('/staff', methods=['GET'])
@role_required('admin')
def get_all_staff(current_user):
    """
    Get list of all Trek Staff members.
    """
    staff_members = User.query.filter_by(role='staff').order_by(User.full_name.asc()).all()
    return jsonify({'staff': [s.to_dict() for s in staff_members]}), 200


@admin_bp.route('/staff', methods=['POST'])
@role_required('admin')
def create_staff(current_user):
    """
    Admin creates a new Trek Staff account (since staff cannot self-register).
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    specialization = data.get('specialization', 'General Guide').strip()

    if not email or not password or not full_name:
        return jsonify({'error': 'Email, password, and full name are required.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'An account with this email already exists.'}), 409

    staff_user = User(
        email=email,
        full_name=full_name,
        role='staff',
        is_active=True
    )
    staff_user.set_password(password)
    db.session.add(staff_user)
    db.session.flush()

    staff_profile = StaffProfile(
        user_id=staff_user.id,
        phone=phone or 'N/A',
        specialization=specialization
    )
    db.session.add(staff_profile)
    db.session.commit()

    return jsonify({
        'message': 'Trek Staff account created successfully.',
        'staff': staff_user.to_dict()
    }), 201


@admin_bp.route('/users', methods=['GET'])
@role_required('admin')
def get_all_users_and_staff(current_user):
    """
    Get all users and staff for search and management.
    """
    users = User.query.filter(User.role != 'admin').order_by(User.created_at.desc()).all()
    return jsonify({'users': [u.to_dict() for u in users]}), 200


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['PUT'])
@role_required('admin')
def toggle_user_active_status(current_user, user_id):
    """
    Blacklist / Deactivate or Reactivate a user or staff member.
    """
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        return jsonify({'error': 'Cannot deactivate an Admin account.'}), 400

    user.is_active = not user.is_active
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated (blacklisted)"
    return jsonify({
        'message': f'User {user.email} has been {status_str}.',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/trigger-job/<job_name>', methods=['POST'])
@role_required('admin')
def trigger_scheduled_job(current_user, job_name):
    """
    Manually trigger Celery scheduled batch jobs.
    """
    from tasks import daily_reminders, monthly_activity_report

    if job_name == 'daily_reminders':
        task = daily_reminders.delay()
        return jsonify({
            'message': 'Daily reminders job triggered asynchronously.',
            'task_id': str(task.id)
        }), 202
    elif job_name == 'monthly_activity_report':
        task = monthly_activity_report.delay()
        return jsonify({
            'message': 'Monthly activity report job triggered asynchronously.',
            'task_id': str(task.id)
        }), 202
    else:
        return jsonify({'error': 'Unknown job name. Use "daily_reminders" or "monthly_activity_report".'}), 400

