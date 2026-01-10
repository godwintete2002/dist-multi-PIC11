"""Application Flask Principale"""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
import logging

from .config import config
from .core.compound import Compound
from .core.thermodynamics import ThermodynamicPackage
from .core.shortcut_methods import ShortcutDistillation
from .utils.validators import validate_input_data
from .utils.logger import setup_logger
from .utils.cache import CacheManager

logger = setup_logger('distillation_app')

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    cache_manager = CacheManager(app.config['CACHE_REDIS_URL'])
    
    @app.route('/')
    def index():
        return "<h1>Distillation Multicomposants V2.0</h1><p>API disponible a /api/compounds</p>"
    
    @app.route('/api/compounds', methods=['GET'])
    def get_compounds():
        try:
            common_compounds = ['benzene', 'toluene', 'o-xylene', 'ethanol', 'methanol', 'acetone']
            compounds_data = []
            for name in common_compounds:
                try:
                    comp = Compound(name)
                    compounds_data.append({'name': name, 'Tb': round(comp.Tb - 273.15, 2), 'MW': round(comp.MW, 2)})
                except:
                    continue
            return jsonify({'success': True, 'compounds': compounds_data})
        except Exception as e:
            logger.error(f"Erreur get_compounds: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/simulate', methods=['POST'])
    def simulate():
        try:
            data = request.get_json()
            is_valid, error_msg = validate_input_data(data)
            if not is_valid:
                return jsonify({'success': False, 'error': error_msg}), 400
            
            cache_key = cache_manager.generate_key('simulation', data)
            cached_result = cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Resultat du cache: {cache_key}")
                return jsonify({'success': True, 'from_cache': True, 'results': cached_result})
            
            compounds = [Compound(name) for name in data['compounds']]
            thermo = ThermodynamicPackage(compounds)
            shortcut = ShortcutDistillation(thermo, data['feed_flow'], data['feed_composition'], data['pressure'])
            
            results = shortcut.complete_shortcut_design(
                recovery_LK_D=data.get('recovery_LK', 0.95),
                recovery_HK_B=data.get('recovery_HK', 0.95),
                R_factor=data.get('reflux_factor', 1.3),
                q=data.get('feed_quality', 1.0),
                efficiency=data.get('efficiency', 0.70)
            )
            
            session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
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
            
            cache_manager.set(cache_key, response_data, timeout=3600)
            logger.info(f"Simulation completee: {session_id}")
            return jsonify({'success': True, 'from_cache': False, 'results': response_data})
            
        except Exception as e:
            logger.error(f"Erreur simulation: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'version': '2.0.0'})
    
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connecte")
        emit('connected', {'message': 'Connexion etablie'})
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app('development')
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
