import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='PATIENT') # PATIENT, DOCTOR, HOSPITAL_ADMIN, SYSTEM_ADMIN
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    patient_profile = db.relationship('Patient', backref='user', uselist=False, cascade="all, delete-orphan")
    doctor_profile = db.relationship('Doctor', backref='user', uselist=False, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Hospital(db.Model):
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    city = db.Column(db.String(100), nullable=False, default='Central City')
    rating = db.Column(db.Float, default=4.5)
    contact_phone = db.Column(db.String(20), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    
    # Bed allocations
    general_beds_total = db.Column(db.Integer, default=50)
    general_beds_avail = db.Column(db.Integer, default=22)
    icu_beds_total = db.Column(db.Integer, default=15)
    icu_beds_avail = db.Column(db.Integer, default=5)
    emergency_beds_total = db.Column(db.Integer, default=10)
    emergency_beds_avail = db.Column(db.Integer, default=3)
    private_rooms_total = db.Column(db.Integer, default=20)
    private_rooms_avail = db.Column(db.Integer, default=8)

    # Relationships
    doctors = db.relationship('Doctor', backref='hospital', lazy=True)
    appointments = db.relationship('Appointment', backref='hospital', lazy=True)
    medicines = db.relationship('Medicine', backref='hospital', lazy=True)
    bed_resources = db.relationship('BedResource', backref='hospital', lazy=True, cascade="all, delete-orphan")


class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(150), nullable=False)
    experience_years = db.Column(db.Integer, default=5)
    avg_consultation_time_min = db.Column(db.Integer, default=10)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    medical_records = db.relationship('MedicalRecord', backref='doctor', lazy=True)


class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer, nullable=False, default=30)
    gender = db.Column(db.String(20), default='Other')
    blood_group = db.Column(db.String(10), default='O+')
    medical_history = db.Column(db.Text, nullable=True)

    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    medical_records = db.relationship('MedicalRecord', backref='patient', lazy=True)


class BedResource(db.Model):
    __tablename__ = 'bed_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    bed_type = db.Column(db.String(50), nullable=False) # GENERAL, ICU, EMERGENCY, PRIVATE
    total = db.Column(db.Integer, nullable=False, default=20)
    occupied = db.Column(db.Integer, nullable=False, default=10)
    
    @property
    def available(self):
        return max(0, self.total - self.occupied)


class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_code = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    appointment_date = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), default='CONFIRMED') # CONFIRMED, WAITING, IN_CONSULTATION, COMPLETED, CANCELLED
    priority = db.Column(db.Integer, default=1) # 1 (Low) to 5 (Critical)
    urgency_level = db.Column(db.String(20), default='GREEN') # RED, ORANGE, YELLOW, GREEN
    symptoms = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    token_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    queue_token = db.relationship('QueueToken', backref='appointment', uselist=False, cascade="all, delete-orphan")


class QueueToken(db.Model):
    __tablename__ = 'queue_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    token_code = db.Column(db.String(20), nullable=False)
    priority = db.Column(db.Integer, default=1)
    status = db.Column(db.String(30), default='WAITING') # WAITING, IN_CONSULTATION, COMPLETED, CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class MedicalRecord(db.Model):
    __tablename__ = 'medical_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    record_date = db.Column(db.String(20), nullable=False)
    diagnosis_notes = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text, nullable=True)
    prescription_summary = db.Column(db.Text, nullable=True)
    report_file = db.Column(db.String(255), nullable=True)
    report_ai_summary = db.Column(db.Text, nullable=True)

    # Relationships
    prescription = db.relationship('Prescription', backref='medical_record', uselist=False, cascade="all, delete-orphan")


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    medical_record_id = db.Column(db.Integer, db.ForeignKey('medical_records.id'), nullable=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    medicines_json = db.Column(db.Text, nullable=False) # JSON list of {medicine, dosage, frequency, duration}
    instructions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    appointment = db.relationship('Appointment', backref='prescription', uselist=False, lazy=True)
    patient = db.relationship('Patient', backref='prescriptions', lazy=True)
    doctor = db.relationship('Doctor', backref='prescriptions', lazy=True)


class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    batch_no = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=100)
    min_stock = db.Column(db.Integer, nullable=False, default=30)
    unit_price = db.Column(db.Float, nullable=False, default=10.0)
    expiry_date = db.Column(db.String(20), nullable=False)
    supplier = db.Column(db.String(100), default='PharmaCorp Direct')

    @property
    def status(self):
        if self.quantity <= 0:
            return 'CRITICAL'
        elif self.quantity < self.min_stock:
            return 'LOW STOCK'
        else:
            return 'NORMAL'


class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicines.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False) # IN or OUT
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    notification_type = db.Column(db.String(50), default='INFO') # INFO, APPOINTMENT, QUEUE, INVENTORY, ALERT
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
