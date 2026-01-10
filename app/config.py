"""
Configuration centralisée de l'application
==========================================
Gère tous les paramètres de configuration par environnement
"""
import os
from pathlib import Path

# Chemins de base
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / 'temp_uploads'
RESULTS_DIR = BASE_DIR / 'results'
LOGS_DIR = BASE_DIR / 'logs'

# Créer les dossiers s'ils n'existent pas
for directory in [TEMP_DIR, RESULTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class Config:
    """Configuration de base"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Application
    APP_NAME = 'Distillation Multicomposants'
    VERSION = '2.0.0'
    
    # Chemins
    UPLOAD_FOLDER = str(TEMP_DIR)
    RESULTS_FOLDER = str(RESULTS_DIR)
    LOGS_FOLDER = str(LOGS_DIR)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # Cache Redis
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 3600
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Session
    SESSION_TYPE = 'redis'
    SESSION_REDIS = None  # Sera configuré à l'init
    PERMANENT_SESSION_LIFETIME = 86400  # 24 heures
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Celery (pour tâches async futures)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/2')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    @staticmethod
    def init_app(app):
        """Initialisation spécifique à l'application"""
        pass


class DevelopmentConfig(Config):
    """Configuration pour développement"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        print(f"🔧 Mode: DEVELOPMENT")
        print(f"📁 Temp: {cls.UPLOAD_FOLDER}")
        print(f"📁 Results: {cls.RESULTS_FOLDER}")


class ProductionConfig(Config):
    """Configuration pour production"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'WARNING'
    
    # Sécurité renforcée
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # SECRET_KEY doit être définie en production
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Vérifier que SECRET_KEY est définie
        if cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production!")
        
        # Logger vers fichier en production
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                f'{cls.LOGS_FOLDER}/app.log',
                maxBytes=10240000,  # 10MB
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(cls.LOG_FORMAT))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info(f'{cls.APP_NAME} startup (PRODUCTION)')


class TestingConfig(Config):
    """Configuration pour tests"""
    TESTING = True
    DEBUG = True
    
    # Utiliser des bases de données de test
    CACHE_TYPE = 'simple'
    CACHE_REDIS_URL = None
    
    # Désactiver CSRF pour les tests
    WTF_CSRF_ENABLED = False


class DockerConfig(ProductionConfig):
    """Configuration pour Docker"""
    
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)
        
        # Log vers stdout pour Docker
        import logging
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info(f'{cls.APP_NAME} startup (DOCKER)')


# Dictionnaire de configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retourne la configuration selon l'environnement"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])