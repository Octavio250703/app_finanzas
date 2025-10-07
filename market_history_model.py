from supabase import create_client, Client
from google_sheets_service import google_sheets_service
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

def save_daily_snapshot():
    try:
        print("🔄 Iniciando save_daily_snapshot")
        
        # Obtener datos de Google Sheets
        market_data_response = google_sheets_service.get_market_data()
        
        # Manejar que puede ser una lista directamente
        if isinstance(market_data_response, list):
            market_data = market_data_response
            print(f"✅ Datos son una lista directa: {len(market_data)} elementos")
        elif isinstance(market_data_response, dict) and 'data' in market_data_response:
            market_data = market_data_response['data']
            print(f"✅ Datos extraídos de diccionario: {len(market_data)} elementos")
        else:
            print(f"❌ Tipo de datos inesperado: {type(market_data_response)}")
            return False
            
        if not market_data:
            print("❌ No hay datos de mercado para guardar")
            return False
            
        print(f"💾 Guardando snapshot de {len(market_data)} símbolos...")
        
        # OBTENER CLIENTE DE SUPABASE
        supabase = get_supabase_client()
        
        saved_count = 0
        updated_count = 0
        errors = 0
        
        # Fecha actual para el snapshot
        today = date.today().isoformat()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        for item in market_data:
            try:
                symbol = item.get('symbol', '').upper()
                price = item.get('price')
                
                print(f"Procesando: {symbol} - ${price}")
                
                # Manejar precios inválidos
                if price in ['#N/A', 'N/A', 'Cargando...'] or price is None:
                    price_numeric = None
                else:
                    try:
                        price_numeric = float(price)
                    except (ValueError, TypeError):
                        price_numeric = None
                        print(f"  ⚠️ Precio inválido para {symbol}: {price}")
                
                # Preparar datos para insertar/actualizar
                record_data = {
                    'symbol': symbol,
                    'price': price_numeric,
                    'raw_price': str(price),
                    'date': today,
                    'timestamp': timestamp,
                    'source': 'google_sheets'
                }
                
                # USAR UPSERT - Actualizar si existe, insertar si no existe
                result = supabase.table('market_data_history').upsert(
                    record_data,
                    on_conflict='symbol,date'  # Campos únicos
                ).execute()
                
                if result.data:
                    print(f"  ✅ Upsert exitoso: {symbol}")
                    saved_count += 1
                else:
                    print(f"  ❌ Error en upsert {symbol}: No se obtuvo respuesta")
                    errors += 1
                    
            except Exception as item_error:
                print(f"  ❌ Error procesando {item.get('symbol', 'Unknown')}: {str(item_error)}")
                errors += 1
                continue
        
        print(f"🎉 Snapshot completado: {saved_count} registros procesados, {errors} errores")
        return saved_count > 0
        
    except Exception as e:
        print(f"❌ ERROR al guardar snapshot diario: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def get_market_history(symbol=None, start_date=None, end_date=None, limit=100):
    """Obtiene el historial de datos de mercado
    
    Args:
        symbol: Filtrar por símbolo específico
        start_date: Fecha de inicio (YYYY-MM-DD)
        end_date: Fecha de fin (YYYY-MM-DD)
        limit: Límite de registros
    
    Returns:
        Lista de registros del historial
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.table('market_data_history').select('*')
        
        if symbol:
            query = query.eq('symbol', symbol)
        
        if start_date:
            query = query.gte('date', start_date)
        
        if end_date:
            query = query.lte('date', end_date)
        
        query = query.order('date', desc=True).order('symbol').limit(limit)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        logger.error(f"Error al obtener historial: {str(e)}")
        return []

def get_latest_prices():
    """Obtiene los precios más recientes de cada símbolo"""
    try:
        supabase = get_supabase_client()
        
        # Subconsulta para obtener la fecha más reciente por símbolo
        result = supabase.rpc('get_latest_market_prices').execute()
        
        if not result.data:
            # Fallback: obtener registros más recientes manualmente
            result = supabase.table('market_data_history').select('*').order('date', desc=True).limit(50).execute()
            
            # Agrupar por símbolo y tomar el más reciente
            latest_by_symbol = {}
            for record in result.data:
                symbol = record['symbol']
                if symbol not in latest_by_symbol or record['date'] > latest_by_symbol[symbol]['date']:
                    latest_by_symbol[symbol] = record
            
            return list(latest_by_symbol.values())
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error al obtener precios más recientes: {str(e)}")
        return []

def get_symbol_history(symbol, days=30):
    """Obtiene el historial de un símbolo específico para los últimos N días"""
    try:
        supabase = get_supabase_client()
        
        # Calcular fecha de inicio
        from datetime import timedelta
        start_date = (date.today() - timedelta(days=days)).isoformat()
        
        result = supabase.table('market_data_history').select('*').eq('symbol', symbol).gte('date', start_date).order('date', desc=True).execute()
        
        return result.data
        
    except Exception as e:
        logger.error(f"Error al obtener historial de {symbol}: {str(e)}")
        return []
