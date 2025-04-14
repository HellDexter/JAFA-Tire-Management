from flask import Blueprint, jsonify, request
from models import db, Tire, Vehicle, TireType, Supplier, ServiceAction, VehicleCombination, PurchaseRequest
from datetime import datetime
from flask_login import login_required, current_user

# Vytvoření API blueprint
api = Blueprint('api', __name__)

# API pro pneumatiky
@api.route('/tires', methods=['GET'])
@login_required
def get_tires():
    tires = Tire.query.all()
    result = []
    for tire in tires:
        result.append({
            'id': tire.id,
            'serial_number': tire.serial_number,
            'status': tire.status,
            'current_tread_depth': tire.current_tread_depth,
            'total_mileage': tire.total_mileage,
            'tire_type': {
                'id': tire.tire_type.id,
                'brand': tire.tire_type.brand,
                'model': tire.tire_type.model,
                'size': tire.tire_type.size
            } if tire.tire_type else None,
            'position': {
                'id': tire.position.id,
                'vehicle_id': tire.position.vehicle_id if hasattr(tire.position, 'vehicle') else None,
                'position_code': tire.position.position_code,
                'vehicle_registration': tire.position.vehicle.registration_number if tire.position and tire.position.vehicle else None
            } if tire.position else None
        })
    return jsonify({'tires': result})

@api.route('/tires/<int:tire_id>', methods=['GET'])
@login_required
def get_tire(tire_id):
    tire = Tire.query.get_or_404(tire_id)
    result = {
        'id': tire.id,
        'serial_number': tire.serial_number,
        'status': tire.status,
        'current_tread_depth': tire.current_tread_depth,
        'total_mileage': tire.total_mileage,
        'tire_type': {
            'id': tire.tire_type.id,
            'brand': tire.tire_type.brand,
            'model': tire.tire_type.model,
            'size': tire.tire_type.size
        } if tire.tire_type else None,
        'position': {
            'id': tire.position.id,
            'vehicle_id': tire.position.vehicle_id if hasattr(tire.position, 'vehicle') else None,
            'position_code': tire.position.position_code,
            'vehicle_registration': tire.position.vehicle.registration_number if tire.position and tire.position.vehicle else None
        } if tire.position else None,
        'history': [{
            'id': h.id,
            'action_type': h.action_type,
            'action_date': h.action_date.strftime('%Y-%m-%d %H:%M:%S'),
            'mileage_at_action': h.mileage_at_action,
            'tread_depth_at_action': h.tread_depth_at_action
        } for h in tire.history]
    }
    return jsonify(result)

# API pro vozidla
@api.route('/vehicles', methods=['GET'])
@login_required
def get_vehicles():
    vehicle_type = request.args.get('type')
    if vehicle_type:
        vehicles = Vehicle.query.filter_by(vehicle_type=vehicle_type).all()
    else:
        vehicles = Vehicle.query.all()
    
    result = []
    for vehicle in vehicles:
        result.append({
            'id': vehicle.id,
            'registration_number': vehicle.registration_number,
            'vehicle_type': vehicle.vehicle_type,
            'brand': vehicle.brand,
            'model': vehicle.model,
            'current_mileage': vehicle.current_mileage,
            'combination_id': vehicle.combination_id
        })
    return jsonify({'vehicles': result})

@api.route('/vehicles/<int:vehicle_id>', methods=['GET'])
@login_required
def get_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    tire_positions = []
    for position in vehicle.tire_positions:
        tire_data = None
        if position.tire:
            tire_data = {
                'id': position.tire.id,
                'serial_number': position.tire.serial_number,
                'current_tread_depth': position.tire.current_tread_depth,
                'tire_type': {
                    'brand': position.tire.tire_type.brand,
                    'model': position.tire.tire_type.model,
                    'size': position.tire.tire_type.size
                } if position.tire.tire_type else None
            }
        
        tire_positions.append({
            'id': position.id,
            'position_code': position.position_code,
            'position_description': position.position_description,
            'tire': tire_data
        })
    
    result = {
        'id': vehicle.id,
        'registration_number': vehicle.registration_number,
        'vehicle_type': vehicle.vehicle_type,
        'brand': vehicle.brand,
        'model': vehicle.model,
        'year_of_manufacture': vehicle.year_of_manufacture,
        'vin': vehicle.vin,
        'current_mileage': vehicle.current_mileage,
        'combination': {
            'id': vehicle.combination.id,
            'name': vehicle.combination.name
        } if vehicle.combination else None,
        'tire_positions': tire_positions
    }
    return jsonify(result)

# API pro kombinace vozidel
@api.route('/combinations', methods=['GET'])
@login_required
def get_combinations():
    combinations = VehicleCombination.query.all()
    result = []
    for combo in combinations:
        vehicles = []
        for vehicle in combo.vehicles:
            vehicles.append({
                'id': vehicle.id,
                'registration_number': vehicle.registration_number,
                'vehicle_type': vehicle.vehicle_type
            })
        
        result.append({
            'id': combo.id,
            'name': combo.name,
            'description': combo.description,
            'is_active': combo.is_active,
            'vehicles': vehicles
        })
    return jsonify({'combinations': result})

# API pro typy pneumatik
@api.route('/tire-types', methods=['GET'])
@login_required
def get_tire_types():
    tire_types = TireType.query.all()
    result = []
    for tt in tire_types:
        result.append({
            'id': tt.id,
            'brand': tt.brand,
            'model': tt.model,
            'size': tt.size,
            'usage_type': tt.usage_type,
            'price': tt.price,
            'supplier': {
                'id': tt.supplier.id,
                'name': tt.supplier.name
            } if tt.supplier else None,
            'stock_count': len([t for t in tt.tires if t.status == 'skladem'])
        })
    return jsonify({'tire_types': result})

# API pro servisní zásahy
@api.route('/service-actions', methods=['GET'])
@login_required
def get_service_actions():
    # Možnost filtrování podle data
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    query = ServiceAction.query
    if from_date:
        query = query.filter(ServiceAction.action_date >= datetime.strptime(from_date, '%Y-%m-%d'))
    if to_date:
        query = query.filter(ServiceAction.action_date <= datetime.strptime(to_date, '%Y-%m-%d'))
    
    actions = query.order_by(ServiceAction.action_date.desc()).all()
    result = []
    for action in actions:
        result.append({
            'id': action.id,
            'action_type': action.action_type,
            'action_date': action.action_date.strftime('%Y-%m-%d %H:%M:%S'),
            'description': action.description,
            'tire': {
                'id': action.tire.id,
                'serial_number': action.tire.serial_number,
                'tire_type': {
                    'brand': action.tire.tire_type.brand,
                    'model': action.tire.tire_type.model,
                    'size': action.tire.tire_type.size
                } if action.tire.tire_type else None
            } if action.tire else None,
            'technician': {
                'id': action.technician.id,
                'username': action.technician.username
            } if action.technician else None
        })
    return jsonify({'service_actions': result})

# API pro statistiky
@api.route('/stats/tires', methods=['GET'])
@login_required
def get_tire_stats():
    # Počty pneumatik podle stavu
    status_counts = {}
    statuses = db.session.query(Tire.status, db.func.count(Tire.id)).group_by(Tire.status).all()
    for status, count in statuses:
        status_counts[status] = count
    
    # Počty podle typů pneumatik
    type_counts = {}
    types = db.session.query(TireType.brand, db.func.count(Tire.id)).join(Tire).group_by(TireType.brand).all()
    for brand, count in types:
        type_counts[brand] = count
    
    # Průměrná životnost pneumatik (pro ty, které již byly vyřazeny)
    avg_lifespan = db.session.query(db.func.avg(Tire.total_mileage)).filter(Tire.status == 'vyřazeno').scalar()
    
    return jsonify({
        'status_counts': status_counts,
        'type_counts': type_counts,
        'avg_lifespan_km': avg_lifespan
    })

# API pro žádosti o nákup
@api.route('/purchase-requests', methods=['GET'])
@login_required
def get_purchase_requests():
    status = request.args.get('status')
    query = PurchaseRequest.query
    
    if status:
        query = query.filter_by(status=status)
    
    requests = query.order_by(PurchaseRequest.request_date.desc()).all()
    result = []
    
    for pr in requests:
        result.append({
            'id': pr.id,
            'tire_type': {
                'id': pr.tire_type.id,
                'brand': pr.tire_type.brand,
                'model': pr.tire_type.model,
                'size': pr.tire_type.size
            } if pr.tire_type else None,
            'quantity': pr.quantity,
            'status': pr.status,
            'priority': pr.priority,
            'request_date': pr.request_date.strftime('%Y-%m-%d'),
            'requester': {
                'id': pr.requester.id,
                'username': pr.requester.username
            } if pr.requester else None
        })
    
    return jsonify({'purchase_requests': result})

# Funkce pro registraci API do hlavní aplikace
def register_api(app):
    app.register_blueprint(api, url_prefix='/api')
