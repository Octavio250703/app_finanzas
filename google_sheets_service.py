"""
Servicio para obtener datos de Google Sheets públicos
"""
import requests
import csv
import io
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        # URL base para acceder a Google Sheets como CSV
        self.base_url = "https://docs.google.com/spreadsheets/d/e/{sheet_id}/pub?output=csv"
    
    def get_sheet_data(self, sheet_id: str) -> Optional[List[Dict]]:
        """
        Obtiene datos de un Google Sheet público
        
        Args:
            sheet_id: ID del Google Sheet público
            
        Returns:
            Lista de diccionarios con los datos o None si hay error
        """
        try:
            url = self.base_url.format(sheet_id=sheet_id)
            logger.info("Obteniendo datos de Google Sheet: %s", url)
            
            # Realizar petición HTTP
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Parsear CSV
            csv_data = response.text
            reader = csv.DictReader(io.StringIO(csv_data))
            
            data = []
            for row in reader:
                # Limpiar los datos (remover espacios en blanco)
                cleaned_row = {k.strip(): v.strip() for k, v in row.items() if k and v}
                if cleaned_row:  # Solo agregar filas no vacías
                    data.append(cleaned_row)
            
            logger.info("✅ Datos obtenidos exitosamente: %s filas", len(data))
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error("❌ Error al obtener datos de Google Sheets: %s", str(e))
            return None
        except Exception as e:
            logger.error("❌ Error procesando datos de Google Sheets: %s", str(e))
            return None
    
    def get_market_data(self) -> Optional[List[Dict]]:
        """
        Obtiene datos específicos del Google Sheet de mercado
        
        Returns:
            Lista con datos de symbol y price
        """
        # ID extraído de tu URL
        sheet_id = "2PACX-1vRYSd8G18V945mwYirKuzuTf8hQf3SySFDVL0D5dpWu1MWgCwH1oTwii0O57N2tl7vIZZT6zDGGc1wj"
        
        raw_data = self.get_sheet_data(sheet_id)
        if not raw_data:
            return None
        
        try:
            market_data = []
            for row in raw_data:
                # Buscar las columnas symbol y price (pueden tener variaciones de nombre)
                symbol = None
                price = None
                
                # Buscar columna symbol (case insensitive)
                for key in row.keys():
                    if key.lower() in ['symbol', 'simbolo', 'ticker']:
                        symbol = row[key]
                        break
                
                # Buscar columna price (case insensitive)
                for key in row.keys():
                    if key.lower() in ['price', 'precio', 'valor', 'cotizacion']:
                        try:
                            # Intentar convertir a float
                            price_str = row[key].replace(',', '').replace('$', '').strip()
                            price = float(price_str) if price_str else None
                        except (ValueError, AttributeError):
                            price = row[key]
                        break
                
                if symbol and price is not None:
                    market_data.append({
                        'symbol': symbol,
                        'price': price,
                        'raw_data': row  # Mantener datos originales por si acaso
                    })
            
            logger.info("✅ Datos de mercado procesados: %s símbolos", len(market_data))
            return market_data
            
        except Exception as e:
            logger.error("❌ Error procesando datos de mercado: %s", str(e))
            return None

# Instancia global del servicio
google_sheets_service = GoogleSheetsService()
