"""
Application Flask Principale - Distillation Multicomposants
============================================================
Version 2.0 - Architecture optimisée avec API REST et WebSocket

Auteur: Prof. BAKHER Zine Elabidine
Améliorations: Architecture moderne, performance, scalabilité
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_caching import Cache
import logging
from datetime import datetime
import json
import os
from pathlib import Path

# Imports locaux
from app.core.compound import Compound
from app.core.thermodynamics import ThermodynamicPackage
from app.core.shortcut_methods import ShortcutDistillation
from app.pdf_generation.report_generator import ReportGenerator
from app.visualization.plotly_viz import DistillationVisualizer
from app.utils.cache import CacheManager
from app.utils.validators import validate_input_data
from app.utils.logger import setup_logger

# Configuration
class Config:
    """Configuration centralisée de l'application"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # Cache Redis
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Upload
    UPLOAD_FOLDER = Path('temp_uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Résultats
    RESULTS_FOLDER = Path('results')
    
    # WebSocket
    SOCKETIO_MESSAGE_QUEUE = os.getenv('REDIS_URL', 'redis://localhost:6379/1')


def create_app(config_class=Config):
    """Factory pour créer l'application Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Créer les dossiers nécessaires
    config_class.UPLOAD_FOLDER.mkdir(exist_ok=True)
    config_class.RESULTS_FOLDER.mkdir(exist_ok=True)
    
    # Extensions
    CORS(app)
    cache = Cache(app)
    socketio = SocketIO(app, cors_allowed_origins="*", message_queue=app.config['SOCKETIO_MESSAGE_QUEUE'])
    
    # Logger
    logger = setup_logger('distillation_app')
    
    # Cache manager
    cache_manager = CacheManager(app.config['CACHE_REDIS_URL'])
    
    # ========================================================================
    # ROUTES PRINCIPALES
    # ========================================================================
    
    @app.route('/')
    def index():
        """Page d'accueil"""
        return render_template('index.html')
    
    @app.route('/simulation')
    def simulation():
        """Page de simulation interactive"""
        return render_template('simulation.html')
    
    @app.route('/documentation')
    def documentation():
        """Page de documentation"""
        return render_template('documentation.html')
    
    # ========================================================================
    # API REST
    # ========================================================================
    
    @app.route('/api/compounds', methods=['GET'])
    @cache.cached(timeout=3600, query_string=True)
    def get_compounds():
        """
        Récupère la liste des composés disponibles
        
        Returns:
            JSON: Liste des composés avec leurs propriétés
        """
        try:
            common_compounds = [
                'benzene', 'toluene', 'o-xylene', 'm-xylene', 'p-xylene',
                'ethanol', 'methanol', 'water', 'acetone', 'butanol'
            ]
            
            compounds_data = []
            for name in common_compounds:
                try:
                    comp = Compound(name)
                    compounds_data.append({
                        'name': name,
                        'Tb': round(comp.Tb - 273.15, 2),
                        'Tc': round(comp.Tc - 273.15, 2),
                        'MW': round(comp.MW, 2)
                    })
                except:
                    continue
            
            return jsonify({
                'success': True,
                'compounds': compounds_data
            })
        
        except Exception as e:
            logger.error(f"Erreur get_compounds: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/simulate', methods=['POST'])
    def simulate():
        """
        Lance une simulation de distillation
        
        Request JSON:
            {
                "compounds": ["benzene", "toluene", "o-xylene"],
                "feed_flow": 100.0,
                "feed_composition": [0.33, 0.33, 0.34],
                "pressure": 101325,
                "recovery_LK": 0.95,
                "recovery_HK": 0.95,
                "reflux_factor": 1.3,
                "feed_quality": 1.0,
                "efficiency": 0.70
            }
        
        Returns:
            JSON: Résultats de la simulation
        """
        try:
            data = request.get_json()
            
            # Validation
            is_valid, error_msg = validate_input_data(data)
            if not is_valid:
                return jsonify({'success': False, 'error': error_msg}), 400
            
            # Générer une clé de cache
            cache_key = cache_manager.generate_key('simulation', data)
            
            # Vérifier le cache
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Résultat récupéré du cache: {cache_key}")
                return jsonify({
                    'success': True,
                    'from_cache': True,
                    'results': cached_result
                })
            
            # Émettre le début de la simulation via WebSocket
            socketio.emit('simulation_started', {
                'timestamp': datetime.now().isoformat(),
                'status': 'Initialisation...'
            })
            
            # Créer les composés
            socketio.emit('simulation_progress', {'progress': 10, 'status': 'Chargement des composés...'})
            compounds = [Compound(name) for name in data['compounds']]
            thermo = ThermodynamicPackage(compounds)
            
            # Initialiser la simulation
            socketio.emit('simulation_progress', {'progress': 30, 'status': 'Configuration de la colonne...'})
            shortcut = ShortcutDistillation(
                thermo, 
                data['feed_flow'], 
                data['feed_composition'], 
                data['pressure']
            )
            
            # Dimensionnement
            socketio.emit('simulation_progress', {'progress': 60, 'status': 'Calculs en cours...'})
            results = shortcut.complete_shortcut_design(
                recovery_LK_D=data.get('recovery_LK', 0.95),
                recovery_HK_B=data.get('recovery_HK', 0.95),
                R_factor=data.get('reflux_factor', 1.3),
                q=data.get('feed_quality', 1.0),
                efficiency=data.get('efficiency', 0.70)
            )
            
            # Générer les visualisations
            socketio.emit('simulation_progress', {'progress': 80, 'status': 'Génération des graphiques...'})
            visualizer = DistillationVisualizer(data['compounds'])
            
            # Sauvegarder les résultats
            session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_dir = Config.RESULTS_FOLDER / session_id
            results_dir.mkdir(exist_ok=True)
            
            # Préparer la réponse
            response_data = {
                'session_id': session_id,
                'results': {
                    'N_min': float(results['N_min']),
                    'N_real': int(results['N_real']),
                    'R_min': float(results['R_min']),
                    'R': float(results['R']),
                    'feed_stage': int(results['feed_stage']),
                    'D': float(results['D']),
                    'B': float(results['B']),
                    'x_D': [float(x) for x in results['x_D']],
                    'x_B': [float(x) for x in results['x_B']]
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Mettre en cache
            cache_manager.set(cache_key, response_data, timeout=3600)
            
            socketio.emit('simulation_completed', {
                'progress': 100, 
                'status': 'Terminé!',
                'session_id': session_id
            })
            
            logger.info(f"Simulation complétée: {session_id}")
            
            return jsonify({
                'success': True,
                'from_cache': False,
                'results': response_data
            })
        
        except Exception as e:
            logger.error(f"Erreur simulation: {e}", exc_info=True)
            socketio.emit('simulation_error', {'error': str(e)})
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/generate_pdf/<session_id>', methods=['GET'])
    def generate_pdf(session_id):
        """
        Génère un rapport PDF pour une simulation
        
        Args:
            session_id: ID de la session de simulation
        
        Returns:
            PDF file
        """
        try:
            results_dir = Config.RESULTS_FOLDER / session_id
            
            if not results_dir.exists():
                return jsonify({'success': False, 'error': 'Session non trouvée'}), 404
            
            # Charger les résultats
            results_file = results_dir / 'results.json'
            if not results_file.exists():
                return jsonify({'success': False, 'error': 'Résultats non trouvés'}), 404
            
            with open(results_file, 'r') as f:
                results = json.load(f)
            
            # Générer le PDF
            generator = ReportGenerator()
            pdf_path = results_dir / f'rapport_{session_id}.pdf'
            
            generator.generate_report(
                results=results,
                output_path=str(pdf_path)
            )
            
            logger.info(f"PDF généré: {pdf_path}")
            
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f'rapport_distillation_{session_id}.pdf',
                mimetype='application/pdf'
            )
        
        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/visualizations/<session_id>', methods=['GET'])
    def get_visualizations(session_id):
        """
        Récupère les visualisations d'une simulation
        
        Args:
            session_id: ID de la session
        
        Returns:
            JSON: URLs des visualisations
        """
        try:
            results_dir = Config.RESULTS_FOLDER / session_id
            
            if not results_dir.exists():
                return jsonify({'success': False, 'error': 'Session non trouvée'}), 404
            
            visualizations = []
            for img_file in results_dir.glob('*.png'):
                visualizations.append({
                    'name': img_file.stem,
                    'url': f'/static/results/{session_id}/{img_file.name}'
                })
            
            return jsonify({
                'success': True,
                'visualizations': visualizations
            })
        
        except Exception as e:
            logger.error(f"Erreur get_visualizations: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ========================================================================
    # WEBSOCKET EVENTS
    # ========================================================================
    
    @socketio.on('connect')
    def handle_connect():
        """Client connecté au WebSocket"""
        logger.info(f"Client connecté: {request.sid}")
        emit('connected', {'message': 'Connexion établie'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Client déconnecté"""
        logger.info(f"Client déconnecté: {request.sid}")
    
    # ========================================================================
    # ERROR HANDLERS
    # ========================================================================
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'error': 'Route non trouvée'}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Erreur serveur: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Erreur serveur interne'}), 500
    
    # ========================================================================
    # HEALTH CHECK
    # ========================================================================
    
    @app.route('/health')
    def health():
        """Endpoint de santé pour monitoring"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
    
    return app, socketio


# Point d'entrée
if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )