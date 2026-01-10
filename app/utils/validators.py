"""
Validateurs pour les données d'entrée
=====================================
Validation robuste des données de simulation
"""
import numpy as np
from typing import Dict, Tuple, List, Any


def validate_input_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valide les données d'entrée de simulation
    
    Parameters:
    -----------
    data : dict
        Données de simulation
    
    Returns:
    --------
    tuple : (is_valid: bool, error_message: str)
    """
    
    # 1. Vérifier les champs obligatoires
    required_fields = ['compounds', 'feed_flow', 'feed_composition', 'pressure']
    for field in required_fields:
        if field not in data:
            return False, f"Champ obligatoire manquant: {field}"
    
    # 2. Valider compounds
    compounds = data['compounds']
    if not isinstance(compounds, list):
        return False, "compounds doit être une liste"
    
    if len(compounds) < 2:
        return False, "Au moins 2 composés requis"
    
    if len(compounds) > 10:
        return False, "Maximum 10 composés supportés"
    
    if len(compounds) != len(set(compounds)):
        return False, "Composés en double détectés"
    
    # 3. Valider feed_flow
    feed_flow = data['feed_flow']
    if not isinstance(feed_flow, (int, float)):
        return False, "feed_flow doit être un nombre"
    
    if feed_flow <= 0:
        return False, "feed_flow doit être positif"
    
    if feed_flow > 10000:
        return False, "feed_flow trop élevé (max 10000 kmol/h)"
    
    # 4. Valider feed_composition
    feed_comp = data['feed_composition']
    if not isinstance(feed_comp, list):
        return False, "feed_composition doit être une liste"
    
    if len(feed_comp) != len(compounds):
        return False, f"feed_composition doit avoir {len(compounds)} éléments"
    
    # Vérifier que toutes les valeurs sont des nombres
    try:
        feed_comp = [float(x) for x in feed_comp]
    except (ValueError, TypeError):
        return False, "feed_composition doit contenir uniquement des nombres"
    
    # Vérifier les valeurs
    if any(x < 0 for x in feed_comp):
        return False, "Les fractions molaires doivent être positives"
    
    if any(x > 1 for x in feed_comp):
        return False, "Les fractions molaires doivent être ≤ 1"
    
    # Vérifier la somme
    total = sum(feed_comp)
    if abs(total - 1.0) > 0.02:
        return False, f"La somme des fractions molaires doit être 1.0 (actuel: {total:.4f})"
    
    # 5. Valider pressure
    pressure = data['pressure']
    if not isinstance(pressure, (int, float)):
        return False, "pressure doit être un nombre"
    
    if pressure < 10000:  # 0.1 bar
        return False, "Pression trop basse (min 0.1 bar = 10 kPa)"
    
    if pressure > 5000000:  # 50 bar
        return False, "Pression trop élevée (max 50 bar)"
    
    # 6. Valider les paramètres optionnels
    if 'reflux_factor' in data:
        R_factor = data['reflux_factor']
        if not isinstance(R_factor, (int, float)):
            return False, "reflux_factor doit être un nombre"
        
        if R_factor < 1.0:
            return False, "reflux_factor doit être ≥ 1.0"
        
        if R_factor > 10.0:
            return False, "reflux_factor trop élevé (max 10.0)"
    
    if 'efficiency' in data:
        eff = data['efficiency']
        if not isinstance(eff, (int, float)):
            return False, "efficiency doit être un nombre"
        
        if eff <= 0 or eff > 1:
            return False, "efficiency doit être entre 0 et 1"
    
    if 'recovery_LK' in data:
        rec = data['recovery_LK']
        if not isinstance(rec, (int, float)):
            return False, "recovery_LK doit être un nombre"
        
        if rec <= 0 or rec > 1:
            return False, "recovery_LK doit être entre 0 et 1"
    
    if 'recovery_HK' in data:
        rec = data['recovery_HK']
        if not isinstance(rec, (int, float)):
            return False, "recovery_HK doit être un nombre"
        
        if rec <= 0 or rec > 1:
            return False, "recovery_HK doit être entre 0 et 1"
    
    # ✅ Validation réussie
    return True, ""


def validate_compound_name(name: str) -> Tuple[bool, str]:
    """
    Valide le nom d'un composé
    
    Parameters:
    -----------
    name : str
        Nom du composé
    
    Returns:
    --------
    tuple : (is_valid, error_message)
    """
    if not isinstance(name, str):
        return False, "Le nom doit être une chaîne de caractères"
    
    if not name or name.strip() == "":
        return False, "Le nom ne peut pas être vide"
    
    if len(name) > 100:
        return False, "Le nom est trop long (max 100 caractères)"
    
    # Caractères interdits
    forbidden_chars = ['<', '>', '/', '\\', '|', '?', '*', '"', "'"]
    if any(char in name for char in forbidden_chars):
        return False, f"Caractères interdits détectés: {forbidden_chars}"
    
    return True, ""


def sanitize_compound_names(compounds: List[str]) -> List[str]:
    """
    Nettoie et standardise les noms de composés
    
    Parameters:
    -----------
    compounds : list
        Liste des noms de composés
    
    Returns:
    --------
    list : Noms nettoyés
    """
    cleaned = []
    for name in compounds:
        # Supprimer les espaces
        name = name.strip()
        
        # Mettre en minuscules
        name = name.lower()
        
        # Remplacer les espaces par des underscores
        name = name.replace(' ', '_')
        
        # Supprimer les caractères spéciaux
        name = ''.join(c for c in name if c.isalnum() or c in ['_', '-'])
        
        cleaned.append(name)
    
    return cleaned


def validate_results(results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valide les résultats de simulation
    
    Parameters:
    -----------
    results : dict
        Résultats de simulation
    
    Returns:
    --------
    tuple : (is_valid, error_message)
    """
    required_keys = ['N_min', 'N_real', 'R_min', 'R', 'D', 'B', 'x_D', 'x_B']
    
    for key in required_keys:
        if key not in results:
            return False, f"Clé manquante dans les résultats: {key}"
    
    # Vérifier les valeurs numériques
    if results['N_min'] <= 0:
        return False, "N_min doit être positif"
    
    if results['N_real'] < results['N_min']:
        return False, "N_real doit être ≥ N_min"
    
    if results['R_min'] < 0:
        return False, "R_min doit être positif"
    
    if results['R'] < results['R_min']:
        return False, "R doit être ≥ R_min"
    
    if results['D'] <= 0 or results['B'] <= 0:
        return False, "Les débits D et B doivent être positifs"
    
    # Vérifier les compositions
    if len(results['x_D']) != len(results['x_B']):
        return False, "x_D et x_B doivent avoir la même taille"
    
    if abs(sum(results['x_D']) - 1.0) > 0.01:
        return False, f"Somme de x_D doit être 1.0 (actuel: {sum(results['x_D'])})"
    
    if abs(sum(results['x_B']) - 1.0) > 0.01:
        return False, f"Somme de x_B doit être 1.0 (actuel: {sum(results['x_B'])})"
    
    return True, ""


# Décorateur pour validation automatique
def validate_request(required_fields: List[str]):
    """
    Décorateur pour valider automatiquement les requêtes
    
    Usage:
    ------
    @app.route('/api/endpoint', methods=['POST'])
    @validate_request(['field1', 'field2'])
    def endpoint():
        ...
    """
    from functools import wraps
    from flask import request, jsonify
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Content-Type doit être application/json'
                }), 400
            
            data = request.get_json()
            
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': f'Champ obligatoire manquant: {field}'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator