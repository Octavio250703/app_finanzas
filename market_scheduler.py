import schedule
import time
import threading
from datetime import datetime
import logging
from market_history_model import save_daily_snapshot

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataScheduler:
    """Programador para tareas automáticas de datos de mercado"""
    
    def __init__(self):
        self.running = False
        self.thread = None
        self._setup_schedule()
    
    def _setup_schedule(self):
        """Configura las tareas programadas"""
        # Programar el snapshot diario 5 veces al día
        schedule.every().day.at("09:00").do(self._run_snapshot)
        schedule.every().day.at("12:00").do(self._run_snapshot)
        schedule.every().day.at("15:00").do(self._run_snapshot)
        schedule.every().day.at("18:00").do(self._run_snapshot)
        schedule.every().day.at("21:00").do(self._run_snapshot)
        
        logger.info("Scheduler configurado: snapshots a las 09:00, 12:00, 15:00, 18:00 y 21:00")
    
    def _run_snapshot(self):
        """Ejecuta el snapshot diario"""
        try:
            logger.info(f"Iniciando snapshot automático - {datetime.now()}")
            success = save_daily_snapshot()
            
            if success:
                logger.info("Snapshot automático completado exitosamente")
            else:
                logger.warning("Snapshot automático falló")
                
        except Exception as e:
            logger.error(f"Error en snapshot automático: {str(e)}")
    
    def start(self):
        """Inicia el scheduler en un hilo separado"""
        if self.running:
            logger.warning("El scheduler ya está ejecutándose")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Market Data Scheduler iniciado en hilo separado")
    
    def stop(self):
        """Detiene el scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Market Data Scheduler detenido")
    
    def _run_scheduler(self):
        """Bucle principal del scheduler"""
        logger.info("Bucle del scheduler iniciado")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
            except Exception as e:
                logger.error(f"Error en bucle del scheduler: {str(e)}")
                time.sleep(60)
        
        logger.info("Bucle del scheduler terminado")
    
    def run_manual_snapshot(self):
        """Ejecuta un snapshot manual (para botón en interfaz)"""
        try:
            logger.info("Iniciando snapshot manual")
            success = save_daily_snapshot()
            return success
        except Exception as e:
            logger.error(f"Error en snapshot manual: {str(e)}")
            return False
    
    def get_next_run_time(self):
        """Obtiene la hora de la próxima ejecución programada"""
        try:
            next_run = schedule.next_run()
            return next_run.strftime("%H:%M:%S") if next_run else "No programado"
        except:
            return "Error"
    
    def get_status(self):
        """Obtiene el estado del scheduler"""
        return {
            'running': self.running,
            'next_run': self.get_next_run_time(),
            'jobs_count': len(schedule.jobs),
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Instancia global del scheduler
market_scheduler = MarketDataScheduler()

def start_scheduler():
    """Función de conveniencia para iniciar el scheduler"""
    market_scheduler.start()

def stop_scheduler():
    """Función de conveniencia para detener el scheduler"""
    market_scheduler.stop()

def manual_snapshot():
    """Función de conveniencia para snapshot manual"""
    return market_scheduler.run_manual_snapshot()

def get_scheduler_status():
    """Función de conveniencia para obtener el estado"""
    return market_scheduler.get_status()