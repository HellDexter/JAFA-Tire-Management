from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='technician')  # admin, manager, technician
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vztahy
    tire_types = db.relationship('TireType', backref='supplier', lazy=True)
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class TireType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    size = db.Column(db.String(20), nullable=False)  # např. "315/80 R22.5"
    usage_type = db.Column(db.String(50))  # např. "hnací", "řídící", "návěsová"
    price = db.Column(db.Float)
    avg_lifespan_km = db.Column(db.Integer)  # Průměrná životnost v km
    min_stock_level = db.Column(db.Integer, default=2)  # Minimální skladové zásoby
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vztahy
    tires = db.relationship('Tire', backref='tire_type', lazy=True)
    
    def __repr__(self):
        return f'<TireType {self.brand} {self.model} {self.size}>'

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(20), nullable=False, unique=True)
    vehicle_type = db.Column(db.String(20), nullable=False)  # "tahač" nebo "návěs"
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    year_of_manufacture = db.Column(db.Integer)
    vin = db.Column(db.String(17))
    current_mileage = db.Column(db.Integer)  # Aktuální nájezd v km
    last_mileage_update = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vztahy - identifikace dvojice tahač + návěs
    combination_id = db.Column(db.Integer, db.ForeignKey('vehicle_combination.id'), nullable=True)
    tire_positions = db.relationship('TirePosition', backref='vehicle', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Vehicle {self.registration_number} ({self.vehicle_type})>'

class VehicleCombination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vztahy
    vehicles = db.relationship('Vehicle', backref='combination', lazy=True)
    
    def __repr__(self):
        return f'<VehicleCombination {self.name}>'

class Tire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(50), nullable=False, unique=True)
    tire_type_id = db.Column(db.Integer, db.ForeignKey('tire_type.id'), nullable=False)
    manufacture_date = db.Column(db.Date)
    purchase_date = db.Column(db.Date)
    status = db.Column(db.String(20), nullable=False, default='skladem')  # skladem, namontováno, vyřazeno
    initial_tread_depth = db.Column(db.Float)  # Počáteční hloubka dezénu v mm
    current_tread_depth = db.Column(db.Float)  # Aktuální hloubka dezénu v mm
    total_mileage = db.Column(db.Integer, default=0)  # Celkový nájezd v km
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Vztahy
    position_id = db.Column(db.Integer, db.ForeignKey('tire_position.id'), nullable=True)
    history = db.relationship('TireHistory', backref='tire', lazy=True, cascade="all, delete-orphan")
    service_actions = db.relationship('ServiceAction', backref='tire', lazy=True)
    
    def __repr__(self):
        return f'<Tire {self.serial_number}>'

class TirePosition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    position_code = db.Column(db.String(10), nullable=False)  # např. "L1", "P3", atd.
    position_description = db.Column(db.String(100))  # např. "Levá přední"
    
    # Vztahy
    tire = db.relationship('Tire', backref='position', uselist=False)
    
    def __repr__(self):
        vehicle_info = self.vehicle.registration_number if hasattr(self, 'vehicle') and self.vehicle else "Unknown vehicle"
        return f'<TirePosition {self.position_code} on {vehicle_info}>'

class TireHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tire_id = db.Column(db.Integer, db.ForeignKey('tire.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=True)
    position_code = db.Column(db.String(10))
    action_type = db.Column(db.String(20), nullable=False)  # montáž, demontáž
    action_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    mileage_at_action = db.Column(db.Integer)  # Nájezd vozidla při akci
    tread_depth_at_action = db.Column(db.Float)  # Hloubka dezénu při akci
    action_reason = db.Column(db.String(100))  # např. "opotřebení", "poškození", "preventivní výměna"
    note = db.Column(db.Text)
    technician_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Vztahy
    vehicle = db.relationship('Vehicle', backref='tire_history_entries')
    photos = db.relationship('TirePhoto', backref='history_entry', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<TireHistory {self.action_type} on {self.action_date}>'

class TirePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey('tire_history.id'), nullable=False)
    photo_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    caption = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<TirePhoto {self.id} for history {self.history_id}>'

class ServiceAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tire_id = db.Column(db.Integer, db.ForeignKey('tire.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)  # např. "prohlídka", "oprava"
    action_date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text, nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    note = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ServiceAction {self.action_type} on {self.action_date}>'

class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tire_type_id = db.Column(db.Integer, db.ForeignKey('tire_type.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    priority = db.Column(db.String(20), default='normal')  # nízká, normální, vysoká, urgentní
    status = db.Column(db.String(20), default='požadováno')  # požadováno, schváleno, objednáno, dodáno
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approval_date = db.Column(db.DateTime, nullable=True)
    expected_delivery_date = db.Column(db.Date, nullable=True)
    actual_delivery_date = db.Column(db.Date, nullable=True)
    note = db.Column(db.Text)
    
    # Vztahy
    tire_type = db.relationship('TireType', backref='purchase_requests')
    requester = db.relationship('User', foreign_keys=[requester_id])
    approver = db.relationship('User', foreign_keys=[approver_id])
    
    def __repr__(self):
        return f'<PurchaseRequest {self.id} for {self.quantity} tires>'
