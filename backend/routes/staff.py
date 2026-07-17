from flask import Blueprint, request, jsonify
from extensions import db, cache
from models import Trek, Booking
from routes.auth import role_required
from routes.user import get_public_treks


staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')


@staff_bp.route('/treks', methods=['GET'])
@role_required('staff', 'admin')
def get_assigned_treks(current_user):
    """
    Fetch treks assigned to the logged-in Trek Staff member.
    """
    if current_user.role == 'admin':
        treks = Trek.query.order_by(Trek.start_date.asc()).all()
    else:
        treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()

    return jsonify({'treks': [t.to_dict() for t in treks]}), 200


@staff_bp.route('/treks/<int:trek_id>', methods=['PUT'])
@role_required('staff', 'admin')
def update_trek_status_or_slots(current_user, trek_id):
    """
    Staff manages trek status (Open / Closed / Completed) and available slots.
    Mandatory rule: Ensure only assigned staff can manage their trek.
    """
    trek = Trek.query.get_or_404(trek_id)

    # Verify that the staff member is assigned to this trek
    if current_user.role != 'admin' and trek.assigned_staff_id != current_user.id:
        return jsonify({'error': 'You are not assigned to this trek and cannot modify it.'}), 403

    data = request.get_json() or {}

    if 'status' in data and data['status'].strip():
        allowed_statuses = ['Open', 'Closed', 'Completed']
        new_status = data['status'].strip()
        if new_status not in allowed_statuses:
            return jsonify({'error': f'Status must be one of: {", ".join(allowed_statuses)}'}), 400
        trek.status = new_status

    if 'available_slots' in data:
        try:
            new_slots = int(data['available_slots'])
        except ValueError:
            return jsonify({'error': 'Available slots must be an integer.'}), 400

        if new_slots < 0:
            return jsonify({'error': 'Available slots cannot be negative.'}), 400
        if new_slots > trek.total_slots:
            return jsonify({'error': f'Available slots ({new_slots}) cannot exceed total slots ({trek.total_slots}).'}), 400
        
        trek.available_slots = new_slots

    db.session.commit()
    cache.delete_memoized(get_public_treks)

    return jsonify({
        'message': 'Trek details updated successfully.',
        'trek': trek.to_dict()
    }), 200


@staff_bp.route('/treks/<int:trek_id>/participants', methods=['GET'])
@role_required('staff', 'admin')
def get_trek_participants(current_user, trek_id):
    """
    Staff views the list of registered trekkers/bookings for their assigned trek.
    """
    trek = Trek.query.get_or_404(trek_id)

    if current_user.role != 'admin' and trek.assigned_staff_id != current_user.id:
        return jsonify({'error': 'You are not assigned to this trek.'}), 403

    bookings = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
    
    return jsonify({
        'trek_name': trek.name,
        'total_slots': trek.total_slots,
        'available_slots': trek.available_slots,
        'participants': [b.to_dict() for b in bookings]
    }), 200
