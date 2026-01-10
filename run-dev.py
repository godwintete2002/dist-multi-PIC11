"""
Point d'entrée avec support des templates HTML
===============================================
"""
import os
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('distillation_app')

# Importer les modules
try:
    from app.core.compound import Compound
    from app.core.thermodynamics import ThermodynamicPackage
    from app.core.shortcut_methods import ShortcutDistillation
    MODULES_AVAILABLE = True
    logger.info("✅ Modules importés avec succès")
except ImportError as e:
    logger.warning(f"⚠️  Modules non trouvés: {e}")
    MODULES_AVAILABLE = False

# Cache en mémoire
MEMORY_CACHE = {}

def create_app():
    """Crée l'application Flask avec templates"""
    
    # Créer l'app avec template_folder
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config['SECRET_KEY'] = 'dev-secret-key'
    CORS(app)
    
    # =========================================================================
    # ROUTES WEB (HTML)
    # =========================================================================
    
    @app.route('/')
    def index():
        """Page d'accueil avec interface de simulation"""
        return render_template('simulation.html')
    
    @app.route('/health')
    def health():
        """Health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'mode': 'development',
            'redis': 'memory',
            'modules': MODULES_AVAILABLE
        })
    
    # =========================================================================
    # API ENDPOINTS (JSON)
    # =========================================================================
    
    @app.route('/api/compounds', methods=['GET'])
    def get_compounds():
        """Liste des composés disponibles"""
        if not MODULES_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Modules non chargés. Installer: pip install thermo chemicals'
            }), 500
        
        try:
            common_compounds = [
                'benzene', 'toluene', 'o-xylene',
                'ethanol', 'methanol', 'acetone',
                'propanol', 'butanol', 'p-xylene', 'm-xylene'
            ]
            
            compounds_data = []
            for name in common_compounds:
                try:
                    comp = Compound(name)
                    compounds_data.append({
                        'name': name,
                        'Tb': round(comp.Tb - 273.15, 2),
                        'Tc': round(comp.Tc - 273.15, 2) if comp.Tc else None,
                        'MW': round(comp.MW, 2)
                    })
                except Exception as e:
                    logger.debug(f"Impossible de charger {name}: {e}")
                    continue
            
            return jsonify({
                'success': True,
                'count': len(compounds_data),
                'compounds': compounds_data
            })
        
        except Exception as e:
            logger.error(f"Erreur get_compounds: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/simulate', methods=['POST'])
    def simulate():
        """Lancer une simulation"""
        if not MODULES_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Modules non chargés'
            }), 500
        
        try:
            data = request.get_json()
            
            # Validation basique
            required = ['compounds', 'feed_flow', 'feed_composition', 'pressure']
            for field in required:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Champ manquant: {field}'
                    }), 400
            
            # Vérifier le cache
            cache_key = str(hash(str(data)))
            if cache_key in MEMORY_CACHE:
                logger.info("✅ Résultat du cache mémoire")
                return jsonify({
                    'success': True,
                    'from_cache': True,
                    'results': MEMORY_CACHE[cache_key]
                })
            
            # Créer les composés
            logger.info(f"📦 Création des composés: {data['compounds']}")
            compounds = [Compound(name) for name in data['compounds']]
            thermo = ThermodynamicPackage(compounds)
            
            # Simulation
            logger.info("⚙️  Initialisation de la simulation...")
            shortcut = ShortcutDistillation(
                thermo,
                data['feed_flow'],
                data['feed_composition'],
                data['pressure']
            )
            
            logger.info("🔄 Exécution du dimensionnement...")
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
                'compounds': data['compounds'],
                'feed_flow': data['feed_flow'],
                'pressure': data['pressure'],
                'results': {
                    'N_min': float(results['N_min']),
                    'N_real': int(results['N_real']),
                    'R_min': float(results['R_min']),
                    'R': float(results['R']),
                    'feed_stage': int(results['feed_stage']),
                    'D': float(results['D']),
                    'B': float(results['B']),
                    'x_D': [float(x) for x in results['x_D']],
                    'x_B': [float(x) for x in results['x_B']],
                    'N_R': int(results['N_R']),
                    'N_S': int(results['N_S']),
                    'alpha_avg': float(results['alpha_avg']),
                    'theta': float(results['theta']),
                    'efficiency': float(results['efficiency'])
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Mettre en cache
            MEMORY_CACHE[cache_key] = response_data
            
            logger.info(f"✅ Simulation complétée: {session_id}")
            
            return jsonify({
                'success': True,
                'from_cache': False,
                'results': response_data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur simulation: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }), 500
    
    return app


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Démarrage de l'application Distillation Multicomposants")
    print("   MODE: Développement avec Interface Web")
    print("=" * 80)
    
    # Créer le dossier templates s'il n'existe pas
    import pathlib
    templates_dir = pathlib.Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Créer les dossiers nécessaires
    for folder in ['logs', 'results', 'temp_uploads']:
        pathlib.Path(folder).mkdir(exist_ok=True)
    
    app = create_app()
    
    port = int(os.getenv('PORT', 5000))
    
    print(f"\n✅ Serveur démarré sur: http://localhost:{port}")
    print(f"🌐 Interface Web: http://localhost:{port}")
    print(f"🔍 Health check: http://localhost:{port}/health")
    print(f"📋 API Composés: http://localhost:{port}/api/compounds")
    print(f"\n💡 Appuyez sur Ctrl+C pour arrêter\n")
    print("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=True
    )