from supabase import create_client, Client
from datetime import datetime, date
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Obtiene el cliente de Supabase"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL y SUPABASE_ANON_KEY deben estar configurados")
    
    return create_client(url, key)

class PortfolioManager:
    """Gestiona carteras de inversión por organismo"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def create_portfolio(self, organism_id, name, description=None):
        """Crea una nueva cartera para un organismo"""
        try:
            portfolio_data = {
                'organism_id': organism_id,
                'name': name,
                'description': description
            }
            
            result = self.supabase.table('portfolios').insert(portfolio_data).execute()
            
            if result.data:
                logger.info("Cartera creada: %s para organismo %s", name, organism_id)
                return result.data[0]
            else:
                logger.error("Error al crear cartera")
                return None
                
        except Exception as e:
            logger.error("Error creando cartera: %s", str(e))
            return None
    
    def get_portfolios_by_organism(self, organism_id):
        """Obtiene todas las carteras de un organismo"""
        try:
            result = self.supabase.table('portfolios').select('*').eq('organism_id', organism_id).order('created_at', desc=True).execute()
            return result.data
        except Exception as e:
            logger.error("Error obteniendo carteras del organismo %s: %s", organism_id, str(e))
            return []
    
    def get_portfolio_by_id(self, portfolio_id):
        """Obtiene una cartera específica por ID"""
        try:
            result = self.supabase.table('portfolios').select('*').eq('id', portfolio_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error("Error obteniendo cartera %s: %s", portfolio_id, str(e))
            return None
    
    def add_position(self, portfolio_id, symbol, quantity, notes=None):
        """Agrega o actualiza una posición en la cartera (sin average_cost)"""
        try:
            position_data = {
                'portfolio_id': portfolio_id,
                'symbol': symbol.upper(),
                'quantity': float(quantity),
                'notes': notes,
                'updated_at': datetime.now().isoformat()
            }
            
            # Usar upsert para actualizar si ya existe
            result = self.supabase.table('portfolio_positions').upsert(
                position_data,
                on_conflict='portfolio_id,symbol'
            ).execute()
            
            if result.data:
                logger.info("Posición agregada/actualizada: %s en cartera %s", symbol, portfolio_id)
                return result.data[0]
            else:
                logger.error("Error al agregar posición")
                return None
                
        except Exception as e:
            logger.error("Error agregando posición: %s", str(e))
            return None
    
    def update_position(self, portfolio_id, symbol, quantity=None, notes=None):
        """Actualiza una posición existente"""
        try:
            update_data = {'updated_at': datetime.now().isoformat()}
            
            if quantity is not None:
                update_data['quantity'] = float(quantity)
            if notes is not None:
                update_data['notes'] = notes
            
            result = self.supabase.table('portfolio_positions').update(update_data).eq('portfolio_id', portfolio_id).eq('symbol', symbol.upper()).execute()
            
            if result.data:
                logger.info("Posición actualizada: %s en cartera %s", symbol, portfolio_id)
                return result.data[0]
            else:
                logger.warning("No se encontró posición %s en cartera %s", symbol, portfolio_id)
                return None
                
        except Exception as e:
            logger.error("Error actualizando posición: %s", str(e))
            return None
    
    def get_portfolio_positions(self, portfolio_id):
        """Obtiene todas las posiciones de una cartera"""
        try:
            result = self.supabase.table('portfolio_positions').select('*').eq('portfolio_id', portfolio_id).order('symbol').execute()
            return result.data
        except Exception as e:
            logger.error("Error obteniendo posiciones de cartera %s: %s", portfolio_id, str(e))
            return []
    
    def remove_position(self, portfolio_id, symbol):
        """Elimina una posición de la cartera"""
        try:
            result = self.supabase.table('portfolio_positions').delete().eq('portfolio_id', portfolio_id).eq('symbol', symbol.upper()).execute()
            
            if result.data:
                logger.info("Posición eliminada: %s de cartera %s", symbol, portfolio_id)
                return True
            else:
                logger.warning("No se encontró posición %s en cartera %s", symbol, portfolio_id)
                return False
                
        except Exception as e:
            logger.error("Error eliminando posición: %s", str(e))
            return False
    
    def calculate_portfolio_value(self, portfolio_id, target_date=None):
        """
        Calcula el valor de la cartera usando datos históricos de mercado
        
        Args:
            portfolio_id: ID de la cartera
            target_date: Fecha específica (YYYY-MM-DD), si es None usa la fecha actual
        
        Returns:
            Diccionario con el valor total y detalle de posiciones
        """
        try:
            positions = self.get_portfolio_positions(portfolio_id)
            
            if not positions:
                return {
                    'total_value': 0,
                    'calculation_date': target_date or date.today().isoformat(),
                    'positions_detail': [],
                    'symbols_not_found': []
                }
            
            # Usar fecha actual si no se especifica
            if not target_date:
                target_date = date.today().isoformat()
            
            # Obtener precios históricos para esa fecha
            prices = self._get_historical_prices([pos['symbol'] for pos in positions], target_date)
            
            positions_detail = []
            total_value = 0
            symbols_not_found = []
            
            for position in positions:
                symbol = position['symbol']
                quantity = float(position['quantity'])
                current_price = prices.get(symbol)
                
                if current_price is None:
                    # Intentar con el precio más reciente disponible
                    current_price = self._get_latest_price_for_symbol(symbol)
                    if current_price is None:
                        current_price = 0
                        symbols_not_found.append(symbol)
                
                position_value = quantity * current_price
                
                positions_detail.append({
                    'symbol': symbol,
                    'quantity': quantity,
                    'current_price': current_price,
                    'position_value': position_value,
                    'notes': position.get('notes', ''),
                    'updated_at': position.get('updated_at', '')
                })
                
                total_value += position_value
            
            # Calcular porcentajes de peso
            for detail in positions_detail:
                detail['weight_percentage'] = (detail['position_value'] / total_value * 100) if total_value > 0 else 0
            
            return {
                'total_value': total_value,
                'calculation_date': target_date,
                'positions_detail': positions_detail,
                'symbols_not_found': symbols_not_found
            }
            
        except Exception as e:
            logger.error("Error calculando valor de cartera %s: %s", portfolio_id, str(e))
            return None
    
    def _get_historical_prices(self, symbols, target_date):
        """Obtiene precios históricos para una fecha específica"""
        try:
            prices = {}
            
            for symbol in symbols:
                result = self.supabase.table('market_data_history').select('price').eq('symbol', symbol).eq('date', target_date).execute()
                
                if result.data:
                    prices[symbol] = float(result.data[0]['price'])
                else:
                    # Buscar el precio más cercano anterior a la fecha objetivo
                    result = self.supabase.table('market_data_history').select('price').eq('symbol', symbol).lte('date', target_date).order('date', desc=True).limit(1).execute()
                    
                    if result.data:
                        prices[symbol] = float(result.data[0]['price'])
                    else:
                        prices[symbol] = None
            
            return prices
            
        except Exception as e:
            logger.error("Error obteniendo precios históricos: %s", str(e))
            return {}
    
    def _get_latest_price_for_symbol(self, symbol):
        """Obtiene el precio más reciente disponible para un símbolo"""
        try:
            result = self.supabase.table('market_data_history').select('price').eq('symbol', symbol).order('date', desc=True).limit(1).execute()
            
            if result.data:
                return float(result.data[0]['price'])
            else:
                # Fallback: intentar obtener desde Google Sheets
                current_prices = self._get_current_prices_from_sheets([symbol])
                return current_prices.get(symbol, 0)
                
        except Exception as e:
            logger.error("Error obteniendo precio más reciente para %s: %s", symbol, str(e))
            return 0
    
    def _get_current_prices_from_sheets(self, symbols):
        """Obtiene precios actuales desde Google Sheets (fallback)"""
        try:
            from google_sheets_service import google_sheets_service
            
            market_data = google_sheets_service.get_market_data()
            
            if not market_data:
                return {}
            
            # Si market_data es un diccionario con 'data'
            if isinstance(market_data, dict) and 'data' in market_data:
                data_list = market_data['data']
            elif isinstance(market_data, list):
                data_list = market_data
            else:
                return {}
            
            current_prices = {}
            for item in data_list:
                symbol = item.get('symbol', '').upper()
                price = item.get('price')
                
                if symbol in symbols and price not in ['#N/A', 'N/A', 'Cargando...', None]:
                    try:
                        # Limpiar el precio (quitar $ y comas)
                        price_str = str(price).replace('$', '').replace(',', '').strip()
                        current_prices[symbol] = float(price_str)
                    except (ValueError, TypeError):
                        current_prices[symbol] = 0
            
            return current_prices
            
        except Exception as e:
            logger.error("Error obteniendo precios desde Google Sheets: %s", str(e))
            return {}
    
    def get_portfolio_stats(self, portfolio_id):
        """Obtiene estadísticas resumidas de la cartera"""
        try:
            portfolio_value = self.calculate_portfolio_value(portfolio_id)
            
            if not portfolio_value:
                return None
            
            positions = portfolio_value['positions_detail']
            
            return {
                'total_positions': len(positions),
                'total_value': portfolio_value['total_value'],
                'calculation_date': portfolio_value['calculation_date'],
                'symbols_count': len([p for p in positions if p['current_price'] > 0]),
                'symbols_not_found': len(portfolio_value['symbols_not_found'])
            }
            
        except Exception as e:
            logger.error("Error obteniendo estadísticas de cartera %s: %s", portfolio_id, str(e))
            return None
    
    def update_portfolio(self, portfolio_id, name=None, description=None):
        """Actualiza información de la cartera"""
        try:
            update_data = {'updated_at': datetime.now().isoformat()}
            
            if name:
                update_data['name'] = name
            if description is not None:  # Permitir string vacío
                update_data['description'] = description
            
            result = self.supabase.table('portfolios').update(update_data).eq('id', portfolio_id).execute()
            
            if result.data:
                logger.info("Cartera %s actualizada", portfolio_id)
                return result.data[0]
            else:
                logger.error("Error actualizando cartera %s", portfolio_id)
                return None
                
        except Exception as e:
            logger.error("Error actualizando cartera: %s", str(e))
            return None
    
    def delete_portfolio(self, portfolio_id):
        """Elimina una cartera y todas sus posiciones"""
        try:
            # Las posiciones se eliminan automáticamente por ON DELETE CASCADE
            result = self.supabase.table('portfolios').delete().eq('id', portfolio_id).execute()
            
            if result.data:
                logger.info("Cartera %s eliminada", portfolio_id)
                return True
            else:
                logger.warning("No se encontró cartera %s", portfolio_id)
                return False
                
        except Exception as e:
            logger.error("Error eliminando cartera: %s", str(e))
            return False

# Instancia global del manejador de carteras
portfolio_manager = PortfolioManager()
