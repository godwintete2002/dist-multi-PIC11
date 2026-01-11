"""
Point d'entrée avec support des templates HTML et PDF
======================================================
"""
import os
import json
from flask import Flask, jsonify, request, render_template, send_file
from flask_cors import CORS
from datetime import datetime
import logging
from pathlib import Path

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
    logger.warning(f"⚠️ Modules non trouvés: {e}")
    MODULES_AVAILABLE = False

# Importer le générateur PDF
try:
    from app.pdf_generation.report_generator import ReportGenerator
    PDF_AVAILABLE = True
    logger.info("✅ Générateur PDF disponible")
except ImportError as e:
    logger.warning(f"⚠️ Générateur PDF non disponible: {e}")
    PDF_AVAILABLE = False

# Cache en mémoire
MEMORY_CACHE = {}
RESULTS_STORAGE = {}  # Stockage des résultats pour PDF

def create_app():
    """Crée l'application Flask avec templates"""
    
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    app.config['SECRET_KEY'] = 'dev-secret-key'
    CORS(app)
    
    # Créer les dossiers nécessaires
    for folder in ['logs', 'results', 'temp_uploads']:
        Path(folder).mkdir(exist_ok=True)
    
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
            'modules': MODULES_AVAILABLE,
            'pdf': PDF_AVAILABLE
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
            logger.info("⚙️ Initialisation de la simulation...")
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
                'feed_composition': data['feed_composition'],
                'pressure': data['pressure'],
                'results': {
                    'N_min': float(results['N_min']),
                    'N_real': int(results['N_real']),
                    'N_theoretical': float(results.get('N_theoretical', results['N_real'] * results['efficiency'])),
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
                    'efficiency': float(results['efficiency']),
                    'L': float(results.get('L', 0)),
                    'V': float(results.get('V', 0))
                },
                'timestamp': datetime.now().isoformat()
            }
            
            # Stocker pour PDF
            RESULTS_STORAGE[session_id] = response_data
            
            # Sauvegarder sur disque
            results_dir = Path('results') / session_id
            results_dir.mkdir(parents=True, exist_ok=True)
            
            results_file = results_dir / 'results.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
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
    
    @app.route('/api/generate_pdf/<session_id>', methods=['GET'])
    def generate_pdf(session_id):
        """Génère un rapport PDF pour une simulation"""
        if not PDF_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Générateur PDF non disponible. Installer: pip install reportlab matplotlib'
            }), 500
        
        try:
            # Chercher dans le cache mémoire d'abord
            if session_id in RESULTS_STORAGE:
                results = RESULTS_STORAGE[session_id]
                logger.info(f"📄 Résultats trouvés en mémoire pour {session_id}")
            else:
                # Sinon chercher sur disque
                results_file = Path('results') / session_id / 'results.json'
                if not results_file.exists():
                    return jsonify({
                        'success': False,
                        'error': f'Session {session_id} non trouvée'
                    }), 404
                
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                logger.info(f"📄 Résultats chargés depuis disque pour {session_id}")
            
            # Générer le PDF
            pdf_path = Path('results') / session_id / f'rapport_{session_id}.pdf'
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🔄 Génération PDF en cours...")
            generator = ReportGenerator()
            generator.generate_report(results, str(pdf_path))
            
            logger.info(f"✅ PDF généré: {pdf_path}")
            
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name=f'rapport_distillation_{session_id}.pdf',
                mimetype='application/pdf'
            )
        
        except Exception as e:
            logger.error(f"❌ Erreur génération PDF: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }), 500
    
    return app


if __name__ == '__main__':
    print("=" * 80)
    print("🚀 Démarrage de l'application Distillation Multicomposants")
    print("   MODE: Développement avec Interface Web + PDF")
    print("=" * 80)
    
    app = create_app()
    
    port = int(os.getenv('PORT', 5000))
    
    print(f"\n✅ Serveur démarré sur: http://localhost:{port}")
    print(f"🌐 Interface Web: http://localhost:{port}")
    print(f"🏥 Health check: http://localhost:{port}/health")
    print(f"📋 API Composés: http://localhost:{port}/api/compounds")
    print(f"📄 PDF: Activé" if PDF_AVAILABLE else "⚠️  PDF: Non disponible")
    print(f"\n💡 Appuyez sur Ctrl+C pour arrêter\n")
    print("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        use_reloader=True
    )