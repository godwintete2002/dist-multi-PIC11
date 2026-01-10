"""
Système de logging centralisé
==============================
Configuration avancée du logging avec rotation et niveaux
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
import json


class ColoredFormatter(logging.Formatter):
    """Formatter avec couleurs pour la console"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Vert
        'WARNING': '\033[33m',    # Jaune
        'ERROR': '\033[31m',      # Rouge
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        record.name = f"\033[94m{record.name}{self.RESET}"  # Bleu
        return super().format(record)


class JSONFormatter(logging.Formatter):
    """Formatter JSON pour logging structuré"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logger(name: str, log_level: str = 'INFO', 
                 log_file: str = None, 
                 console: bool = True,
                 json_format: bool = False) -> logging.Logger:
    """
    Configure un logger avec handlers personnalisés
    
    Parameters:
    -----------
    name : str
        Nom du logger
    log_level : str
        Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_file : str
        Chemin du fichier de log (optionnel)
    console : bool
        Afficher dans la console
    json_format : bool
        Utiliser le format JSON
    
    Returns:
    --------
    logger : logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Supprimer les handlers existants
    logger.handlers.clear()
    
    # Format
    if json_format:
        formatter = JSONFormatter()
    else:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        formatter = logging.Formatter(log_format, date_format)
    
    # Handler console
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        
        if not json_format:
            console_formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
        else:
            console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    # Handler fichier avec rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def setup_app_logging(app):
    """
    Configure le logging pour l'application Flask
    
    Parameters:
    -----------
    app : Flask
        Instance Flask
    """
    from app.config import LOGS_DIR
    
    # Logger principal de l'app
    app_logger = setup_logger(
        'distillation_app',
        log_level=app.config.get('LOG_LEVEL', 'INFO'),
        log_file=str(LOGS_DIR / 'app.log'),
        console=True,
        json_format=app.config.get('JSON_LOGS', False)
    )
    
    # Logger pour les requêtes
    request_logger = setup_logger(
        'distillation_requests',
        log_level='INFO',
        log_file=str(LOGS_DIR / 'requests.log'),
        console=False,
        json_format=True
    )
    
    # Logger pour les erreurs
    error_logger = setup_logger(
        'distillation_errors',
        log_level='ERROR',
        log_file=str(LOGS_DIR / 'errors.log'),
        console=True,
        json_format=False
    )
    
    # Logger pour les simulations
    sim_logger = setup_logger(
        'distillation_simulations',
        log_level='INFO',
        log_file=str(LOGS_DIR / 'simulations.log'),
        console=False,
        json_format=True
    )
    
    app_logger.info(f"✅ Logging configuré - Niveau: {app.config.get('LOG_LEVEL', 'INFO')}")
    
    return {
        'app': app_logger,
        'requests': request_logger,
        'errors': error_logger,
        'simulations': sim_logger
    }


class RequestLogger:
    """Middleware pour logger les requêtes HTTP"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialise le middleware"""
        logger = logging.getLogger('distillation_requests')
        
        @app.before_request
        def log_request():
            from flask import request
            logger.info({
                'method': request.method,
                'path': request.path,
                'ip': request.remote_addr,
                'user_agent': request.user_agent.string
            })
        
        @app.after_request
        def log_response(response):
            from flask import request
            logger.info({
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'size': response.content_length
            })
            return response


class PerformanceLogger:
    """Logger pour mesurer les performances"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.logger = logging.getLogger('distillation_performance')
        self.start_time = None
    
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"🚀 Début: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        
        if exc_type is None:
            self.logger.info(f"✅ Terminé: {self.operation_name} ({duration:.3f}s)")
        else:
            self.logger.error(f"❌ Échec: {self.operation_name} ({duration:.3f}s) - {exc_val}")
        
        return False  # Re-raise exception si elle existe


# Décorateur pour logger les fonctions
def log_function_call(logger_name='distillation_app'):
    """
    Décorateur pour logger automatiquement les appels de fonction
    
    Usage:
    ------
    @log_function_call('my_logger')
    def my_function(arg1, arg2):
        ...
    """
    def decorator(func):
        from functools import wraps
        logger = logging.getLogger(logger_name)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Appel: {func.__name__}(args={args}, kwargs={kwargs})")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Retour: {func.__name__} -> {type(result).__name__}")
                return result
            
            except Exception as e:
                logger.error(f"Erreur dans {func.__name__}: {str(e)}", exc_info=True)
                raise
        
        return wrapper
    
    return decorator


# Exemple d'utilisation
if __name__ == '__main__':
    # Test du logger
    logger = setup_logger('test_logger', 'DEBUG', 'test.log')
    
    logger.debug("Ceci est un message DEBUG")
    logger.info("Ceci est un message INFO")
    logger.warning("Ceci est un message WARNING")
    logger.error("Ceci est un message ERROR")
    logger.critical("Ceci est un message CRITICAL")
    
    # Test du performance logger
    with PerformanceLogger("Test operation"):
        import time
        time.sleep(0.5)
    
    print("✅ Tests du logger terminés")