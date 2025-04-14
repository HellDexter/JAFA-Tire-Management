from flask import render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Supplier, TireType, Tire, Vehicle, TirePosition, TireHistory, ServiceAction, PurchaseRequest, VehicleCombination, TirePhoto
from extensions import db
import os
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

def register_routes(app):
    # ===== Autentizační routy =====
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            flash('Nesprávné přihlašovací údaje.', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Byli jste úspěšně odhlášeni.', 'success')
        return redirect(url_for('login'))
    
    # ===== Dashboard =====
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Počet pneumatik podle stavu
        tires_by_status = {
            'skladem': Tire.query.filter_by(status='skladem').count(),
            'namontovano': Tire.query.filter_by(status='namontováno').count(),
            'vyrazeno': Tire.query.filter_by(status='vyřazeno').count()
        }
        
        # Pneumatiky pod minimální úrovní skladu
        low_stock_tires = db.session.query(
            TireType, 
            db.func.count(Tire.id).label('stock_count')
        ).outerjoin(
            Tire, 
            (Tire.tire_type_id == TireType.id) & (Tire.status == 'skladem')
        ).group_by(TireType.id).having(
            db.func.count(Tire.id) < TireType.min_stock_level
        ).all()
        
        # Aktivní soupravy
        active_combinations = VehicleCombination.query.filter_by(is_active=True).all()
        
        # Nedávné servisní zásahy
        recent_service_actions = ServiceAction.query.order_by(ServiceAction.action_date.desc()).limit(5).all()
        
        # Poslední pohyby pneumatik
        recent_tire_history = TireHistory.query.order_by(TireHistory.action_date.desc()).limit(5).all()
        
        return render_template(
            'dashboard.html',
            tires_by_status=tires_by_status,
            low_stock_tires=low_stock_tires,
            active_combinations=active_combinations,
            recent_service_actions=recent_service_actions,
            recent_tire_history=recent_tire_history
        )
    
    # ===== Dodavatelé =====
    @app.route('/suppliers')
    @login_required
    def list_suppliers():
        suppliers = Supplier.query.all()
        return render_template('suppliers/list.html', suppliers=suppliers)
    
    @app.route('/suppliers/add', methods=['GET', 'POST'])
    @login_required
    def add_supplier():
        if request.method == 'POST':
            supplier = Supplier(
                name=request.form.get('name'),
                contact_person=request.form.get('contact_person'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                address=request.form.get('address'),
                note=request.form.get('note')
            )
            db.session.add(supplier)
            db.session.commit()
            flash('Dodavatel byl úspěšně přidán.', 'success')
            return redirect(url_for('list_suppliers'))
        return render_template('suppliers/add.html')
    
    @app.route('/suppliers/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_supplier(id):
        supplier = Supplier.query.get_or_404(id)
        if request.method == 'POST':
            supplier.name = request.form.get('name')
            supplier.contact_person = request.form.get('contact_person')
            supplier.email = request.form.get('email')
            supplier.phone = request.form.get('phone')
            supplier.address = request.form.get('address')
            supplier.note = request.form.get('note')
            db.session.commit()
            flash('Dodavatel byl úspěšně aktualizován.', 'success')
            return redirect(url_for('list_suppliers'))
        return render_template('suppliers/edit.html', supplier=supplier)
    
    @app.route('/suppliers/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_supplier(id):
        supplier = Supplier.query.get_or_404(id)
        db.session.delete(supplier)
        db.session.commit()
        flash('Dodavatel byl úspěšně odstraněn.', 'success')
        return redirect(url_for('list_suppliers'))
    
    # ===== Typy pneumatik =====
    @app.route('/tire-types')
    @login_required
    def list_tire_types():
        tire_types = TireType.query.all()
        return render_template('tire_types/list.html', tire_types=tire_types)
    
    @app.route('/tire-types/add', methods=['GET', 'POST'])
    @login_required
    def add_tire_type():
        suppliers = Supplier.query.all()
        if request.method == 'POST':
            tire_type = TireType(
                brand=request.form.get('brand'),
                model=request.form.get('model'),
                size=request.form.get('size'),
                usage_type=request.form.get('usage_type'),
                price=float(request.form.get('price') or 0),
                avg_lifespan_km=int(request.form.get('avg_lifespan_km') or 0),
                min_stock_level=int(request.form.get('min_stock_level') or 2),
                supplier_id=int(request.form.get('supplier_id')),
                note=request.form.get('note')
            )
            db.session.add(tire_type)
            db.session.commit()
            flash('Typ pneumatiky byl úspěšně přidán.', 'success')
            return redirect(url_for('list_tire_types'))
        return render_template('tire_types/add.html', suppliers=suppliers)

    @app.route('/tire-types/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_tire_type(id):
        tire_type = TireType.query.get_or_404(id)
        suppliers = Supplier.query.all()
        if request.method == 'POST':
            tire_type.brand = request.form.get('brand')
            tire_type.model = request.form.get('model')
            tire_type.size = request.form.get('size')
            tire_type.usage_type = request.form.get('usage_type')
            tire_type.price = float(request.form.get('price') or 0)
            tire_type.avg_lifespan_km = int(request.form.get('avg_lifespan_km') or 0)
            tire_type.min_stock_level = int(request.form.get('min_stock_level') or 2)
            tire_type.supplier_id = int(request.form.get('supplier_id'))
            tire_type.note = request.form.get('note')
            db.session.commit()
            flash('Typ pneumatiky byl úspěšně aktualizován.', 'success')
            return redirect(url_for('list_tire_types'))
        return render_template('tire_types/edit.html', tire_type=tire_type, suppliers=suppliers)
    
    @app.route('/tire-types/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_tire_type(id):
        tire_type = TireType.query.get_or_404(id)
        db.session.delete(tire_type)
        db.session.commit()
        flash('Typ pneumatiky byl úspěšně odstraněn.', 'success')
        return redirect(url_for('list_tire_types'))
    
    # ===== Pneumatiky =====
    @app.route('/tires')
    @login_required
    def list_tires():
        status_filter = request.args.get('status', '')
        query = Tire.query
        if status_filter:
            query = query.filter_by(status=status_filter)
        tires = query.all()
        return render_template('tires/list.html', tires=tires, status_filter=status_filter)
    
    @app.route('/tires/add', methods=['GET', 'POST'])
    @login_required
    def add_tire():
        tire_types = TireType.query.all()
        if request.method == 'POST':
            quantity = int(request.form.get('quantity', 1))
            serial_numbers = request.form.getlist('serial_numbers[]')
            
            # Pokud nejsou zadána žádná sériová čísla, vytvoříme prázdný seznam
            if not serial_numbers:
                serial_numbers = [''] * quantity
            
            # Zajistíme, že máme správný počet sériových čísel
            while len(serial_numbers) < quantity:
                serial_numbers.append('')
            
            # Společné údaje pro všechny pneumatiky
            tire_type_id = int(request.form.get('tire_type_id'))
            manufacture_date = datetime.strptime(request.form.get('manufacture_date'), '%Y-%m-%d').date() if request.form.get('manufacture_date') else None
            purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date() if request.form.get('purchase_date') else None
            initial_tread_depth = float(request.form.get('initial_tread_depth') or 0)
            note = request.form.get('note')
            
            # Vytvoření pneumatik
            created_count = 0
            for i in range(quantity):
                serial_number = serial_numbers[i].strip() if i < len(serial_numbers) else ''
                
                # Pokud není zadáno sériové číslo, vygenerujeme náhodné (s timestampem)
                if not serial_number:
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    serial_number = f"AUTO-{timestamp}-{i+1}"
                
                # Kontrola duplicity sériového čísla
                existing_tire = Tire.query.filter_by(serial_number=serial_number).first()
                if existing_tire and serial_number.startswith('AUTO-') is False:
                    flash(f'Pneumatika s tímto sériovým číslem již existuje: {serial_number}', 'danger')
                    continue
                
                # Vytvoření a uložení pneumatiky
                tire = Tire(
                    serial_number=serial_number,
                    tire_type_id=tire_type_id,
                    manufacture_date=manufacture_date,
                    purchase_date=purchase_date,
                    status='skladem',
                    initial_tread_depth=initial_tread_depth,
                    current_tread_depth=initial_tread_depth,
                    note=note
                )
                db.session.add(tire)
                created_count += 1
            
            # Commit změn do databáze
            db.session.commit()
            
            # Informace pro uživatele
            if created_count == 1:
                flash('Pneumatika byla úspěšně přidána.', 'success')
            else:
                flash(f'Bylo úspěšně přidáno {created_count} pneumatik.', 'success')
            
            return redirect(url_for('list_tires'))
        
        return render_template('tires/add.html', tire_types=tire_types)
    
    @app.route('/tires/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_tire(id):
        tire = Tire.query.get_or_404(id)
        tire_types = TireType.query.all()
        if request.method == 'POST':
            tire.serial_number = request.form.get('serial_number')
            tire.tire_type_id = int(request.form.get('tire_type_id'))
            tire.manufacture_date = datetime.strptime(request.form.get('manufacture_date'), '%Y-%m-%d').date() if request.form.get('manufacture_date') else None
            tire.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date() if request.form.get('purchase_date') else None
            tire.current_tread_depth = float(request.form.get('current_tread_depth') or 0)
            tire.note = request.form.get('note')
            db.session.commit()
            flash('Pneumatika byla úspěšně aktualizována.', 'success')
            return redirect(url_for('list_tires'))
        return render_template('tires/edit.html', tire=tire, tire_types=tire_types)
    
    @app.route('/tires/detail/<int:id>')
    @login_required
    def tire_detail(id):
        tire = Tire.query.get_or_404(id)
        history = TireHistory.query.filter_by(tire_id=id).order_by(TireHistory.action_date.desc()).all()
        service_actions = ServiceAction.query.filter_by(tire_id=id).order_by(ServiceAction.action_date.desc()).all()
        return render_template('tires/detail.html', tire=tire, history=history, service_actions=service_actions)
    
    # ===== Vozidla =====
    @app.route('/vehicles')
    @login_required
    def list_vehicles():
        vehicle_type = request.args.get('type', '')
        query = Vehicle.query
        if vehicle_type:
            query = query.filter_by(vehicle_type=vehicle_type)
        vehicles = query.all()
        return render_template('vehicles/list.html', vehicles=vehicles, vehicle_type=vehicle_type)
    
    @app.route('/vehicles/add', methods=['GET', 'POST'])
    @login_required
    def add_vehicle():
        combinations = VehicleCombination.query.all()
        if request.method == 'POST':
            vehicle = Vehicle(
                registration_number=request.form.get('registration_number'),
                vehicle_type=request.form.get('vehicle_type'),
                brand=request.form.get('brand'),
                model=request.form.get('model'),
                year_of_manufacture=int(request.form.get('year_of_manufacture') or 0),
                vin=request.form.get('vin'),
                current_mileage=int(request.form.get('current_mileage') or 0),
                combination_id=int(request.form.get('combination_id')) if request.form.get('combination_id') else None,
                note=request.form.get('note')
            )
            db.session.add(vehicle)
            db.session.commit()
            
            # Vytvoření pozic pro pneumatiky
            positions = []
            if vehicle.vehicle_type == 'tahač':
                positions = [
                    {'code': 'L1', 'desc': 'Levá přední'},
                    {'code': 'P1', 'desc': 'Pravá přední'},
                    {'code': 'L2', 'desc': 'Levá zadní vnější'},
                    {'code': 'P2', 'desc': 'Pravá zadní vnější'},
                    {'code': 'L3', 'desc': 'Levá zadní vnitřní'},
                    {'code': 'P3', 'desc': 'Pravá zadní vnitřní'}
                ]
            elif vehicle.vehicle_type == 'návěs':
                positions = [
                    {'code': 'L1', 'desc': 'Levá přední'},
                    {'code': 'P1', 'desc': 'Pravá přední'},
                    {'code': 'L2', 'desc': 'Levá středová'},
                    {'code': 'P2', 'desc': 'Pravá středová'},
                    {'code': 'L3', 'desc': 'Levá zadní'},
                    {'code': 'P3', 'desc': 'Pravá zadní'}
                ]
            
            for pos in positions:
                position = TirePosition(
                    vehicle_id=vehicle.id,
                    position_code=pos['code'],
                    position_description=pos['desc']
                )
                db.session.add(position)
            
            db.session.commit()
            flash('Vozidlo bylo úspěšně přidáno.', 'success')
            return redirect(url_for('list_vehicles'))
        return render_template('vehicles/add.html', combinations=combinations)
    
    @app.route('/vehicles/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_vehicle(id):
        vehicle = Vehicle.query.get_or_404(id)
        combinations = VehicleCombination.query.all()
        if request.method == 'POST':
            vehicle.registration_number = request.form.get('registration_number')
            vehicle.brand = request.form.get('brand')
            vehicle.model = request.form.get('model')
            vehicle.year_of_manufacture = int(request.form.get('year_of_manufacture') or 0)
            vehicle.vin = request.form.get('vin')
            vehicle.current_mileage = int(request.form.get('current_mileage') or 0)
            vehicle.combination_id = int(request.form.get('combination_id')) if request.form.get('combination_id') else None
            vehicle.note = request.form.get('note')
            vehicle.last_mileage_update = datetime.utcnow()
            db.session.commit()
            flash('Vozidlo bylo úspěšně aktualizováno.', 'success')
            return redirect(url_for('list_vehicles'))
        return render_template('vehicles/edit.html', vehicle=vehicle, combinations=combinations)
    
    @app.route('/vehicles/detail/<int:id>')
    @login_required
    def vehicle_detail(id):
        vehicle = Vehicle.query.get_or_404(id)
        positions = TirePosition.query.filter_by(vehicle_id=id).all()
        return render_template('vehicles/detail.html', vehicle=vehicle, positions=positions)
    
    # ===== Soupravy vozidel =====
    @app.route('/combinations')
    @login_required
    def list_combinations():
        combinations = VehicleCombination.query.all()
        return render_template('combinations/list.html', combinations=combinations)
    
    @app.route('/combinations/add', methods=['GET', 'POST'])
    @login_required
    def add_combination():
        if request.method == 'POST':
            combination = VehicleCombination(
                name=request.form.get('name'),
                description=request.form.get('description'),
                is_active=bool(request.form.get('is_active'))
            )
            db.session.add(combination)
            db.session.commit()
            flash('Souprava byla úspěšně přidána.', 'success')
            return redirect(url_for('list_combinations'))
        return render_template('combinations/add.html')
    
    @app.route('/combinations/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_combination(id):
        combination = VehicleCombination.query.get_or_404(id)
        if request.method == 'POST':
            combination.name = request.form.get('name')
            combination.description = request.form.get('description')
            combination.is_active = bool(request.form.get('is_active'))
            db.session.commit()
            flash('Souprava byla úspěšně aktualizována.', 'success')
            return redirect(url_for('list_combinations'))
        return render_template('combinations/edit.html', combination=combination)
    
    @app.route('/combinations/detail/<int:id>')
    @login_required
    def combination_detail(id):
        combination = VehicleCombination.query.get_or_404(id)
        vehicles = Vehicle.query.filter_by(combination_id=id).all()
        return render_template('combinations/detail.html', combination=combination, vehicles=vehicles)
    
    # ===== Montáž/demontáž pneumatik =====
    @app.route('/tire-mount', methods=['GET', 'POST'])
    @login_required
    def tire_mount():
        vehicles = Vehicle.query.all()
        available_tires = Tire.query.filter_by(status='skladem').all()
        
        if request.method == 'POST':
            tire_id = int(request.form.get('tire_id'))
            vehicle_id = int(request.form.get('vehicle_id'))
            position_id = int(request.form.get('position_id'))
            mileage = int(request.form.get('mileage') or 0)
            tread_depth = float(request.form.get('tread_depth') or 0)
            note = request.form.get('note')
            
            tire = Tire.query.get_or_404(tire_id)
            vehicle = Vehicle.query.get_or_404(vehicle_id)
            position = TirePosition.query.get_or_404(position_id)
            
            # Kontrola, zda už není pneumatika na jiné pozici
            if position.tire:
                flash('Na vybrané pozici už je namontována pneumatika. Nejprve ji demontujte.', 'danger')
                return redirect(url_for('tire_mount'))
            
            # Aktualizace statusu pneumatiky
            tire.status = 'namontováno'
            tire.position_id = position_id
            tire.current_tread_depth = tread_depth
            
            # Záznam do historie
            history = TireHistory(
                tire_id=tire_id,
                vehicle_id=vehicle_id,
                position_code=position.position_code,
                action_type='montáž',
                mileage_at_action=mileage,
                tread_depth_at_action=tread_depth,
                note=note,
                technician_id=current_user.id
            )
            db.session.add(history)
            db.session.commit()
            
            flash('Pneumatika byla úspěšně namontována.', 'success')
            return redirect(url_for('vehicle_detail', id=vehicle_id))
        
        return render_template('tires/mount.html', vehicles=vehicles, available_tires=available_tires)
    
    @app.route('/tire-dismount/<int:tire_id>', methods=['GET', 'POST'])
    @login_required
    def tire_dismount(tire_id):
        tire = Tire.query.get_or_404(tire_id)
        
        if tire.status != 'namontováno' or not tire.position:
            flash('Pneumatika není namontována na žádném vozidle.', 'danger')
            return redirect(url_for('tire_detail', id=tire_id))
        
        # Kontrola existence vehicle
        if not hasattr(tire.position, 'vehicle') or not tire.position.vehicle:
            flash('Pneumatika je přiřazena k pozici, ale vozidlo není dostupné.', 'danger')
            return redirect(url_for('tire_detail', id=tire_id))
            
        vehicle = tire.position.vehicle
        
        if request.method == 'POST':
            mileage = int(request.form.get('mileage') or 0)
            tread_depth = float(request.form.get('tread_depth') or 0)
            reason = request.form.get('reason')
            note = request.form.get('note')
            
            # Výpočet nájezdu pneumatiky
            previous_history = TireHistory.query.filter_by(
                tire_id=tire_id, 
                action_type='montáž'
            ).order_by(TireHistory.action_date.desc()).first()
            
            if previous_history and previous_history.mileage_at_action:
                km_traveled = mileage - previous_history.mileage_at_action
                tire.total_mileage += max(0, km_traveled)
            
            position_id = tire.position_id
            position_code = tire.position.position_code
            vehicle_id = tire.position.vehicle_id if hasattr(tire.position, 'vehicle') and tire.position.vehicle else None
            
            # Aktualizace statusu pneumatiky
            tire.status = 'skladem' if reason != 'vyřazení' else 'vyřazeno'
            tire.position_id = None
            tire.current_tread_depth = tread_depth
            
            # Záznam do historie
            history = TireHistory(
                tire_id=tire_id,
                vehicle_id=vehicle_id,
                position_code=position_code,
                action_type='demontáž',
                action_reason=reason,
                mileage_at_action=mileage,
                tread_depth_at_action=tread_depth,
                note=note,
                technician_id=current_user.id
            )
            db.session.add(history)
            
            # Zpracování nahraných fotografií
            photos = request.files.getlist('photos')
            for photo in photos:
                if photo and photo.filename:
                    filename = secure_filename(f"{uuid.uuid4()}_{photo.filename}")
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    photo.save(photo_path)
                    
                    photo_db = TirePhoto(
                        history_id=history.id,
                        photo_path=filename,
                        caption=request.form.get('photo_caption')
                    )
                    db.session.add(photo_db)
            
            db.session.commit()
            
            flash('Pneumatika byla úspěšně demontována.', 'success')
            return redirect(url_for('vehicle_detail', id=vehicle_id))
        
        return render_template('tires/dismount.html', tire=tire, vehicle=vehicle)
    
    # ===== Servisní zásahy =====
    @app.route('/service-actions')
    @login_required
    def list_service_actions():
        service_actions = ServiceAction.query.order_by(ServiceAction.action_date.desc()).all()
        return render_template('service/list.html', service_actions=service_actions)
    
    @app.route('/service-actions/add', methods=['GET', 'POST'])
    @login_required
    def add_service_action():
        tires = Tire.query.all()
        if request.method == 'POST':
            tire_id = int(request.form.get('tire_id'))
            action_type = request.form.get('action_type')
            description = request.form.get('description')
            note = request.form.get('note')
            
            service = ServiceAction(
                tire_id=tire_id,
                action_type=action_type,
                description=description,
                technician_id=current_user.id,
                note=note
            )
            db.session.add(service)
            db.session.commit()
            
            flash('Servisní záznam byl úspěšně přidán.', 'success')
            return redirect(url_for('tire_detail', id=tire_id))
        
        return render_template('service/add.html', tires=tires)
    
    # ===== Žádosti o nákup =====
    @app.route('/purchase-requests')
    @login_required
    def list_purchase_requests():
        purchase_requests = PurchaseRequest.query.order_by(PurchaseRequest.request_date.desc()).all()
        return render_template('purchase/list.html', purchase_requests=purchase_requests)
    
    @app.route('/purchase-requests/add', methods=['GET', 'POST'])
    @login_required
    def add_purchase_request():
        tire_types = TireType.query.all()
        if request.method == 'POST':
            tire_type_id = int(request.form.get('tire_type_id'))
            quantity = int(request.form.get('quantity'))
            priority = request.form.get('priority')
            note = request.form.get('note')
            
            request_obj = PurchaseRequest(
                tire_type_id=tire_type_id,
                quantity=quantity,
                priority=priority,
                requester_id=current_user.id,
                note=note
            )
            db.session.add(request_obj)
            db.session.commit()
            
            flash('Žádost o nákup byla úspěšně vytvořena.', 'success')
            return redirect(url_for('list_purchase_requests'))
        
        return render_template('purchase/add.html', tire_types=tire_types)
    
    @app.route('/purchase-requests/approve/<int:id>', methods=['POST'])
    @login_required
    def approve_purchase_request(id):
        if current_user.role != 'admin' and current_user.role != 'manager':
            flash('Nemáte oprávnění ke schválení žádosti o nákup.', 'danger')
            return redirect(url_for('list_purchase_requests'))
        
        purchase_request = PurchaseRequest.query.get_or_404(id)
        purchase_request.status = 'schváleno'
        purchase_request.approver_id = current_user.id
        purchase_request.approval_date = datetime.utcnow()
        db.session.commit()
        
        flash('Žádost o nákup byla úspěšně schválena.', 'success')
        return redirect(url_for('list_purchase_requests'))
    
    @app.route('/purchase-requests/deliver/<int:id>', methods=['POST'])
    @login_required
    def deliver_purchase_request(id):
        purchase_request = PurchaseRequest.query.get_or_404(id)
        purchase_request.status = 'dodáno'
        purchase_request.actual_delivery_date = datetime.utcnow().date()
        db.session.commit()
        
        flash('Žádost o nákup byla označena jako dodaná.', 'success')
        return redirect(url_for('list_purchase_requests'))
        
    # ===== Reporty =====
    @app.route('/reports')
    @login_required
    def reports():
        return render_template('reports/index.html')
    
    @app.route('/reports/tire-lifespan')
    @login_required
    def report_tire_lifespan():
        # Reporty o průměrné životnosti pneumatik podle typu
        lifespan_data = db.session.query(
            TireType.brand,
            TireType.model,
            TireType.size,
            db.func.avg(Tire.total_mileage).label('avg_mileage'),
            db.func.count(Tire.id).label('tire_count')
        ).join(
            Tire, Tire.tire_type_id == TireType.id
        ).filter(
            Tire.total_mileage > 0
        ).group_by(
            TireType.id
        ).order_by(
            db.desc('avg_mileage')
        ).all()
        
        return render_template('reports/tire_lifespan.html', lifespan_data=lifespan_data)
    
    @app.route('/reports/dismount-reasons')
    @login_required
    def report_dismount_reasons():
        # Reporty o nejčastějších důvodech demontáže/vyřazení
        reason_data = db.session.query(
            TireHistory.action_reason,
            db.func.count(TireHistory.id).label('reason_count')
        ).filter(
            TireHistory.action_type == 'demontáž',
            TireHistory.action_reason.isnot(None)
        ).group_by(
            TireHistory.action_reason
        ).order_by(
            db.desc('reason_count')
        ).all()
        
        return render_template('reports/dismount_reasons.html', reason_data=reason_data)
    
    @app.route('/reports/low-stock')
    @login_required
    def report_low_stock():
        # Reporty o stavu skladu - pneumatiky pod minimální úrovní
        low_stock_data = db.session.query(
            TireType.brand,
            TireType.model,
            TireType.size,
            TireType.min_stock_level,
            db.func.count(Tire.id).label('current_stock')
        ).outerjoin(
            Tire, 
            (Tire.tire_type_id == TireType.id) & (Tire.status == 'skladem')
        ).group_by(TireType.id).having(
            db.func.count(Tire.id) < TireType.min_stock_level
        ).all()
        
        return render_template('reports/low_stock.html', low_stock_data=low_stock_data)
    
    # ===== Nahrávání fotek =====
    @app.route('/uploads/<filename>')
    @login_required
    def get_upload(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # ===== API pro načítání dat pro formuláře =====
    @app.route('/api/positions/<int:vehicle_id>')
    @login_required
    def get_positions(vehicle_id):
        positions = TirePosition.query.filter_by(vehicle_id=vehicle_id).all()
        position_list = [
            {
                'id': pos.id,
                'code': pos.position_code,
                'description': pos.position_description,
                'tire_mounted': bool(pos.tire)
            }
            for pos in positions
        ]
        return jsonify(position_list)
        
    # ===== Inicializace databáze =====
    @app.route('/init-db')
    def init_db():
        db.create_all()
        
        # Pokud neexistuje žádný uživatel, vytvořit admin účet
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@jafa.cz',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            flash('Databáze byla inicializována a byl vytvořen výchozí admin účet.', 'success')
        else:
            flash('Databáze byla inicializována.', 'success')
            
        return redirect(url_for('index'))
