from datetime import datetime
from flask import Blueprint, request, jsonify
from extensions import db, cache
from models import Trek, Booking
from routes.auth import token_required

user_bp = Blueprint('user', __name__, url_prefix='/api')


@cache.memoize(timeout=300)
def get_public_treks():
    """
    Cached helper function to fetch all open/available treks.
    Redis cache is cleared whenever a trek is created, modified, or booked.
    """
    treks = Trek.query.order_by(Trek.start_date.asc()).all()
    return [t.to_dict() for t in treks]


@user_bp.route('/treks', methods=['GET'])
def browse_treks():
    """
    Browse open and available treks with filtering and search capabilities.
    """
    difficulty = request.args.get('difficulty', '').strip()
    location = request.args.get('location', '').strip().lower()
    search = request.args.get('search', '').strip().lower()
    status = request.args.get('status', 'Open').strip()

    # Get cached base list
    all_treks = get_public_treks()

    # Apply in-memory filtering (to leverage base Redis cache efficiently)
    filtered = []
    for t in all_treks:
        if status and status != 'All' and t['status'] != status:
            continue
        if difficulty and difficulty != 'All' and t['difficulty'].lower() != difficulty.lower():
            continue
        if location and location not in t['location'].lower():
            continue
        if search and (search not in t['name'].lower() and search not in t['location'].lower() and search not in t['description'].lower()):
            continue
        filtered.append(t)

    return jsonify({'treks': filtered}), 200


@user_bp.route('/bookings', methods=['POST'])
@token_required
def book_trek(current_user):
    """
    Book a trekking route.
    Validations:
    1. Allow booking only when trek status is 'Open'.
    2. Prevent overbooking beyond available slots.
    3. Prevent duplicate bookings for the same trek by the same user.
    """
    data = request.get_json() or {}
    trek_id = data.get('trek_id')
    tickets_booked = data.get('tickets_booked', 1)

    if not trek_id:
        return jsonify({'error': 'Trek ID is required.'}), 400

    try:
        tickets_booked = int(tickets_booked)
    except ValueError:
        return jsonify({'error': 'Tickets booked must be a valid integer.'}), 400

    if tickets_booked <= 0:
        return jsonify({'error': 'You must book at least 1 ticket.'}), 400

    trek = Trek.query.get_or_404(trek_id)

    # Check 1: Trek Status
    if trek.status != 'Open':
        return jsonify({'error': f'Booking failed: This trek is currently "{trek.status}" and not accepting bookings.'}), 400

    # Check 2: Overbooking Constraint
    if trek.available_slots < tickets_booked:
        return jsonify({
            'error': f'Overbooking prevented! Only {trek.available_slots} slots left for this trek, but {tickets_booked} requested.'
        }), 400

    # Check 3: Duplicate Booking Constraint
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id,
        status='Booked'
    ).first()
    if existing_booking:
        return jsonify({
            'error': 'Duplicate booking prevented! You already have an active booking for this trek.'
        }), 409

    # Execute Booking
    trek.available_slots -= tickets_booked
    new_booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        tickets_booked=tickets_booked,
        status='Booked'
    )
    db.session.add(new_booking)
    db.session.commit()

    # Invalidate public treks cache due to updated available slots
    cache.delete_memoized(get_public_treks)

    return jsonify({
        'message': f'Successfully booked {tickets_booked} ticket(s) for {trek.name}!',
        'booking': new_booking.to_dict()
    }), 201


@user_bp.route('/bookings', methods=['GET'])
@token_required
def get_user_bookings(current_user):
    """
    Fetch booking status and history for the logged-in user.
    """
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return jsonify({'bookings': [b.to_dict() for b in bookings]}), 200


@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@token_required
def cancel_booking(current_user, booking_id):
    """
    Cancel an active booking and restore available slots.
    """
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id and current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized to cancel this booking.'}), 403

    if booking.status != 'Booked':
        return jsonify({'error': f'Cannot cancel a booking that is already {booking.status}.'}), 400

    booking.status = 'Cancelled'
    if booking.trek:
        booking.trek.available_slots += booking.tickets_booked

    db.session.commit()
    cache.delete_memoized(get_public_treks)

    return jsonify({
        'message': 'Booking cancelled successfully. Slots restored.',
        'booking': booking.to_dict()
    }), 200


@user_bp.route('/bookings/export-csv', methods=['POST'])
@token_required
def trigger_csv_export(current_user):
    """
    Trigger Celery asynchronous batch job to export user's booking history as CSV.
    Mandatory rule: Triggered from user dashboard, triggers batch job, sends alert once done.
    """
    from tasks import export_user_bookings_csv
    
    # Launch async task
    task = export_user_bookings_csv.delay(current_user.id, current_user.email)
    
    return jsonify({
        'message': 'CSV export job started! We will notify you once your download is ready.',
        'task_id': str(task.id),
        'status': 'Processing'
    }), 202


@user_bp.route('/bookings/export-status/<task_id>', methods=['GET'])
@token_required
def check_csv_export_status(current_user, task_id):
    """
    Check the status of the triggered CSV export task.
    Once complete, returns the download file URL.
    """
    from celery.result import AsyncResult
    from extensions import celery
    
    task_result = AsyncResult(task_id, app=celery)
    
    if task_result.state == 'SUCCESS':
        return jsonify({
            'state': 'SUCCESS',
            'download_url': task_result.result.get('download_url'),
            'filename': task_result.result.get('filename')
        }), 200
    elif task_result.state == 'FAILURE':
        return jsonify({
            'state': 'FAILURE',
            'error': str(task_result.result)
        }), 500
    else:
        return jsonify({
            'state': task_result.state
        }), 200
