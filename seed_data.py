import datetime
from app import app
from models import db, User, Hospital, Doctor, Patient, BedResource, Appointment, QueueToken, MedicalRecord, Prescription, Medicine, InventoryTransaction, Notification

def seed_database():
    with app.app_context():
        db.drop_all()
        db.create_all()

        print("Creating initial seed data...")

        # 1. Create Core Users for each role
        admin_user = User(
            email='admin@medq.com',
            role='SYSTEM_ADMIN',
            name='Dr. Arthur Pendelton',
            phone='+1 800-555-0100'
        )
        admin_user.set_password('admin123')

        hospital_admin_user = User(
            email='hospital@medq.com',
            role='HOSPITAL_ADMIN',
            name='Sarah Jenkins (Admin)',
            phone='+1 800-555-0101'
        )
        hospital_admin_user.set_password('hospital123')

        doctor_user1 = User(
            email='doctor@medq.com',
            role='DOCTOR',
            name='Dr. Rajesh Sharma',
            phone='+1 800-555-0102'
        )
        doctor_user1.set_password('doctor123')

        doctor_user2 = User(
            email='dr.ananya@medq.com',
            role='DOCTOR',
            name='Dr. Ananya Roy',
            phone='+1 800-555-0103'
        )
        doctor_user2.set_password('doctor123')

        patient_user1 = User(
            email='patient@medq.com',
            role='PATIENT',
            name='Ramesh Kumar',
            phone='+91 9876543210'
        )
        patient_user1.set_password('patient123')

        patient_user2 = User(
            email='priya@medq.com',
            role='PATIENT',
            name='Priya Patel',
            phone='+91 9876543211'
        )
        patient_user2.set_password('patient123')

        db.session.add_all([admin_user, hospital_admin_user, doctor_user1, doctor_user2, patient_user1, patient_user2])
        db.session.commit()

        # 2. Create Hospitals
        hospitals = [
            Hospital(
                name='City Care Multi-Specialty Hospital',
                address='124 Healthcare Boulevard, Central City',
                city='Central City',
                rating=4.8,
                contact_phone='+91 40 2345 6789',
                contact_email='contact@citycarehospital.org',
                image_url='/static/images/hospital1.jpg',
                general_beds_total=60, general_beds_avail=24,
                icu_beds_total=15, icu_beds_avail=4,
                emergency_beds_total=10, emergency_beds_avail=3,
                private_rooms_total=25, private_rooms_avail=8
            ),
            Hospital(
                name='Apex Heart & Trauma Center',
                address='45 Cardiac Avenue, North Wing',
                city='North Wing',
                rating=4.9,
                contact_phone='+91 40 2345 9999',
                contact_email='emergency@apexheart.org',
                image_url='/static/images/hospital2.jpg',
                general_beds_total=40, general_beds_avail=12,
                icu_beds_total=20, icu_beds_avail=2,
                emergency_beds_total=15, emergency_beds_avail=5,
                private_rooms_total=15, private_rooms_avail=4
            ),
            Hospital(
                name='Lifeline Children & General Hospital',
                address='88 Pediatric Drive, East District',
                city='East District',
                rating=4.6,
                contact_phone='+91 40 8888 1111',
                contact_email='info@lifelinegen.org',
                image_url='/static/images/hospital1.jpg',
                general_beds_total=50, general_beds_avail=30,
                icu_beds_total=10, icu_beds_avail=6,
                emergency_beds_total=8, emergency_beds_avail=4,
                private_rooms_total=10, private_rooms_avail=5
            ),
            Hospital(
                name='St. Jude Women & Wellness Clinic',
                address='12 Rose Lane, West Suburbs',
                city='West Suburbs',
                rating=4.7,
                contact_phone='+91 40 7777 2222',
                contact_email='care@stjudewomens.org',
                image_url='/static/images/hospital2.jpg',
                general_beds_total=30, general_beds_avail=18,
                icu_beds_total=5, icu_beds_avail=3,
                emergency_beds_total=5, emergency_beds_avail=2,
                private_rooms_total=12, private_rooms_avail=6
            ),
            Hospital(
                name='Metro Emergency Super Specialty',
                address='1 Highway Junction, Downtown',
                city='Downtown',
                rating=4.9,
                contact_phone='+91 40 1080 0000',
                contact_email='trauma@metroemergency.org',
                image_url='/static/images/hospital1.jpg',
                general_beds_total=100, general_beds_avail=45,
                icu_beds_total=35, icu_beds_avail=8,
                emergency_beds_total=25, emergency_beds_avail=7,
                private_rooms_total=30, private_rooms_avail=12
            )
        ]
        db.session.add_all(hospitals)
        db.session.commit()

        # 3. Create Doctors & Patient Profiles
        doc1 = Doctor(
            user_id=doctor_user1.id,
            hospital_id=hospitals[0].id,
            department='General Physician',
            specialization='Internal Medicine & Diagnostics',
            experience_years=12,
            avg_consultation_time_min=8
        )
        doc2 = Doctor(
            user_id=doctor_user2.id,
            hospital_id=hospitals[1].id,
            department='Heart',
            specialization='Interventional Cardiology',
            experience_years=15,
            avg_consultation_time_min=12
        )
        db.session.add_all([doc1, doc2])

        p1 = Patient(user_id=patient_user1.id, age=42, gender='Male', blood_group='B+', medical_history='Hypertension, Mild Asthma')
        p2 = Patient(user_id=patient_user2.id, age=29, gender='Female', blood_group='O+', medical_history='No chronic illness')
        db.session.add_all([p1, p2])
        db.session.commit()

        # 4. Create Bed Resources breakdown
        for h in hospitals:
            br_gen = BedResource(hospital_id=h.id, bed_type='GENERAL', total=h.general_beds_total, occupied=h.general_beds_total - h.general_beds_avail)
            br_icu = BedResource(hospital_id=h.id, bed_type='ICU', total=h.icu_beds_total, occupied=h.icu_beds_total - h.icu_beds_avail)
            br_emg = BedResource(hospital_id=h.id, bed_type='EMERGENCY', total=h.emergency_beds_total, occupied=h.emergency_beds_total - h.emergency_beds_avail)
            br_pvt = BedResource(hospital_id=h.id, bed_type='PRIVATE', total=h.private_rooms_total, occupied=h.private_rooms_total - h.private_rooms_avail)
            db.session.add_all([br_gen, br_icu, br_emg, br_pvt])

        # 5. Create Medicines
        meds = [
            Medicine(hospital_id=hospitals[0].id, name='Paracetamol 650mg', category='Analgesic', batch_no='PCM-2026-09', quantity=500, min_stock=100, unit_price=2.5, expiry_date='2027-12-31'),
            Medicine(hospital_id=hospitals[0].id, name='Amoxicillin 500mg', category='Antibiotic', batch_no='AMX-2026-04', quantity=120, min_stock=150, unit_price=12.0, expiry_date='2027-06-30'),
            Medicine(hospital_id=hospitals[0].id, name='Insulin Glargine 100IU', category='Diabetes', batch_no='INS-2026-01', quantity=15, min_stock=30, unit_price=450.0, expiry_date='2026-11-15'),
            Medicine(hospital_id=hospitals[0].id, name='Ibuprofen 400mg', category='Anti-inflammatory', batch_no='IBU-2026-11', quantity=350, min_stock=80, unit_price=5.0, expiry_date='2028-03-31'),
            Medicine(hospital_id=hospitals[0].id, name='Azithromycin 500mg', category='Antibiotic', batch_no='AZI-2026-07', quantity=8, min_stock=25, unit_price=65.0, expiry_date='2026-10-31'),
            Medicine(hospital_id=hospitals[0].id, name='Metformin 500mg', category='Diabetes', batch_no='MET-2026-03', quantity=600, min_stock=200, unit_price=4.0, expiry_date='2027-09-30')
        ]
        db.session.add_all(meds)
        db.session.commit()

        # 6. Sample Initial Appointment & Queue Token
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        app1 = Appointment(
            appointment_code='APP-1001',
            patient_id=p1.id,
            doctor_id=doc1.id,
            hospital_id=hospitals[0].id,
            department='General Physician',
            appointment_date=today_str,
            time_slot='10:30 AM',
            status='WAITING',
            priority=4,
            urgency_level='ORANGE',
            symptoms='Persistent High Fever, Cough, Shortness of Breath',
            category='General Physician',
            token_number='A-101'
        )
        db.session.add(app1)
        db.session.commit()

        token1 = QueueToken(
            appointment_id=app1.id,
            hospital_id=hospitals[0].id,
            token_code='A-101',
            priority=4,
            status='WAITING'
        )
        db.session.add(token1)

        # 7. Notifications
        n1 = Notification(user_id=patient_user1.id, message='Your appointment APP-1001 at City Care is confirmed. Token: A-101.', notification_type='APPOINTMENT')
        n2 = Notification(user_id=hospital_admin_user.id, message='Low stock alert: Insulin Glargine & Azithromycin below minimum safety threshold.', notification_type='INVENTORY')
        db.session.add_all([n1, n2])

        db.session.commit()
        print("Database successfully seeded!")

if __name__ == '__main__':
    seed_database()
