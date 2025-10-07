from supabase import create_client, Client
from config import Config
from datetime import datetime, timedelta
import logging

class Database:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        self.access_token = None
    
    def set_auth_token(self, access_token):
        """Configura el token de autenticación para las operaciones de base de datos"""
        self.access_token = access_token
        if access_token:
            self.supabase.options.headers.update({
                'Authorization': f'Bearer {access_token}'
            })
    
    def clear_auth_token(self):
        """Limpia el token de autenticación"""
        self.access_token = None
        self.supabase.options.headers.update({
            'Authorization': f'Bearer {Config.SUPABASE_KEY}'
        })
    
    def init_tables(self):
        """Inicializa las tablas necesarias en Supabase"""
        # Esta función puede usarse para verificar que las tablas existan
        # Las tablas se crearían desde el panel de Supabase
        pass

class AuthService:
    def __init__(self, db: Database):
        self.db = db
    
    def sign_up(self, email, password):
        """Registra un nuevo usuario usando Supabase Auth"""
        try:
            result = self.db.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return result
        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return None
    
    def sign_in(self, email, password):
        """Autentica un usuario usando Supabase Auth"""
        try:
            result = self.db.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return result
        except Exception as e:
            logging.error(f"Error authenticating user: {e}")
            return None
    
    def sign_out(self):
        """Cierra la sesión del usuario"""
        try:
            result = self.db.supabase.auth.sign_out()
            return result
        except Exception as e:
            logging.error(f"Error signing out: {e}")
            return None
    
    def get_user(self):
        """Obtiene el usuario actual autenticado"""
        try:
            result = self.db.supabase.auth.get_user()
            return result
        except Exception as e:
            logging.error(f"Error getting current user: {e}")
            return None
    
    def refresh_session(self):
        """Refresca la sesión del usuario"""
        try:
            result = self.db.supabase.auth.refresh_session()
            return result
        except Exception as e:
            logging.error(f"Error refreshing session: {e}")
            return None

class Organism:
    def __init__(self, db: Database):
        self.db = db
    
    def create_organism(self, user_uuid, data):
        """Crea un nuevo organismo"""
        try:
            organism_data = {
                'user_uuid': user_uuid,
                'name': data['name'],
                'full_name': data.get('full_name', ''),
                'description': data.get('description', ''),
                'website': data.get('website', ''),
                'contact_email': data.get('contact_email', ''),
                'contact_phone': data.get('contact_phone', ''),
                'address': data.get('address', ''),
                'country': data.get('country', 'Argentina'),
                'enabled': True
                # created_at será manejado automáticamente por PostgreSQL
            }
            
            result = self.db.supabase.table('organisms').insert(organism_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error creating organism: {e}")
            return None
    
    def get_user_organisms(self, user_uuid, include_disabled=True):
        """Obtiene todos los organismos de un usuario"""
        try:
            query = self.db.supabase.table('organisms').select("*").eq('user_uuid', user_uuid)
            
            if not include_disabled:
                query = query.eq('enabled', True)
            
            result = query.order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logging.error(f"Error getting organisms: {e}")
            return []
    
    def get_organism_by_id(self, organism_id, user_uuid):
        """Obtiene un organismo específico"""
        try:
            result = self.db.supabase.table('organisms').select("*").eq('id', organism_id).eq('user_uuid', user_uuid).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error getting organism: {e}")
            return None
    
    def update_organism(self, organism_id, user_uuid, data):
        """Actualiza un organismo"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.db.supabase.table('organisms').update(data).eq('id', organism_id).eq('user_uuid', user_uuid).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error updating organism: {e}")
            return None
    
    def toggle_organism_status(self, organism_id, user_uuid):
        """Cambia el estado habilitado/inhabilitado de un organismo"""
        try:
            organism = self.get_organism_by_id(organism_id, user_uuid)
            if organism:
                new_status = not organism['enabled']
                result = self.db.supabase.table('organisms').update({'enabled': new_status}).eq('id', organism_id).eq('user_uuid', user_uuid).execute()
                return result.data[0] if result.data else None
            return None
        except Exception as e:
            logging.error(f"Error toggling organism status: {e}")
            return None
    
    def get_organism_stats(self, organism_id, user_uuid):
        """Obtiene estadísticas de un organismo"""
        try:
            # Obtener inversiones activas del organismo
            investments_result = self.db.supabase.table('investments').select("*").eq('organism_id', organism_id).eq('user_uuid', user_uuid).eq('enabled', True).execute()
            investments = investments_result.data if investments_result.data else []
            
            # Calcular estadísticas
            stats = {
                'total_investments': len(investments),
                'total_amount_usd': 0,
                'total_amount_ars': 0,
                'estimated_return_usd': 0,
                'estimated_return_ars': 0,
                'currency_distribution': {'USD': 0, 'ARS': 0}
            }
            
            for investment in investments:
                amount = float(investment['amount'])
                currency = investment['currency']
                
                if currency == 'USD':
                    stats['total_amount_usd'] += amount
                    stats['currency_distribution']['USD'] += amount
                elif currency == 'ARS':
                    stats['total_amount_ars'] += amount
                    stats['currency_distribution']['ARS'] += amount
                
                # Calcular rendimiento estimado
                if investment['annual_rate'] and investment['end_date']:
                    est_return = self._calculate_estimated_return(investment)
                    if est_return:
                        if currency == 'USD':
                            stats['estimated_return_usd'] += est_return['profit']
                        elif currency == 'ARS':
                            stats['estimated_return_ars'] += est_return['profit']
            
            # Agregar porcentajes seguros para el frontend
            total_currency = stats['currency_distribution']['USD'] + stats['currency_distribution']['ARS']
            stats['currency_percentages'] = {
                'USD': round((stats['currency_distribution']['USD'] / total_currency * 100), 1) if total_currency > 0 else 0.0,
                'ARS': round((stats['currency_distribution']['ARS'] / total_currency * 100), 1) if total_currency > 0 else 0.0
            }
            
            return stats
        except Exception as e:
            logging.error(f"Error getting organism stats: {e}")
            return None
    
    def _calculate_estimated_return(self, investment):
        """Calcula el rendimiento estimado de una inversión (método interno)"""
        if not investment['annual_rate'] or not investment['end_date']:
            return None
        
        try:
            start_date = datetime.fromisoformat(investment['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(investment['end_date'].replace('Z', '+00:00'))
            
            days_invested = (end_date - start_date).days
            annual_rate = investment['annual_rate'] / 100
            daily_rate = annual_rate / 365
            
            estimated_return = investment['amount'] * (1 + daily_rate * days_invested)
            profit = estimated_return - investment['amount']
            
            return {
                'estimated_return': round(estimated_return, 2),
                'profit': round(profit, 2),
                'days_invested': days_invested,
                'percentage_return': round((profit / investment['amount']) * 100, 2)
            }
        except Exception as e:
            logging.error(f"Error calculating return: {e}")
            return None

class OrganismRating:
    def __init__(self, db: Database):
        self.db = db
    
    def create_or_update_rating(self, organism_id, user_uuid, data):
        """Crea o actualiza una calificación de organismo"""
        try:
            rating_data = {
                'organism_id': organism_id,
                'user_uuid': user_uuid,
                'risk_level': float(data['risk_level']),
                'profitability_potential': float(data['profitability_potential']),
                'agility_bureaucracy': float(data['agility_bureaucracy']),
                'transparency': float(data['transparency']),
                'updated_at': datetime.now().isoformat()
            }
            
            # Verificar si ya existe una calificación
            existing = self.get_user_rating(organism_id, user_uuid)
            
            if existing:
                # Actualizar
                result = self.db.supabase.table('organism_ratings').update(rating_data).eq('organism_id', organism_id).eq('user_uuid', user_uuid).execute()
            else:
                # Crear nueva
                rating_data['created_at'] = datetime.now().isoformat()
                result = self.db.supabase.table('organism_ratings').insert(rating_data).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error creating/updating rating: {e}")
            return None
    
    def get_user_rating(self, organism_id, user_uuid):
        """Obtiene la calificación de un usuario para un organismo"""
        try:
            result = self.db.supabase.table('organism_ratings').select("*").eq('organism_id', organism_id).eq('user_uuid', user_uuid).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error getting user rating: {e}")
            return None
    
    def get_organism_average_ratings(self, organism_id):
        """Obtiene las calificaciones promedio de un organismo"""
        try:
            result = self.db.supabase.table('organism_ratings').select("*").eq('organism_id', organism_id).execute()
            ratings = result.data if result.data else []
            
            if not ratings:
                return None
            
            total_ratings = len(ratings)
            avg_ratings = {
                'risk_level': sum(r['risk_level'] for r in ratings) / total_ratings,
                'profitability_potential': sum(r['profitability_potential'] for r in ratings) / total_ratings,
                'agility_bureaucracy': sum(r['agility_bureaucracy'] for r in ratings) / total_ratings,
                'transparency': sum(r['transparency'] for r in ratings) / total_ratings,
                'total_votes': total_ratings
            }
            
            # Redondear a 1 decimal
            for key in avg_ratings:
                if key != 'total_votes':
                    avg_ratings[key] = round(avg_ratings[key], 1)
            
            return avg_ratings
        except Exception as e:
            logging.error(f"Error getting average ratings: {e}")
            return None

class InvestmentMessage:
    def __init__(self, db: Database):
        self.db = db
    
    def create_message(self, investment_id, user_uuid, message):
        """Crea un nuevo mensaje en una inversión"""
        try:
            message_data = {
                'investment_id': investment_id,
                'user_uuid': user_uuid,
                'message': message,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.db.supabase.table('investment_messages').insert(message_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error creating investment message: {e}")
            return None
    
    def get_investment_messages(self, investment_id, user_uuid, limit=50):
        """Obtiene los mensajes de una inversión"""
        try:
            # Verificar que el usuario sea dueño de la inversión
            investment_check = self.db.supabase.table('investments').select("id").eq('id', investment_id).eq('user_uuid', user_uuid).execute()
            if not investment_check.data:
                return []
            
            result = self.db.supabase.table('investment_messages').select("*").eq('investment_id', investment_id).order('created_at', desc=False).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logging.error(f"Error getting investment messages: {e}")
            return []
    
    def delete_message(self, message_id, user_uuid):
        """Elimina un mensaje"""
        try:
            result = self.db.supabase.table('investment_messages').delete().eq('id', message_id).eq('user_uuid', user_uuid).execute()
            return result.data
        except Exception as e:
            logging.error(f"Error deleting investment message: {e}")
            return None

class OrganismMessage:
    def __init__(self, db: Database):
        self.db = db
    
    def create_message(self, organism_id, user_uuid, message):
        """Crea un nuevo mensaje en un organismo"""
        try:
            message_data = {
                'organism_id': organism_id,
                'user_uuid': user_uuid,
                'message': message,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.db.supabase.table('organism_messages').insert(message_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error creating organism message: {e}")
            return None
    
    def get_organism_messages(self, organism_id, user_uuid, limit=50):
        """Obtiene los mensajes de un organismo"""
        try:
            # Verificar que el usuario sea dueño del organismo
            organism_check = self.db.supabase.table('organisms').select("id").eq('id', organism_id).eq('user_uuid', user_uuid).execute()
            if not organism_check.data:
                return []
            
            result = self.db.supabase.table('organism_messages').select("*").eq('organism_id', organism_id).order('created_at', desc=False).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logging.error(f"Error getting organism messages: {e}")
            return []
    
    def delete_message(self, message_id, user_uuid):
        """Elimina un mensaje"""
        try:
            result = self.db.supabase.table('organism_messages').delete().eq('id', message_id).eq('user_uuid', user_uuid).execute()
            return result.data
        except Exception as e:
            logging.error(f"Error deleting organism message: {e}")
            return None

class Investment:
    def __init__(self, db: Database):
        self.db = db
    
    def create_investment(self, user_uuid, data):
        """Crea una nueva inversión"""
        try:
            investment_data = {
                'user_uuid': user_uuid,
                'name': data['name'],
                'organism_id': data.get('organism_id'),  # Usar organism_id en lugar de organism
                'organism': data.get('organism', ''),  # Mantener compatibilidad con texto libre
                'description': data['description'],
                'investment_type': data['investment_type'],
                'status': data['status'],
                'amount': float(data['amount']),
                'currency': data['currency'],
                'start_date': data['start_date'],
                'end_date': data.get('end_date'),
                'annual_rate': float(data['annual_rate']) if data.get('annual_rate') else None,
                'enabled': True,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.db.supabase.table('investments').insert(investment_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error creating investment: {e}")
            return None
    
    def get_user_investments(self, user_uuid, include_disabled=True):
        """Obtiene todas las inversiones de un usuario con información del organismo"""
        try:
            query = self.db.supabase.table('investments').select("""
                *, 
                organisms(id, name, full_name)
            """).eq('user_uuid', user_uuid)
            
            if not include_disabled:
                query = query.eq('enabled', True)
            
            result = query.order('created_at', desc=True).execute()
            return result.data if result.data else []
        except Exception as e:
            logging.error(f"Error getting investments: {e}")
            return []
    
    def get_investment_by_id(self, investment_id, user_uuid):
        """Obtiene una inversión específica con información del organismo"""
        try:
            result = self.db.supabase.table('investments').select("""
                *, 
                organisms(id, name, full_name, description)
            """).eq('id', investment_id).eq('user_uuid', user_uuid).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error getting investment: {e}")
            return None
    
    def get_investments_by_organism(self, organism_id, user_uuid):
        """Obtiene todas las inversiones de un organismo específico"""
        try:
            result = self.db.supabase.table('investments').select("*").eq('organism_id', organism_id).eq('user_uuid', user_uuid).execute()
            return result.data if result.data else []
        except Exception as e:
            logging.error(f"Error getting investments by organism: {e}")
            return []
    
    def update_investment(self, investment_id, user_uuid, data):
        """Actualiza una inversión"""
        try:
            data['updated_at'] = datetime.now().isoformat()
            result = self.db.supabase.table('investments').update(data).eq('id', investment_id).eq('user_uuid', user_uuid).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error updating investment: {e}")
            return None
    
    def toggle_investment_status(self, investment_id, user_uuid):
        """Cambia el estado habilitado/inhabilitado de una inversión"""
        try:
            # Primero obtenemos el estado actual
            investment = self.get_investment_by_id(investment_id, user_uuid)
            if investment:
                new_status = not investment['enabled']
                result = self.db.supabase.table('investments').update({'enabled': new_status}).eq('id', investment_id).eq('user_uuid', user_uuid).execute()
                return result.data[0] if result.data else None
            return None
        except Exception as e:
            logging.error(f"Error toggling investment status: {e}")
            return None
    
    def calculate_estimated_return(self, investment):
        """Calcula el rendimiento estimado de una inversión"""
        if not investment['annual_rate'] or not investment['end_date']:
            return None
        
        try:
            start_date = datetime.fromisoformat(investment['start_date'].replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(investment['end_date'].replace('Z', '+00:00'))
            
            # Calcular días de inversión
            days_invested = (end_date - start_date).days
            
            # Calcular rendimiento
            annual_rate = investment['annual_rate'] / 100
            daily_rate = annual_rate / 365
            
            estimated_return = investment['amount'] * (1 + daily_rate * days_invested)
            profit = estimated_return - investment['amount']
            
            return {
                'estimated_return': round(estimated_return, 2),
                'profit': round(profit, 2),
                'days_invested': days_invested,
                'percentage_return': round((profit / investment['amount']) * 100, 2)
            }
        except Exception as e:
            logging.error(f"Error calculating return: {e}")
            return None
    
    def get_dashboard_stats(self, user_uuid):
        """Obtiene estadísticas para el dashboard"""
        print(f"[DEBUG STATS] ========== INICIANDO get_dashboard_stats ==========")
        print(f"[DEBUG STATS] User UUID: {user_uuid}")
        
        try:
            investments = self.get_user_investments(user_uuid, include_disabled=False)
            print(f"[DEBUG STATS] Inversiones obtenidas: {len(investments) if investments else 0}")
            
            # INICIALIZAR CON VALORES POR DEFECTO GARANTIZADOS
            stats = {
                'total_investments': 0,
                'total_amount_usd': 0,
                'total_amount_ars': 0,
                'estimated_return_usd': 0,
                'estimated_return_ars': 0,
                'active_investments': 0,
                'closed_investments': 0,
                'in_study_investments': 0,
                'currency_distribution': {},
                'status_distribution': {}
            }
            
            print(f"[DEBUG STATS] Stats inicializados: {stats}")
            
            if not investments:
                print("[DEBUG STATS] No hay inversiones, configurando datos por defecto")
                # Retornar datos por defecto si no hay inversiones
                stats['currency_distribution'] = {'USD': 0, 'ARS': 0}
                stats['status_distribution'] = {'activa': 0, 'cerrada': 0, 'en estudio': 0}
                print(f"[DEBUG STATS] Stats finales (sin inversiones): {stats}")
                return stats
            
            stats['total_investments'] = len(investments)
            print(f"[DEBUG STATS] Total de inversiones: {stats['total_investments']}")
            
            # Inicializar contadores
            currency_counts = {}
            status_counts = {}
            
            print(f"[DEBUG STATS] Iniciando procesamiento de inversiones...")
            for i, investment in enumerate(investments):
                print(f"[DEBUG STATS] Procesando inversión {i+1}/{len(investments)}: {investment}")
                try:
                    amount = float(investment.get('amount', 0))
                    currency = investment.get('currency', 'USD')
                    status = investment.get('status', 'activa')
                    
                    print(f"[DEBUG STATS] - Inversión {i+1}: amount={amount}, currency={currency}, status={status}")
                    
                    # Contabilizar por moneda
                    if currency == 'USD':
                        stats['total_amount_usd'] += amount
                    elif currency == 'ARS':
                        stats['total_amount_ars'] += amount
                    
                    # Acumular para distribución de moneda
                    currency_counts[currency] = currency_counts.get(currency, 0) + amount
                    print(f"[DEBUG STATS] - Currency counts actualizados: {currency_counts}")
                    
                    # Acumular para distribución de estado
                    status_counts[status] = status_counts.get(status, 0) + 1
                    print(f"[DEBUG STATS] - Status counts actualizados: {status_counts}")
                    
                    # Contabilizar por estado
                    if status == 'activa':
                        stats['active_investments'] += 1
                    elif status == 'cerrada':
                        stats['closed_investments'] += 1
                    elif status == 'en estudio':
                        stats['in_study_investments'] += 1
                    
                    # Calcular rendimiento estimado
                    if investment.get('annual_rate') and investment.get('end_date'):
                        try:
                            est_return = self.calculate_estimated_return(investment)
                            if est_return and 'profit' in est_return:
                                if currency == 'USD':
                                    stats['estimated_return_usd'] += est_return['profit']
                                elif currency == 'ARS':
                                    stats['estimated_return_ars'] += est_return['profit']
                        except Exception as calc_error:
                            print(f"[DEBUG STATS] Error calculando rendimiento para inversión {i+1}: {calc_error}")
                            
                except Exception as inv_error:
                    print(f"[DEBUG STATS] Error procesando inversión {i+1}: {inv_error}")
                    continue
            
            print(f"[DEBUG STATS] Procesamiento de inversiones completado")
            
            # Asegurar que los diccionarios de distribución no estén vacíos
            stats['currency_distribution'] = currency_counts if currency_counts else {'USD': 0, 'ARS': 0}
            stats['status_distribution'] = status_counts if status_counts else {'activa': 0, 'cerrada': 0, 'en estudio': 0}
            
            print(f"[DEBUG STATS] Stats finales - Currency: {stats['currency_distribution']}")
            print(f"[DEBUG STATS] Stats finales - Status: {stats['status_distribution']}")
            print(f"[DEBUG STATS] Stats completos: {stats}")
            print(f"[DEBUG STATS] ========== FIN get_dashboard_stats - ÉXITO ==========")
            
            return stats
            
        except Exception as e:
            print(f"[ERROR STATS] ========== ERROR EN get_dashboard_stats ==========")
            print(f"[ERROR STATS] Error: {e}")
            print(f"[ERROR STATS] Tipo de error: {type(e)}")
            import traceback
            print(f"[ERROR STATS] Traceback: {traceback.format_exc()}")
            logging.error(f"Error getting dashboard stats: {e}")
            
            # RETORNAR DATOS POR DEFECTO EN CASO DE ERROR
            default_stats = {
                'total_investments': 0,
                'total_amount_usd': 0,
                'total_amount_ars': 0,
                'estimated_return_usd': 0,
                'estimated_return_ars': 0,
                'active_investments': 0,
                'closed_investments': 0,
                'in_study_investments': 0,
                'currency_distribution': {'USD': 0, 'ARS': 0},
                'status_distribution': {'activa': 0, 'cerrada': 0, 'en estudio': 0}
            }
            print(f"[ERROR STATS] Retornando stats por defecto: {default_stats}")
            print(f"[ERROR STATS] ========== FIN get_dashboard_stats - ERROR ==========")
            return default_stats