from datetime import datetime, timedelta
from functools import wraps
import jwt
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

def token_required(f):
    """
    JWT Token verification decorator.
    Ensures the request has a valid token and the user is not blacklisted/deactivated.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Extract token from Authorization header (Bearer <token>)
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = auth_header

        if not token:
            return jsonify({'error': 'Authentication token is missing. Please log in.'}), 401

        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            if not current_user:
                return jsonify({'error': 'User associated with token no longer exists.'}), 401
            if not current_user.is_active:
                return jsonify({'error': 'Your account has been deactivated or blacklisted by the Admin.'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Your session has expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token. Please log in again.'}), 401

        return f(current_user, *args, **kwargs)
    return decorated


def role_required(*roles):
    """
    Role-Based Access Control (RBAC) decorator.
    Can accept one or multiple allowed roles: @role_required('admin') or @role_required('admin', 'staff')
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({
                    'error': f'Unauthorized access. Required role(s): {", ".join(roles)}'
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Unified login endpoint for Admin, Staff, and User roles.
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Please provide both email and password.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    if not user.is_active:
        return jsonify({'error': 'Your account has been deactivated or blacklisted by the Admin.'}), 403

    # Generate JWT Token
    expiration = datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA']
    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': expiration
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Self-registration endpoint for Users (Trekkers) only.
    As mandated by rules: Admin pre-exists and Staff must be created by Admin.
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()

    if not email or not password or not full_name:
        return jsonify({'error': 'Email, password, and full name are all required.'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long.'}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({'error': 'An account with this email address already exists.'}), 409

    new_user = User(
        email=email,
        full_name=full_name,
        role='user',  # Force 'user' role for self-registration
        is_active=True
    )
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'Registration successful! You can now log in.',
        'user': new_user.to_dict()
    }), 201


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Fetch current user profile details.
    """
    return jsonify({'user': current_user.to_dict()}), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update current user profile (full name, password, or staff specialization/phone).
    """
    data = request.get_json() or {}
    
    if 'full_name' in data and data['full_name'].strip():
        current_user.full_name = data['full_name'].strip()
        
    if 'password' in data and data['password']:
        if len(data['password']) < 6:
            return jsonify({'error': 'New password must be at least 6 characters.'}), 400
        current_user.set_password(data['password'])

    if current_user.role == 'staff' and current_user.staff_profile:
        if 'phone' in data:
            current_user.staff_profile.phone = data['phone'].strip()
        if 'specialization' in data:
            current_user.staff_profile.specialization = data['specialization'].strip()

    db.session.commit()
    return jsonify({
        'message': 'Profile updated successfully.',
        'user': current_user.to_dict()
    }), 200
