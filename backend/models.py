from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # roles: 'admin', 'staff', 'user'
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # used for blacklisting/deactivation
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    assigned_treks = db.relationship('Trek', backref='staff_member', foreign_keys='Trek.assigned_staff_id')
    bookings = db.relationship('Booking', backref='trekker', cascade='all, delete-orphan', foreign_keys='Booking.user_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        data = {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        if self.role == 'staff' and self.staff_profile:
            data['phone'] = self.staff_profile.phone
            data['specialization'] = self.staff_profile.specialization
        return data


class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    phone = db.Column(db.String(20), default='N/A')
    specialization = db.Column(db.String(100), default='General Trek Leader')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone': self.phone,
            'specialization': self.specialization
        }


class Trek(db.Model):
    __tablename__ = 'treks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)  # 'Easy', 'Moderate', 'Hard'
    duration_days = db.Column(db.Integer, nullable=False, default=1)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(50), default='Open', nullable=False)  # 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    bookings = db.relationship('Booking', backref='trek', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'difficulty': self.difficulty,
            'duration_days': self.duration_days,
            'total_slots': self.total_slots,
            'available_slots': self.available_slots,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': self.staff_member.full_name if self.staff_member else 'Unassigned',
            'status': self.status,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'description': self.description or 'No description provided.'
        }


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Booked', nullable=False)  # 'Booked', 'Cancelled', 'Completed'
    tickets_booked = db.Column(db.Integer, default=1, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.trekker.email if self.trekker else 'Unknown',
            'user_name': self.trekker.full_name if self.trekker else 'Unknown',
            'trek_id': self.trek_id,
            'trek_name': self.trek.name if self.trek else 'Unknown Trek',
            'location': self.trek.location if self.trek else 'Unknown Location',
            'difficulty': self.trek.difficulty if self.trek else 'Unknown',
            'booking_date': self.booking_date.strftime('%Y-%m-%d %H:%M:%S') if self.booking_date else None,
            'status': self.status,
            'tickets_booked': self.tickets_booked
        }


def init_default_data():
    """
    Programmatic creation of required pre-existing Admin and sample data during database initialization.
    Mandatory rule: Only ONE Admin must exist and be created programmatically after database creation.
    """
    from datetime import date, timedelta

    # 1. Create default Superuser Admin if none exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            email='admin@tma.com',
            full_name='System Admin',
            role='admin',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("--> Created pre-existing Admin account: admin@tma.com / admin123")

    # 2. Create sample Staff if none exists
    staff = User.query.filter_by(email='staff@tma.com').first()
    if not staff:
        staff = User(
            email='staff@tma.com',
            full_name='Ravi Kumar (Staff)',
            role='staff',
            is_active=True
        )
        staff.set_password('staff123')
        db.session.add(staff)
        db.session.flush() # get staff.id
        
        profile = StaffProfile(
            user_id=staff.id,
            phone='9876543210',
            specialization='Himalayan High Altitude Guide'
        )
        db.session.add(profile)
        print("--> Created sample Trek Staff account: staff@tma.com / staff123")

    # 3. Create sample Trekker User if none exists
    trekker = User.query.filter_by(email='user@tma.com').first()
    if not trekker:
        trekker = User(
            email='user@tma.com',
            full_name='Rahul Sharma',
            role='user',
            is_active=True
        )
        trekker.set_password('user123')
        db.session.add(trekker)
        print("--> Created sample Trekker account: user@tma.com / user123")

    # 4. Create sample Treks if none exist
    if Trek.query.count() == 0:
        db.session.flush() # ensure staff.id is ready
        today = date.today()
        treks_data = [
            Trek(
                name='Triund Summit Trek',
                location='McLeod Ganj, Himachal Pradesh',
                difficulty='Easy',
                duration_days=2,
                total_slots=20,
                available_slots=20,
                assigned_staff_id=staff.id if staff else None,
                status='Open',
                start_date=today + timedelta(days=5),
                end_date=today + timedelta(days=6),
                description='A scenic 2-day weekend trek offering breathtaking panoramic views of the Dhauladhar range.'
            ),
            Trek(
                name='Kedarkantha Winter Trek',
                location='Uttarkashi, Uttarakhand',
                difficulty='Moderate',
                duration_days=6,
                total_slots=15,
                available_slots=15,
                assigned_staff_id=staff.id if staff else None,
                status='Open',
                start_date=today + timedelta(days=12),
                end_date=today + timedelta(days=17),
                description='One of the most popular winter peak climbs featuring pristine snow trails and lush pine forests.'
            ),
            Trek(
                name='Roopkund Mystery Lake Trek',
                location='Chamoli, Uttarakhand',
                difficulty='Hard',
                duration_days=8,
                total_slots=10,
                available_slots=10,
                assigned_staff_id=staff.id if staff else None,
                status='Open',
                start_date=today + timedelta(days=20),
                end_date=today + timedelta(days=27),
                description='High altitude trek leading to the famous glacial mystery lake surrounded by dramatic snow peaks.'
            )
        ]
        db.session.add_all(treks_data)
        print("--> Pre-populated sample Trekking Routes and records.")

    db.session.commit()
