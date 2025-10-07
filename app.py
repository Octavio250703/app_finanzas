from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from config import Config
from models import Database, AuthService, Investment, Organism, OrganismRating, InvestmentMessage, OrganismMessage
from google_sheets_service import google_sheets_service  # ✅ Correcto
from market_history_model import save_daily_snapshot, get_market_history, get_latest_prices
from market_scheduler import start_scheduler, manual_snapshot, get_scheduler_status
from datetime import datetime, date, timedelta
import threading
import logging
from portfolio_model_improved import portfolio_manager

app = Flask(__name__)
app.config.from_object(Config)

# Configurar logging
# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar servicios
db = Database()
auth_service = AuthService(db)
investment_model = Investment(db)
organism_model = Organism(db)
organism_rating_model = OrganismRating(db)
investment_message_model = InvestmentMessage(db)
organism_message_model = OrganismMessage(db)

def require_auth():
    """Decorador para rutas que requieren autenticación"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'access_token' not in session or 'user_uuid' not in session:
                return redirect(url_for('login'))
            
            # Configurar el token de autenticación en la base de datos
            db.set_auth_token(session['access_token'])
            
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@app.route('/')
def index():
    if 'user_uuid' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        result = auth_service.sign_in(email, password)
        
        if result and result.user:
            # Guardar información de la sesión
            session['access_token'] = result.session.access_token
            session['refresh_token'] = result.session.refresh_token
            session['user_uuid'] = result.user.id
            session['user_email'] = result.user.email
            
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas o usuario no verificado', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Cerrar sesión en Supabase
    auth_service.sign_out()
    
    # Limpiar el token de autenticación de la base de datos
    # Comentado temporalmente mientras RLS está deshabilitado
    # db.clear_auth_token()
    
    # Limpiar sesión local
    session.clear()
    flash('Sesión cerrada exitosamente', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_auth()
def dashboard():
    investments = investment_model.get_user_investments(session['user_uuid'])
    organisms = organism_model.get_user_organisms(session['user_uuid'], include_disabled=False)
    
    # Agregar cálculos de rendimiento a cada inversión
    for investment in investments:
        calculation = investment_model.calculate_estimated_return(investment)
        investment['calculation'] = calculation
    
    # Obtener estadísticas del dashboard
    stats = investment_model.get_dashboard_stats(session['user_uuid'])
    
    # Obtener datos de mercado (con manejo de errores)
    try:
        # Por esto:
        market_summary = google_sheets_service.get_market_data()
        if market_summary and market_summary.get('data'):
            # Crear resumen para el dashboard
            market_count = len(market_summary['data'])
            prices = []
            for item in market_summary['data']:
                try:
                    price_str = str(item.get('price', '')).replace('$', '').replace(',', '').strip()
                    if price_str and price_str not in ['#N/A', 'N/A', '']:
                        prices.append(float(price_str))
                except (ValueError, TypeError):
                    continue
            market_avg = sum(prices) / len(prices) if prices else 0
        else:
            market_count = 0
            market_avg = 0
    except Exception as e:
        logging.error("Error obteniendo datos de mercado para dashboard: %s", str(e))
        market_count = 0
        market_avg = 0
    
    return render_template('dashboard.html', 
                         investments=investments, 
                         organisms=organisms,
                         stats=stats,
                         market_count=market_count,
                         market_avg=market_avg)

@app.route('/create_investment', methods=['GET', 'POST'])
@require_auth()
def create_investment():
    # Obtener el organism_id desde query params si viene desde un organismo
    organism_id = request.args.get('organism_id')
    
    if request.method == 'POST':
        investment_data = {
            'name': request.form['name'],
            'organism_id': int(request.form['organism_id']) if request.form['organism_id'] else None,
            'organism': request.form.get('organism', ''),  # Texto libre como backup
            'description': request.form['description'],
            'investment_type': request.form['investment_type'],
            'status': request.form['status'],
            'amount': request.form['amount'],
            'currency': request.form['currency'],
            'start_date': request.form['start_date'],
            'end_date': request.form['end_date'] if request.form['end_date'] else None,
            'annual_rate': request.form['annual_rate'] if request.form['annual_rate'] else None
        }
        
        investment = investment_model.create_investment(session['user_uuid'], investment_data)
        
        if investment:
            flash('Inversión creada exitosamente', 'success')
            # Si vino desde un organismo, redirigir de vuelta al organismo
            if investment_data['organism_id']:
                return redirect(url_for('view_organism', organism_id=investment_data['organism_id']))
            return redirect(url_for('dashboard'))
        else:
            flash('Error al crear la inversión', 'error')
    
    # Obtener lista de organismos para el selector
    organisms = organism_model.get_user_organisms(session['user_uuid'], include_disabled=False)
    
    return render_template('create_investment.html', 
                         organisms=organisms, 
                         selected_organism_id=organism_id)

@app.route('/investment/<int:investment_id>')
@require_auth()
def view_investment(investment_id):
    investment = investment_model.get_investment_by_id(investment_id, session['user_uuid'])
    
    if not investment:
        flash('Inversión no encontrada', 'error')
        return redirect(url_for('dashboard'))
    
    # Calcular rendimiento estimado
    calculation = investment_model.calculate_estimated_return(investment)
    investment['calculation'] = calculation
    
    return render_template('view_investment.html', investment=investment)

@app.route('/edit_investment/<int:investment_id>', methods=['GET', 'POST'])
@require_auth()
def edit_investment(investment_id):
    investment = investment_model.get_investment_by_id(investment_id, session['user_uuid'])
    
    if not investment:
        flash('Inversión no encontrada', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        update_data = {
            'name': request.form['name'],
            'organism': request.form['organism'],
            'description': request.form['description'],
            'investment_type': request.form['investment_type'],
            'status': request.form['status'],
            'amount': float(request.form['amount']),
            'currency': request.form['currency'],
            'start_date': request.form['start_date'],
            'end_date': request.form['end_date'] if request.form['end_date'] else None,
            'annual_rate': float(request.form['annual_rate']) if request.form['annual_rate'] else None
        }
        
        updated_investment = investment_model.update_investment(investment_id, session['user_uuid'], update_data)
        
        if updated_investment:
            flash('Inversión actualizada exitosamente', 'success')
            return redirect(url_for('view_investment', investment_id=investment_id))
        else:
            flash('Error al actualizar la inversión', 'error')
    
    return render_template('edit_investment.html', investment=investment)

@app.route('/toggle_investment/<int:investment_id>', methods=['POST'])
@require_auth()
def toggle_investment(investment_id):
    result = investment_model.toggle_investment_status(investment_id, session['user_uuid'])
    
    if result:
        status = "habilitada" if result['enabled'] else "inhabilitada"
        return jsonify({'success': True, 'message': f'Inversión {status} exitosamente', 'enabled': result['enabled']})
    else:
        return jsonify({'success': False, 'message': 'Error al cambiar el estado de la inversión'})

# ==========================================
# RUTAS DE ORGANISMOS
# ==========================================

@app.route('/organisms')
@require_auth()
def organisms():
    """Lista todos los organismos del usuario"""
    organisms = organism_model.get_user_organisms(session['user_uuid'])
    
    # Agregar estadísticas para cada organismo
    for organism in organisms:
        stats = organism_model.get_organism_stats(organism['id'], session['user_uuid'])
        organism['stats'] = stats
        
        # Obtener calificaciones promedio
        ratings = organism_rating_model.get_organism_average_ratings(organism['id'])
        organism['ratings'] = ratings
    
    return render_template('organisms.html', organisms=organisms)

@app.route('/create_organism', methods=['GET', 'POST'])
@require_auth()
def create_organism():
    """Crea un nuevo organismo"""
    if request.method == 'POST':
        organism_data = {
            'name': request.form['name'],
            'full_name': request.form.get('full_name', ''),
            'description': request.form.get('description', ''),
            'website': request.form.get('website', ''),
            'contact_email': request.form.get('contact_email', ''),
            'contact_phone': request.form.get('contact_phone', ''),
            'address': request.form.get('address', ''),
            'country': request.form.get('country', 'Argentina')
        }
        
        organism = organism_model.create_organism(session['user_uuid'], organism_data)
        
        if organism:
            flash('Organismo creado exitosamente', 'success')
            return redirect(url_for('view_organism', organism_id=organism['id']))
        else:
            flash('Error al crear el organismo', 'error')
    
    return render_template('create_organism.html')

@app.route('/organism/<int:organism_id>')
@require_auth()
def view_organism(organism_id):
    """Ver detalles de un organismo"""
    organism = organism_model.get_organism_by_id(organism_id, session['user_uuid'])
    
    if not organism:
        flash('Organismo no encontrado', 'error')
        return redirect(url_for('organisms'))
    
    # Obtener estadísticas del organismo
    stats = organism_model.get_organism_stats(organism_id, session['user_uuid'])
    organism['stats'] = stats
    
    # Obtener inversiones del organismo
    investments = investment_model.get_investments_by_organism(organism_id, session['user_uuid'])
    
    # Obtener calificaciones
    avg_ratings = organism_rating_model.get_organism_average_ratings(organism_id)
    user_rating = organism_rating_model.get_user_rating(organism_id, session['user_uuid'])
    
    # Obtener mensajes del organismo
    messages = organism_message_model.get_organism_messages(organism_id, session['user_uuid'])
    
    return render_template('view_organism.html', 
                         organism=organism,
                         investments=investments,
                         avg_ratings=avg_ratings,
                         user_rating=user_rating,
                         messages=messages)

@app.route('/edit_organism/<int:organism_id>', methods=['GET', 'POST'])
@require_auth()
def edit_organism(organism_id):
    """Editar un organismo"""
    organism = organism_model.get_organism_by_id(organism_id, session['user_uuid'])
    
    if not organism:
        flash('Organismo no encontrado', 'error')
        return redirect(url_for('organisms'))
    
    if request.method == 'POST':
        update_data = {
            'name': request.form['name'],
            'full_name': request.form.get('full_name', ''),
            'description': request.form.get('description', ''),
            'website': request.form.get('website', ''),
            'contact_email': request.form.get('contact_email', ''),
            'contact_phone': request.form.get('contact_phone', ''),
            'address': request.form.get('address', ''),
            'country': request.form.get('country', 'Argentina')
        }
        
        updated_organism = organism_model.update_organism(organism_id, session['user_uuid'], update_data)
        
        if updated_organism:
            flash('Organismo actualizado exitosamente', 'success')
            return redirect(url_for('view_organism', organism_id=organism_id))
        else:
            flash('Error al actualizar el organismo', 'error')
    
    return render_template('edit_organism.html', organism=organism)

@app.route('/toggle_organism/<int:organism_id>', methods=['POST'])
@require_auth()
def toggle_organism(organism_id):
    """Habilitar/Deshabilitar un organismo"""
    result = organism_model.toggle_organism_status(organism_id, session['user_uuid'])
    
    if result:
        status = "habilitado" if result['enabled'] else "inhabilitado"
        return jsonify({'success': True, 'message': f'Organismo {status} exitosamente', 'enabled': result['enabled']})
    else:
        return jsonify({'success': False, 'message': 'Error al cambiar el estado del organismo'})

# ==========================================
# RUTAS DE CALIFICACIONES
# ==========================================

@app.route('/rate_organism/<int:organism_id>', methods=['POST'])
@require_auth()
def rate_organism(organism_id):
    """Calificar un organismo"""
    try:
        rating_data = {
            'risk_level': float(request.form['risk_level']),
            'profitability_potential': float(request.form['profitability_potential']),
            'agility_bureaucracy': float(request.form['agility_bureaucracy']),
            'transparency': float(request.form['transparency'])
        }
        
        result = organism_rating_model.create_or_update_rating(organism_id, session['user_uuid'], rating_data)
        
        if result:
            flash('Calificación guardada exitosamente', 'success')
        else:
            flash('Error al guardar la calificación', 'error')
            
    except Exception as e:
        logging.error("Error rating organism: %s", str(e))
        flash('Error al procesar la calificación', 'error')
    
    return redirect(url_for('view_organism', organism_id=organism_id))

# ==========================================
# RUTAS DE MENSAJES - INVERSIONES
# ==========================================

@app.route('/investment/<int:investment_id>/messages')
@require_auth()
def investment_messages(investment_id):
    """Obtener mensajes de una inversión (API)"""
    messages = investment_message_model.get_investment_messages(investment_id, session['user_uuid'])
    return jsonify({'messages': messages})

@app.route('/investment/<int:investment_id>/add_message', methods=['POST'])
@require_auth()
def add_investment_message(investment_id):
    """Agregar un mensaje a una inversión"""
    message = request.form.get('message', '').strip()
    
    if not message:
        flash('El mensaje no puede estar vacío', 'error')
        return redirect(url_for('view_investment', investment_id=investment_id))
    
    result = investment_message_model.create_message(investment_id, session['user_uuid'], message)
    
    if result:
        flash('Mensaje enviado exitosamente', 'success')
    else:
        flash('Error al enviar el mensaje', 'error')
    
    return redirect(url_for('view_investment', investment_id=investment_id))

@app.route('/delete_investment_message/<int:message_id>', methods=['POST'])
@require_auth()
def delete_investment_message(message_id):
    """Eliminar un mensaje de inversión"""
    result = investment_message_model.delete_message(message_id, session['user_uuid'])
    
    if result:
        return jsonify({'success': True, 'message': 'Mensaje eliminado exitosamente'})
    else:
        return jsonify({'success': False, 'message': 'Error al eliminar el mensaje'})

# ==========================================
# RUTAS DE MENSAJES - ORGANISMOS
# ==========================================

@app.route('/organism/<int:organism_id>/messages')
@require_auth()
def organism_messages(organism_id):
    """Obtener mensajes de un organismo (API)"""
    messages = organism_message_model.get_organism_messages(organism_id, session['user_uuid'])
    return jsonify({'messages': messages})

@app.route('/organism/<int:organism_id>/add_message', methods=['POST'])
@require_auth()
def add_organism_message(organism_id):
    """Agregar un mensaje a un organismo"""
    message = request.form.get('message', '').strip()
    
    if not message:
        flash('El mensaje no puede estar vacío', 'error')
        return redirect(url_for('view_organism', organism_id=organism_id))
    
    result = organism_message_model.create_message(organism_id, session['user_uuid'], message)
    
    if result:
        flash('Mensaje enviado exitosamente', 'success')
    else:
        flash('Error al enviar el mensaje', 'error')
    
    return redirect(url_for('view_organism', organism_id=organism_id))

@app.route('/delete_organism_message/<int:message_id>', methods=['POST'])
@require_auth()
def delete_organism_message(message_id):
    """Eliminar un mensaje de organismo"""
    result = organism_message_model.delete_message(message_id, session['user_uuid'])
    
    if result:
        return jsonify({'success': True, 'message': 'Mensaje eliminado exitosamente'})
    else:
        return jsonify({'success': False, 'message': 'Error al eliminar el mensaje'})

# ==========================================
# RUTAS DE API PARA ESTADÍSTICAS
# ==========================================

@app.route('/api/organism/<int:organism_id>/stats')
@require_auth()
def api_organism_stats(organism_id):
    """API para obtener estadísticas de un organismo"""
    stats = organism_model.get_organism_stats(organism_id, session['user_uuid'])
    
    if stats:
        return jsonify({'success': True, 'stats': stats})
    else:
        return jsonify({'success': False, 'message': 'Error al obtener estadísticas'})

@app.route('/api/dashboard/stats')
@require_auth()
def api_dashboard_stats():
    """API para obtener estadísticas del dashboard"""
    stats = investment_model.get_dashboard_stats(session['user_uuid'])
    
    if stats:
        return jsonify({'success': True, 'stats': stats})
    else:
        return jsonify({'success': False, 'message': 'Error al obtener estadísticas'})

# ==========================================
# RUTAS DE DATOS DE MERCADO
# ==========================================

@app.route('/market-data')
@require_auth()
def market_data():
    """Página para mostrar datos de mercado desde Google Sheets"""
    try:
        # Obtener datos del Google Sheet
        # Por esto:
        market_data = google_sheets_service.get_market_data()
        
        if market_data is None:
            flash('Error al obtener datos de Google Sheets', 'warning')
            market_data = {'data': []}
        
        return render_template('market_data.html', 
                             market_data=market_data.get('data', []),
                             user_email=session.get('user_email'))
    
    except Exception as e:
        logging.error("Error en ruta market_data: %s", str(e))
        flash('Error interno del servidor', 'error')
        return render_template('market_data.html', 
                             market_data=[],
                             user_email=session.get('user_email'))
    

@app.route('/api/market-data')
def api_market_data():
    try:
        print("Iniciando api_market_data")
        
        # Obtener datos de Google Sheets
        data = google_sheets_service.get_market_data()
        print("Datos obtenidos: %s", type(data))
        
        # Manejar caso de timeout o None
        if data is None:
            print("❌ No se pudieron obtener datos (timeout o error)")
            return jsonify({
                'success': False,
                'error': 'Timeout al obtener datos de Google Sheets. Intentar de nuevo.',
                'data': [],
                'timestamp': datetime.now().isoformat()
            })
        
        # Manejar diferentes tipos de respuesta
        if isinstance(data, dict):
            # Si es un diccionario, extraer la lista de 'data'
            market_data = data.get('data', [])
            print("Datos extraídos de diccionario")
        elif isinstance(data, list):
            # Si ya es una lista, usarla directamente
            market_data = data
            print("Datos ya son una lista")
        else:
            print("Tipo de datos inesperado: %s", type(data))
            return jsonify({
                'success': False,
                'error': 'Tipo de datos inesperado: ' + str(type(data)),
                'data': [],
                'timestamp': datetime.now().isoformat()
            })
        
        print("Market data final: %s elementos", len(market_data))
        
        # Retornar la respuesta exitosa
        return jsonify({
            'success': True,
            'data': market_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print("ERROR en api_market_data: %s", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/market-data/force-update', methods=['POST'])
def api_force_update():
    try:
        # Ejecutar manualmente el job del scheduler
        from market_scheduler import manual_snapshot
        result = manual_snapshot()
        return jsonify({
            'success': True,
            'message': 'Actualización forzada completada'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
    
@app.route('/market-history')
@require_auth()
def market_history():
    """Página para ver el histórico de datos de mercado"""
    try:
        # Obtener resumen de los últimos 7 días
        summaries = []
        for i in range(7):
            target_date = date.today() - timedelta(days=i)
            # Por ahora, creamos un resumen básico
            # Más adelante puedes implementar get_daily_summary si quieres
            summary = {
                'date': target_date.isoformat(),
                'count': 0,  # Placeholder
                'avg_price': 0  # Placeholder
            }
            summaries.append(summary)
        
        # Obtener fecha del último snapshot (usar los datos más recientes)
        try:
            historical_data = get_market_history(limit=1)
            last_snapshot = historical_data[0]['date'] if historical_data else None
        except:
            last_snapshot = None
        
        return render_template('market_history.html',
                             daily_summaries=summaries,
                             last_snapshot=last_snapshot,
                             user_email=session.get('user_email'))
    
    except Exception as e:
        logging.error("Error en market_history: %s", str(e))
        flash('Error cargando histórico de mercado', 'error')
        return redirect(url_for('market_data'))

# ==========================================
# NUEVAS RUTAS PARA HISTORIAL DE MERCADO
# ==========================================

@app.route('/api/market-data/save-snapshot', methods=['POST'])
@require_auth()
def save_market_snapshot():
    """Guarda snapshot manual de datos de mercado"""
    try:
        success = manual_snapshot()
        if success:
            return jsonify({
                'success': True,
                'message': 'Snapshot guardado exitosamente'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error al guardar snapshot'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/market-data/history')
@require_auth()
def get_market_data_history():
    """Obtiene historial de datos de mercado"""
    try:
        symbol = request.args.get('symbol')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        
        history = get_market_history(symbol, start_date, end_date, limit)
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@app.route('/api/market-data/scheduler-status')
@require_auth()
def scheduler_status():
    """Obtiene el estado del scheduler"""
    try:
        status = get_scheduler_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

from portfolio_model_improved import portfolio_manager

@app.route('/portfolios')
@require_auth()
def all_portfolios():
    """Página para mostrar todas las carteras del usuario (todos los organismos)"""
    try:
        # Obtener todos los organismos del usuario
        user_uuid = session.get('user_uuid')
        organisms = organism_model.get_user_organisms(user_uuid)
        
        # Obtener todas las carteras agrupadas por organismo
        all_portfolios = []
        for organism in organisms:
            portfolios = portfolio_manager.get_portfolios_by_organism(organism['id'])
            for portfolio in portfolios:
                portfolio['organism_name'] = organism['name']
                # Agregar estadísticas básicas
                stats = portfolio_manager.get_portfolio_stats(portfolio['id'])
                portfolio['stats'] = stats
                all_portfolios.append(portfolio)
        
        return render_template('all_portfolios.html', 
                             portfolios=all_portfolios,
                             organisms=organisms)
                             
    except Exception as e:
        logger.error("Error en all_portfolios: %s", str(e))
        flash('Error al cargar las carteras', 'error')
        return redirect(url_for('dashboard'))

@app.route('/portfolios/<int:organism_id>')
@require_auth()
def portfolios_page(organism_id):
    """Página de carteras para un organismo"""
    try:
        user_uuid = session.get('user_uuid')
        organism = organism_model.get_organism_by_id(organism_id, user_uuid)
        
        if not organism:
            flash('Organismo no encontrado', 'error')
            return redirect(url_for('organisms'))
        
        portfolios = portfolio_manager.get_portfolios_by_organism(organism_id)
        
        # Agregar estadísticas a cada cartera
        for portfolio in portfolios:
            stats = portfolio_manager.get_portfolio_stats(portfolio['id'])
            portfolio['stats'] = stats
        
        return render_template('portfolios.html', 
                             organism=organism, 
                             portfolios=portfolios)
    except Exception as e:
        logger.error("Error en portfolios_page: %s", str(e))
        flash('Error al cargar las carteras', 'error')
        return redirect(url_for('organisms'))

@app.route('/portfolio/<int:portfolio_id>')
@require_auth()
def portfolio_detail(portfolio_id):
    import traceback
    import sys
    
    try:
        # Obtener datos del portfolio
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            flash('Portfolio no encontrado', 'error')
            return redirect(url_for('portfolios'))
        
        # Verificar que el portfolio pertenece al usuario
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], session.get('user_uuid'))
        if not organism or organism.get('user_uuid') != session.get('user_uuid'):
            flash('No tienes permisos para ver este portfolio', 'error')
            return redirect(url_for('portfolios'))
        
        print("DEBUG: Antes de calculate_portfolio_value")
        sys.stdout.flush()
        
        # Calcular valor del portfolio
        portfolio_value = portfolio_manager.calculate_portfolio_value(portfolio_id)
        
        print("DEBUG: Después de calculate_portfolio_value")
        print(f"DEBUG: portfolio_value = {portfolio_value}")
        sys.stdout.flush()
        
        print("DEBUG: Antes de render_template")
        sys.stdout.flush()
        
        return render_template('portfolio_detail.html', 
                             portfolio=portfolio,
                             organism=organism,
                             portfolio_value=portfolio_value)
        
    except Exception as e:
        print("================== ERROR COMPLETO ==================")
        print(f"Error tipo: {type(e)}")
        print(f"Error mensaje: {str(e)}")
        print("Stack trace completo:")
        traceback.print_exc()
        print("====================================================")
        sys.stdout.flush()
        
        # También capturar en logging sin f-strings
        logger.error("Error en portfolio_detail: %s", str(e))
        
        flash('Error al cargar los detalles del portfolio', 'error')
        return redirect(url_for('all_portfolios'))

# ================== RUTAS DE API ==================

@app.route('/api/portfolios', methods=['GET'])
@require_auth()
def api_get_all_portfolios():
    """API para obtener todas las carteras del usuario"""
    try:
        user_uuid = session.get('user_uuid')
        organism_id = request.args.get('organism_id')
        
        if organism_id:
            # Verificar que el organismo pertenece al usuario
            organism = organism_model.get_organism_by_id(int(organism_id), user_uuid)
            if not organism:
                return jsonify({'success': False, 'error': 'Organismo no encontrado'})
            
            portfolios = portfolio_manager.get_portfolios_by_organism(int(organism_id))
        else:
            # Obtener todas las carteras del usuario
            organisms = organism_model.get_user_organisms(user_uuid)
            portfolios = []
            for organism in organisms:
                org_portfolios = portfolio_manager.get_portfolios_by_organism(organism['id'])
                for portfolio in org_portfolios:
                    portfolio['organism_name'] = organism['name']
                    portfolios.append(portfolio)
        
        # AGREGAR CÁLCULO DE VALOR ACTUAL PARA CADA CARTERA
        for portfolio in portfolios:
            try:
                # Calcular valor actual de la cartera
                portfolio_value = portfolio_manager.calculate_portfolio_value(portfolio['id'])
                if portfolio_value:
                    portfolio['current_value'] = portfolio_value.get('total_value', 0)
                    portfolio['positions_count'] = len(portfolio_value.get('positions_detail', []))
                else:
                    portfolio['current_value'] = 0
                    portfolio['positions_count'] = 0
                
                # También agregar las estadísticas básicas
                stats = portfolio_manager.get_portfolio_stats(portfolio['id'])
                portfolio['stats'] = stats
                
            except Exception as e:
                logger.error("Error calculando valor para cartera %s: %s", portfolio['id'], str(e))
                portfolio['current_value'] = 0
                portfolio['positions_count'] = 0
        
        return jsonify({'success': True, 'portfolios': portfolios})
    except Exception as e:
        logger.error("Error en api_get_all_portfolios: %s", str(e))
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/api/portfolios', methods=['POST'])
@require_auth()
def api_create_portfolio():
    """API para crear nueva cartera"""
    try:
        user_uuid = session.get('user_uuid')
        data = request.get_json()
        organism_id = data.get('organism_id')
        name = data.get('name')
        description = data.get('description', '')
        
        if not organism_id or not name:
            return jsonify({
                'success': False,
                'error': 'organism_id y name son requeridos'
            }), 400
        
        # Verificar que el organismo pertenece al usuario
        organism = organism_model.get_organism_by_id(organism_id, user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'Organismo no encontrado'
            }), 404
        
        portfolio = portfolio_manager.create_portfolio(organism_id, name, description)
        
        if portfolio:
            return jsonify({
                'success': True,
                'portfolio': portfolio
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al crear cartera'
            }), 500
            
    except Exception as e:
        logger.error("Error en api_create_portfolio: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolios/<int:organism_id>', methods=['GET'])
@require_auth()
def api_get_portfolios(organism_id):
    """API para obtener carteras de un organismo"""
    try:
        user_uuid = session.get('user_uuid')
        
        # Verificar que el organismo pertenece al usuario
        organism = organism_model.get_organism_by_id(organism_id, user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'Organismo no encontrado'
            }), 404
        
        portfolios = portfolio_manager.get_portfolios_by_organism(organism_id)
        
        # AGREGAR CÁLCULO DE VALOR ACTUAL PARA CADA CARTERA
        for portfolio in portfolios:
            try:
                # Calcular valor actual de la cartera
                portfolio_value = portfolio_manager.calculate_portfolio_value(portfolio['id'])
                if portfolio_value:
                    portfolio['current_value'] = portfolio_value.get('total_value', 0)
                    portfolio['positions_count'] = len(portfolio_value.get('positions_detail', []))
                else:
                    portfolio['current_value'] = 0
                    portfolio['positions_count'] = 0
                
                # También agregar las estadísticas básicas
                stats = portfolio_manager.get_portfolio_stats(portfolio['id'])
                portfolio['stats'] = stats
                
            except Exception as e:
                logger.error("Error calculando valor para cartera %s: %s", portfolio['id'], str(e))
                portfolio['current_value'] = 0
                portfolio['positions_count'] = 0
        
        return jsonify({
            'success': True,
            'portfolios': portfolios
        })
    except Exception as e:
        logger.error("Error en api_get_portfolios: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>', methods=['GET'])
@require_auth()
def api_get_portfolio(portfolio_id):
    """API para obtener una cartera específica"""
    try:
        user_uuid = session.get('user_uuid')
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        # Verificar permisos
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        # Agregar estadísticas
        stats = portfolio_manager.get_portfolio_stats(portfolio_id)
        portfolio['stats'] = stats
        
        return jsonify({
            'success': True,
            'portfolio': portfolio
        })
    except Exception as e:
        logger.error("Error en api_get_portfolio: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>', methods=['PUT'])
@require_auth()
def api_update_portfolio(portfolio_id):
    """API para actualizar cartera"""
    try:
        user_uuid = session.get('user_uuid')
        data = request.get_json()
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        name = data.get('name')
        description = data.get('description')
        
        updated_portfolio = portfolio_manager.update_portfolio(portfolio_id, name, description)
        
        if updated_portfolio:
            return jsonify({
                'success': True,
                'portfolio': updated_portfolio
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al actualizar cartera'
            }), 500
            
    except Exception as e:
        logger.error("Error en api_update_portfolio: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>', methods=['DELETE'])
@require_auth()
def api_delete_portfolio(portfolio_id):
    """API para eliminar cartera"""
    try:
        user_uuid = session.get('user_uuid')
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        success = portfolio_manager.delete_portfolio(portfolio_id)
        
        return jsonify({
            'success': success,
            'message': 'Cartera eliminada' if success else 'Error eliminando cartera'
        })
        
    except Exception as e:
        logger.error("Error en api_delete_portfolio: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>/value', methods=['GET'])
@require_auth()
def api_portfolio_value(portfolio_id):
    """API para obtener valor actual de la cartera"""
    try:
        user_uuid = session.get('user_uuid')
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        # Obtener fecha específica si se proporciona
        target_date = request.args.get('date')  # Formato: YYYY-MM-DD
        
        portfolio_value = portfolio_manager.calculate_portfolio_value(portfolio_id, target_date)
        
        if portfolio_value is not None:
            return jsonify({
                'success': True,
                'portfolio_value': portfolio_value
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error calculando valor de cartera'
            }), 500
            
    except Exception as e:
        logger.error("Error en api_portfolio_value: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ================== RUTAS DE POSICIONES ==================

@app.route('/api/portfolio/<int:portfolio_id>/positions', methods=['GET'])
@require_auth()
def api_get_positions(portfolio_id):
    """API para obtener posiciones de una cartera"""
    try:
        user_uuid = session.get('user_uuid')
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        positions = portfolio_manager.get_portfolio_positions(portfolio_id)
        
        return jsonify({
            'success': True,
            'positions': positions
        })
        
    except Exception as e:
        logger.error("Error en api_get_positions: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>/positions', methods=['POST'])
@require_auth()
def api_add_position(portfolio_id):
    """API para agregar posición a cartera (solo símbolo + cantidad)"""
    try:
        user_uuid = session.get('user_uuid')
        data = request.get_json()
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        symbol = data.get('symbol')
        quantity = data.get('quantity')
        notes = data.get('notes', '')
        
        if not symbol or not quantity:
            return jsonify({
                'success': False,
                'error': 'symbol y quantity son requeridos'
            }), 400
        
        # No necesitamos average_cost, solo símbolo y cantidad
        position = portfolio_manager.add_position(
            portfolio_id, symbol, quantity, notes=notes
        )
        
        if position:
            return jsonify({
                'success': True,
                'position': position
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al agregar posición'
            }), 500
            
    except Exception as e:
        logger.error("Error en api_add_position: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>/positions/<symbol>', methods=['PUT'])
@require_auth()
def api_update_position(portfolio_id, symbol):
    """API para actualizar una posición"""
    try:
        user_uuid = session.get('user_uuid')
        data = request.get_json()
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        quantity = data.get('quantity')
        notes = data.get('notes')
        
        position = portfolio_manager.update_position(
            portfolio_id, symbol, quantity, notes
        )
        
        if position:
            return jsonify({
                'success': True,
                'position': position
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error al actualizar posición'
            }), 500
            
    except Exception as e:
        logger.error("Error en api_update_position: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/portfolio/<int:portfolio_id>/positions/<symbol>', methods=['DELETE'])
@require_auth()
def api_remove_position(portfolio_id, symbol):
    """API para eliminar posición de cartera"""
    try:
        user_uuid = session.get('user_uuid')
        
        # Verificar permisos
        portfolio = portfolio_manager.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return jsonify({
                'success': False,
                'error': 'Cartera no encontrada'
            }), 404
        
        organism = organism_model.get_organism_by_id(portfolio['organism_id'], user_uuid)
        if not organism:
            return jsonify({
                'success': False,
                'error': 'No tienes acceso a esta cartera'
            }), 403
        
        success = portfolio_manager.remove_position(portfolio_id, symbol)
        
        return jsonify({
            'success': success,
            'message': 'Posición eliminada' if success else 'Error eliminando posición'
        })
        
    except Exception as e:
        logger.error("Error en api_remove_position: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ===============================================
# FIN DE RUTAS DE PORTFOLIOS
# ===============================================


# Filtros de template personalizados
@app.template_filter('currency')
def currency_filter(value, currency='USD'):
    """Formatea un número como moneda"""
    if value is None:
        return "N/A"
    return f"{currency} {value:,.2f}"

@app.template_filter('percentage')
def percentage_filter(value):
    """Formatea un número como porcentaje"""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"

@app.template_filter('date_format')
def date_format(value):
    """Formatea una fecha"""
    if not value:
        return "N/A"
    try:
        if isinstance(value, str):
            date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            date_obj = value
        return date_obj.strftime('%d/%m/%Y')
    except:
        return value

@app.template_filter('datetime_format')
def datetime_format(value):
    """Formatea una fecha y hora"""
    if not value:
        return "N/A"
    try:
        if isinstance(value, str):
            date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            date_obj = value
        return date_obj.strftime('%d/%m/%Y %H:%M')
    except:
        return value

@app.template_filter('time_ago')
def time_ago(value):
    """Muestra tiempo transcurrido desde una fecha"""
    if not value:
        return "N/A"
    try:
        if isinstance(value, str):
            date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            date_obj = value
        
        now = datetime.now(date_obj.tzinfo)
        diff = now - date_obj
        
        if diff.days > 0:
            return f"hace {diff.days} día{'s' if diff.days > 1 else ''}"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"hace {hours} hora{'s' if hours > 1 else ''}"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"hace {minutes} minuto{'s' if minutes > 1 else ''}"
        else:
            return "hace unos segundos"
    except:
        return value

@app.template_filter('stars')
def stars_filter(value):
    """Convierte un número a estrellas visuales"""
    if value is None:
        return "N/A"
    try:
        rating = float(value)
        full_stars = int(rating)
        half_star = 1 if (rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star
        
        stars_html = "★" * full_stars
        if half_star:
            stars_html += "☆"
        stars_html += "☆" * empty_stars
        
        return stars_html
    except:
        return "N/A"

@app.template_filter('organism_name')
def organism_name_filter(investment):
    """Obtiene el nombre del organismo de una inversión"""
    if investment.get('organisms') and isinstance(investment['organisms'], dict):
        return investment['organisms'].get('name', investment.get('organism', 'N/A'))
    return investment.get('organism', 'N/A')

# Context processor para variables globales
@app.context_processor
def inject_global_vars():
    """Inyecta variables globales en todos los templates"""
    return {
        'current_year': datetime.now().year,
        'user_email': session.get('user_email', ''),
        'user_uuid': session.get('user_uuid', '')
    }

# Middleware para verificar sesión
@app.before_request
def check_session():
    """Verifica que la sesión sea válida antes de cada request"""
    # Rutas que no requieren autenticación
    public_routes = ['login', 'static']
    
    # Rutas de API que requieren autenticación pero manejan errores internamente
    api_routes = ['api_organism_stats', 'api_dashboard_stats']
    
    if request.endpoint not in public_routes:
        if 'access_token' in session and 'user_uuid' in session:
            # Aquí podrías verificar que el token sigue siendo válido
            # Por simplicidad, asumimos que es válido
            pass
        else:
            if request.endpoint and request.endpoint not in api_routes and request.endpoint != 'login':
                return redirect(url_for('login'))

# Iniciar el scheduler al arrancar la aplicación
def init_app():
    """Inicializa la aplicación y sus servicios"""
    try:
        # Iniciar scheduler en un hilo separado
        scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
        scheduler_thread.start()
        logging.info("✅ Market Data Scheduler iniciado")
    except Exception as e:
        logging.error("❌ Error iniciando Market Data Scheduler: %s", str(e))

# Llamar a la inicialización
init_app()

if __name__ == '__main__':
    app.run(debug=True)
