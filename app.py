import os
import json
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import (
    db, User, Hospital, Doctor, Patient, BedResource,
    Appointment, QueueToken, MedicalRecord, Prescription,
    Medicine, InventoryTransaction, Notification
)
from triage_engine import triage_engine
from inventory_engine import inventory_engine

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'medq-secret-key-2026-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///medq.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('Unauthorized access for your account role.', 'error')
                return redirect(url_for('dashboard_router'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Automatic Router based on Role
@app.route('/dashboard', endpoint='dashboard')
@app.route('/dashboard_router', endpoint='dashboard_router')
@login_required
def dashboard_router():
    if current_user.role == 'PATIENT':
        return redirect(url_for('patient_dashboard'))
    elif current_user.role == 'DOCTOR':
        return redirect(url_for('doctor_dashboard'))
    elif current_user.role == 'HOSPITAL_ADMIN':
        return redirect(url_for('hospital_dashboard'))
    elif current_user.role == 'SYSTEM_ADMIN':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('home'))

# ---------------------------------------------------------
# LANDING & AUTH ROUTES
# ---------------------------------------------------------

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_router'))
    hospitals = Hospital.query.limit(6).all()
    categories = triage_engine.symptoms_map.keys() if triage_engine.symptoms_map else []
    return render_template('home.html', hospitals=hospitals, categories=categories)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_router'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard_router'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard_router'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'PATIENT').strip()

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists.', 'error')
            return render_template('register.html')

        user = User(email=email, name=name, phone=phone, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if role == 'PATIENT':
            patient_profile = Patient(user_id=user.id, age=30, gender='Unspecified', blood_group='Unknown')
            db.session.add(patient_profile)
            db.session.commit()

        login_user(user)
        flash('Account registered successfully!', 'success')
        return redirect(url_for('dashboard_router'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# ---------------------------------------------------------
# PATIENT PORTAL ROUTES
# ---------------------------------------------------------

@app.route('/patient/dashboard')
@role_required('PATIENT')
def patient_dashboard():
    patient = current_user.patient_profile
    if not patient:
        patient = Patient(user_id=current_user.id, age=30, gender='Unspecified', blood_group='Unknown')
        db.session.add(patient)
        db.session.commit()

    upcoming = Appointment.query.filter_by(patient_id=patient.id).filter(Appointment.status.in_(['WAITING', 'CONFIRMED', 'IN_CONSULTATION'])).all()
    records = MedicalRecord.query.filter_by(patient_id=patient.id).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()

    active_app = upcoming[0] if upcoming else None
    estimated_wait = 0
    patients_ahead = 0

    if active_app and active_app.queue_token:
        # Calculate patients ahead in the queue for the same hospital
        ahead_tokens = QueueToken.query.filter_by(hospital_id=active_app.hospital_id, status='WAITING')\
            .filter(QueueToken.priority >= active_app.priority)\
            .filter(QueueToken.id < active_app.queue_token.id).all()
        patients_ahead = len(ahead_tokens)
        estimated_wait = max(5, patients_ahead * 10)

    return render_template('patient/dashboard.html',
                           upcoming_appointments=upcoming,
                           medical_records=records,
                           notifications=notifications,
                           active_appointment=active_app,
                           estimated_wait_min=estimated_wait,
                           patients_ahead=patients_ahead)

@app.route('/patient/hospitals')
@role_required('PATIENT')
def patient_hospitals():
    query_str = request.args.get('q', '').strip()
    dept = request.args.get('dept', '').strip()
    
    hospitals_query = Hospital.query
    if query_str:
        hospitals_query = hospitals_query.filter((Hospital.name.contains(query_str)) | (Hospital.city.contains(query_str)))
        
    hospitals = hospitals_query.all()
    return render_template('patient/hospitals.html', hospitals=hospitals)

@app.route('/patient/hospital/<int:hospital_id>')
@role_required('PATIENT')
def patient_hospital_detail(hospital_id):
    hospital = Hospital.query.get_or_404(hospital_id)
    return render_template('patient/hospital_detail.html', hospital=hospital)

@app.route('/patient/profile', methods=['GET', 'POST'])
@role_required('PATIENT')
def patient_profile():
    patient = current_user.patient_profile
    if not patient:
        patient = Patient(user_id=current_user.id, age=30, gender='Unspecified', blood_group='Unknown')
        db.session.add(patient)
        db.session.commit()

    if request.method == 'POST':
        current_user.name = request.form.get('name', current_user.name).strip()
        current_user.phone = request.form.get('phone', current_user.phone).strip()
        patient.age = int(request.form.get('age', patient.age))
        patient.gender = request.form.get('gender', patient.gender)
        patient.blood_group = request.form.get('blood_group', patient.blood_group)
        patient.medical_history = request.form.get('medical_history', '').strip()
        db.session.commit()
        flash('Health profile updated successfully!', 'success')
        return redirect(url_for('patient_profile'))

    return render_template('patient/profile.html', patient=patient)

@app.route('/patient/reports', methods=['GET', 'POST'])
@role_required('PATIENT')
def patient_reports():
    patient = current_user.patient_profile
    if not patient:
        patient = Patient(user_id=current_user.id, age=30, gender='Unspecified', blood_group='Unknown')
        db.session.add(patient)
        db.session.commit()

    upload_dir = os.path.join(app.static_folder, 'uploads', 'reports')
    os.makedirs(upload_dir, exist_ok=True)

    if request.method == 'POST':
        report_name = request.form.get('report_name', 'Diagnostic Report').strip()
        report_date = request.form.get('report_date', datetime.date.today().strftime('%Y-%m-%d'))
        file_obj = request.files.get('report_file')

        if file_obj and file_obj.filename:
            ext = file_obj.filename.rsplit('.', 1)[-1].lower() if '.' in file_obj.filename else 'pdf'
            filename = f"report_{patient.id}_{int(datetime.datetime.utcnow().timestamp())}.{ext}"
            file_path = os.path.join(upload_dir, filename)
            file_obj.save(file_path)

            doc = Doctor.query.first()
            hosp = Hospital.query.first()

            rec = MedicalRecord(
                patient_id=patient.id,
                doctor_id=doc.id if doc else 1,
                hospital_id=hosp.id if hosp else 1,
                record_date=report_date,
                diagnosis_notes=report_name,
                report_file=filename,
                report_ai_summary=f"Report '{report_name}' uploaded. No critical anomalies flagged."
            )
            db.session.add(rec)
            db.session.commit()
            flash('Medical lab report uploaded successfully!', 'success')
            return redirect(url_for('patient_reports'))

    reports = MedicalRecord.query.filter_by(patient_id=patient.id).filter(MedicalRecord.report_file.isnot(None)).all()
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('patient/reports.html', reports=reports, today_str=today_str)

@app.route('/patient/appointments', methods=['GET', 'POST'])
@role_required('PATIENT')
def patient_appointments():
    patient = current_user.patient_profile
    if not patient:
        patient = Patient(user_id=current_user.id, age=30, gender='Unspecified', blood_group='Unknown')
        db.session.add(patient)
        db.session.commit()

    if request.method == 'POST':
        hospital_id = int(request.form.get('hospital_id'))
        department = request.form.get('department')
        doctor_id_val = request.form.get('doctor_id')
        doctor_id = int(doctor_id_val) if doctor_id_val else None
        appointment_date = request.form.get('appointment_date')
        time_slot = request.form.get('time_slot')
        symptoms = request.form.get('symptoms', '')

        # Evaluate Triage Priority
        triage_eval = triage_engine.evaluate_triage(
            age=patient.age,
            category=department,
            selected_symptoms=symptoms
        )
        priority = triage_eval['priority']
        urgency_level = triage_eval['urgency_level']

        # Generate unique code and token
        app_count = Appointment.query.count()
        app_code = f"APP-{1000 + app_count + 1}"
        token_code = f"{department[0].upper()}-{100 + app_count + 1}"

        app_obj = Appointment(
            appointment_code=app_code,
            patient_id=patient.id,
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            department=department,
            appointment_date=appointment_date,
            time_slot=time_slot,
            symptoms=symptoms,
            priority=priority,
            urgency_level=urgency_level,
            token_number=token_code,
            status='WAITING'
        )
        db.session.add(app_obj)
        db.session.commit()

        token_obj = QueueToken(
            appointment_id=app_obj.id,
            hospital_id=hospital_id,
            token_code=token_code,
            priority=priority,
            status='WAITING'
        )
        db.session.add(token_obj)

        notif = Notification(
            user_id=current_user.id,
            message=f"Appointment {app_code} confirmed at {app_obj.hospital.name}. Token: {token_code}.",
            notification_type='APPOINTMENT'
        )
        db.session.add(notif)
        db.session.commit()

        flash(f"Appointment booked! Your OPD Queue Token is {token_code} (Priority {priority}).", "success")
        return redirect(url_for('patient_queue'))

    hospitals = Hospital.query.all()
    doctors = Doctor.query.all()
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.created_at.desc()).all()
    selected_hospital_id = request.args.get('hospital_id', type=int)
    today_str = datetime.date.today().strftime('%Y-%m-%d')

    return render_template('patient/appointments.html',
                           hospitals=hospitals,
                           doctors=doctors,
                           appointments=appointments,
                           selected_hospital_id=selected_hospital_id,
                           today_str=today_str)

@app.route('/patient/appointment/cancel/<int:appointment_id>', methods=['POST'])
@role_required('PATIENT')
def patient_appointment_cancel(appointment_id):
    app_obj = Appointment.query.get_or_404(appointment_id)
    app_obj.status = 'CANCELLED'
    if app_obj.queue_token:
        app_obj.queue_token.status = 'CANCELLED'
    db.session.commit()
    flash(f"Appointment {app_obj.appointment_code} cancelled successfully.", "info")
    return redirect(url_for('patient_appointments'))

@app.route('/patient/queue')
@role_required('PATIENT')
def patient_queue():
    patient = current_user.patient_profile
    active_app = Appointment.query.filter_by(patient_id=patient.id).filter(Appointment.status.in_(['WAITING', 'IN_CONSULTATION'])).order_by(Appointment.created_at.desc()).first()
    
    patients_ahead = 0
    estimated_wait = 0

    if active_app and active_app.queue_token:
        ahead = QueueToken.query.filter_by(hospital_id=active_app.hospital_id, status='WAITING')\
            .filter(QueueToken.priority >= active_app.priority)\
            .filter(QueueToken.id < active_app.queue_token.id).all()
        patients_ahead = len(ahead)
        estimated_wait = max(5, patients_ahead * 10)

    return render_template('patient/queue.html',
                           active_appointment=active_app,
                           patients_ahead=patients_ahead,
                           estimated_wait_min=estimated_wait)

@app.route('/patient/triage', methods=['GET', 'POST'])
@role_required('PATIENT')
def patient_triage():
    triage_result = None
    if request.method == 'POST':
        age = request.form.get('age')
        category = request.form.get('category')
        symptoms = request.form.get('symptoms')
        duration_days = request.form.get('duration_days', 1)

        triage_result = triage_engine.evaluate_triage(
            age=age,
            category=category,
            selected_symptoms=symptoms,
            duration_days=duration_days
        )

    categories = triage_engine.symptoms_map if isinstance(triage_engine.symptoms_map, list) else [{'name': k} for k in triage_engine.symptoms_map.keys()]
    return render_template('patient/triage.html', categories=categories, triage_result=triage_result)

@app.route('/patient/assistant')
@role_required('PATIENT')
def patient_assistant():
    return render_template('patient/assistant.html')

@app.route('/api/assistant/chat', methods=['POST'])
def api_assistant_chat():
    data = request.get_json() or {}
    message = data.get('message', '').lower()

    if 'chest pain' in message or 'heart' in message:
        reply = "Chest pain can be serious. If severe, please visit Emergency immediately or call local emergency dispatch. For OPD consultations, select Cardiology / Heart department."
    elif 'fever' in message or 'cough' in message or 'covid' in message:
        reply = "For persistent fever or cough, we recommend booking a General Physician consultation or performing an AI Triage evaluation."
    elif 'bed' in message or 'room' in message:
        reply = "You can view live real-time General, ICU, Emergency bed and Private room availability under 'Find Hospitals' or 'Emergency' in the sidebar."
    elif 'token' in message or 'queue' in message:
        reply = "MEDQ automatically assigns a digital priority queue token (P1 to P5) when you schedule an appointment. You can track wait times live under 'Live Queue'."
    else:
        reply = "I am your MEDQ Healthcare Assistant. You can ask me about hospital departments, live bed availability, digital queue tokens, or symptom triage!"

    return jsonify({'reply': reply})

@app.route('/patient/emergency')
@role_required('PATIENT')
def patient_emergency():
    hospitals = Hospital.query.filter(Hospital.emergency_beds_avail > 0).all()
    if not hospitals:
        hospitals = Hospital.query.all()
    return render_template('patient/emergency.html', emergency_hospitals=hospitals)

# ---------------------------------------------------------
# DOCTOR PORTAL ROUTES
# ---------------------------------------------------------

@app.route('/doctor/dashboard')
@app.route('/doctor/queue', endpoint='doctor_queue')
@role_required('DOCTOR')
def doctor_dashboard():
    doctor = current_user.doctor_profile
    if not doctor:
        flash('Doctor profile not configured.', 'error')
        return redirect(url_for('home'))

    waiting_tokens = QueueToken.query.filter_by(hospital_id=doctor.hospital_id, status='WAITING')\
        .order_by(QueueToken.priority.desc(), QueueToken.id.asc()).all()
        
    completed_tokens = QueueToken.query.filter_by(hospital_id=doctor.hospital_id, status='COMPLETED').all()

    return render_template('doctor/dashboard.html',
                           doctor_profile=doctor,
                           waiting_tokens=waiting_tokens,
                           completed_tokens=completed_tokens)

@app.route('/doctor/consultation/<int:appointment_id>', methods=['GET', 'POST'])
@role_required('DOCTOR')
def doctor_consultation(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    doctor = current_user.doctor_profile

    if request.method == 'POST':
        notes = request.form.get('diagnosis_notes', '')
        instructions = request.form.get('instructions', '')
        
        med_names = request.form.getlist('med_name[]')
        med_dosages = request.form.getlist('med_dosage[]')
        med_freqs = request.form.getlist('med_freq[]')
        med_durations = request.form.getlist('med_duration[]')

        # Build Prescription
        med_list = []
        for i in range(len(med_names)):
            if med_names[i].strip():
                med_list.append({
                    'name': med_names[i],
                    'dosage': med_dosages[i] if i < len(med_dosages) else '',
                    'frequency': med_freqs[i] if i < len(med_freqs) else '',
                    'duration': med_durations[i] if i < len(med_durations) else ''
                })

        presc = Prescription(
            appointment_id=appointment.id,
            patient_id=appointment.patient_id,
            doctor_id=doctor.id,
            medicines_json=json.dumps(med_list),
            instructions=instructions
        )
        db.session.add(presc)

        # Record Medical Record Entry
        record = MedicalRecord(
            patient_id=appointment.patient_id,
            doctor_id=doctor.id,
            hospital_id=appointment.hospital_id,
            record_date=datetime.date.today().strftime('%Y-%m-%d'),
            diagnosis_notes=notes,
            symptoms=appointment.symptoms,
            prescription_summary=json.dumps(med_list)
        )
        db.session.add(record)

        # Update Appointment & Token Status
        appointment.status = 'COMPLETED'
        if appointment.queue_token:
            appointment.queue_token.status = 'COMPLETED'

        db.session.commit()
        flash('Consultation completed and prescription generated!', 'success')
        return redirect(url_for('doctor_dashboard'))

    # Mark as IN_CONSULTATION when doctor opens session
    appointment.status = 'IN_CONSULTATION'
    if appointment.queue_token:
        appointment.queue_token.status = 'IN_CONSULTATION'
    db.session.commit()

    return render_template('doctor/consultation.html', appointment=appointment)

@app.route('/doctor/prescriptions')
@role_required('DOCTOR')
def doctor_prescriptions():
    doctor = current_user.doctor_profile
    prescriptions = Prescription.query.filter_by(doctor_id=doctor.id).all()
    return render_template('doctor/prescriptions.html', prescriptions=prescriptions)

# ---------------------------------------------------------
# HOSPITAL ADMIN PORTAL ROUTES
# ---------------------------------------------------------

@app.route('/hospital/dashboard')
@role_required('HOSPITAL_ADMIN')
def hospital_dashboard():
    hospital = Hospital.query.first()
    if not hospital:
        hospital = Hospital(name='City Care Hospital', address='Main Ave', city='Central City')
        db.session.add(hospital)
        db.session.commit()

    active_queue = QueueToken.query.filter_by(hospital_id=hospital.id, status='WAITING').all()
    low_stock = Medicine.query.filter(Medicine.hospital_id==hospital.id, Medicine.quantity <= Medicine.min_stock).all()

    return render_template('hospital/dashboard.html',
                           hospital=hospital,
                           active_queue=active_queue,
                           low_stock_count=len(low_stock))

@app.route('/hospital/beds', methods=['GET', 'POST'])
@role_required('HOSPITAL_ADMIN')
def hospital_beds():
    hospital = Hospital.query.first()
    if request.method == 'POST':
        hospital.general_beds_avail = int(request.form.get('general_avail'))
        hospital.icu_beds_avail = int(request.form.get('icu_avail'))
        hospital.emergency_beds_avail = int(request.form.get('emergency_avail'))
        hospital.private_rooms_avail = int(request.form.get('private_avail'))
        db.session.commit()
        flash('Hospital bed capacities updated live!', 'success')
        return redirect(url_for('hospital_beds'))

    return render_template('hospital/beds.html', hospital=hospital)

@app.route('/hospital/inventory', methods=['GET', 'POST'])
@role_required('HOSPITAL_ADMIN')
def hospital_inventory():
    hospital = Hospital.query.first()
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        batch_no = request.form.get('batch_no')
        quantity = int(request.form.get('quantity'))
        min_stock = int(request.form.get('min_stock'))
        unit_price = float(request.form.get('unit_price'))

        med = Medicine(
            hospital_id=hospital.id,
            name=name,
            category=category,
            batch_no=batch_no,
            quantity=quantity,
            min_stock=min_stock,
            unit_price=unit_price
        )
        db.session.add(med)
        db.session.commit()
        flash('New medicine batch added to pharmacy inventory.', 'success')
        return redirect(url_for('hospital_inventory'))

    medicines = Medicine.query.filter_by(hospital_id=hospital.id).all()
    predictions = [inventory_engine.predict_demand_and_shortage(med) for med in medicines]

    return render_template('hospital/inventory.html',
                           hospital=hospital,
                           medicines=medicines,
                           inventory_predictions=predictions)

@app.route('/hospital/inventory/adjust/<int:medicine_id>', methods=['POST'])
@role_required('HOSPITAL_ADMIN')
def hospital_inventory_adjust(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    change = int(request.form.get('change_qty', 0))
    med.quantity = max(0, med.quantity + change)
    db.session.commit()
    flash(f"Adjusted stock for {med.name}. New total: {med.quantity}", "info")
    return redirect(url_for('hospital_inventory'))

@app.route('/hospital/inventory/delete/<int:medicine_id>', methods=['POST'])
@role_required('HOSPITAL_ADMIN')
def hospital_inventory_delete(medicine_id):
    med = Medicine.query.get_or_404(medicine_id)
    name = med.name
    db.session.delete(med)
    db.session.commit()
    flash(f"Removed {name} from pharmacy inventory.", "info")
    return redirect(url_for('hospital_inventory'))

@app.route('/hospital/analytics')
@role_required('HOSPITAL_ADMIN')
def hospital_analytics():
    hospital = Hospital.query.first()
    return render_template('hospital/dashboard.html', hospital=hospital, active_queue=[], low_stock_count=0)

# ---------------------------------------------------------
# SYSTEM ADMIN PORTAL ROUTES
# ---------------------------------------------------------

@app.route('/admin/dashboard')
@role_required('SYSTEM_ADMIN')
def admin_dashboard():
    users = User.query.order_by(User.id.desc()).all()
    hospitals = Hospital.query.all()
    total_appointments = Appointment.query.count()
    
    return render_template('admin/dashboard.html',
                           users=users,
                           hospitals=hospitals,
                           total_users=len(users),
                           total_hospitals=len(hospitals),
                           total_appointments=total_appointments)

@app.route('/admin/users')
@role_required('SYSTEM_ADMIN')
def admin_users():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users, hospitals=[], total_users=len(users), total_hospitals=0, total_appointments=0)

@app.route('/admin/hospitals')
@role_required('SYSTEM_ADMIN')
def admin_hospitals():
    hospitals = Hospital.query.all()
    return render_template('admin/dashboard.html', users=[], hospitals=hospitals, total_users=0, total_hospitals=len(hospitals), total_appointments=0)

# ---------------------------------------------------------
# BACKWARD COMPATIBLE LEGACY ROUTES & APIS
# ---------------------------------------------------------

@app.route('/add_appointment', methods=['POST'])
def legacy_add_appointment():
    data = request.get_json() or {}
    category = data.get('category', 'General Physician')
    age = data.get('age', 30)
    symptoms = data.get('symptoms', '')
    
    triage_eval = triage_engine.evaluate_triage(age=age, category=category, selected_symptoms=symptoms)
    priority = triage_eval['priority']
    
    return jsonify({
        'status': 'success',
        'priority': priority,
        'message': 'Appointment priority calculated',
        'urgency_level': triage_eval['urgency_level']
    })

@app.route('/get_appointments', methods=['GET'])
def legacy_get_appointments():
    appointments = Appointment.query.all()
    results = []
    for a in appointments:
        results.append({
            'name': a.patient.user.name if a.patient and a.patient.user else 'Patient',
            'category': a.department,
            'priority': a.priority,
            'status': a.status,
            'token': a.token_number
        })
    return jsonify(results)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
