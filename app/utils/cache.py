"""
Gestion du cache Redis
=======================
Système de cache pour améliorer les performances
"""
import redis
import json
import hashlib
import logging
from typing import Any, Optional, Dict
from functools import wraps

logger = logging.getLogger('distillation_app')


class CacheManager:
    """Gestionnaire de cache avec Redis"""
    
    def __init__(self, redis_url: str = 'redis://localhost:6379/0', 
                 prefix: str = 'distillation'):
        """
        Initialise le gestionnaire de cache
        
        Parameters:
        -----------
        redis_url : str
            URL de connexion Redis
        prefix : str
            Préfixe pour les clés
        """
        self.prefix = prefix
        self.redis_url = redis_url
        
        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test de connexion
            self.client.ping()
            self.available = True
            logger.info(f"✅ Redis connecté: {redis_url}")
        
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"⚠️  Redis non disponible: {e}")
            self.client = None
            self.available = False
    
    def _make_key(self, key: str) -> str:
        """Crée une clé complète avec préfixe"""
        return f"{self.prefix}:{key}"
    
    def generate_key(self, operation: str, data: Dict) -> str:
        """
        Génère une clé unique basée sur les données
        
        Parameters:
        -----------
        operation : str
            Nom de l'opération (ex: 'simulation')
        data : dict
            Données à hasher
        
        Returns:
        --------
        str : Clé unique
        """
        # Sérialiser les données de manière déterministe
        json_str = json.dumps(data, sort_keys=True)
        
        # Créer un hash
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()[:16]  # 16 premiers caractères
        
        return f"{operation}:{hash_hex}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Récupère une valeur du cache
        
        Parameters:
        -----------
        key : str
            Clé de cache
        
        Returns:
        --------
        Any : Valeur du cache ou None
        """
        if not self.available:
            return None
        
        try:
            full_key = self._make_key(key)
            value = self.client.get(full_key)
            
            if value is not None:
                logger.debug(f"🎯 Cache HIT: {key}")
                return json.loads(value)
            else:
                logger.debug(f"❌ Cache MISS: {key}")
                return None
        
        except Exception as e:
            logger.error(f"Erreur lecture cache: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: int = 3600) -> bool:
        """
        Stocke une valeur dans le cache
        
        Parameters:
        -----------
        key : str
            Clé de cache
        value : Any
            Valeur à stocker (sera sérialisée en JSON)
        timeout : int
            Durée de vie en secondes (défaut: 1 heure)
        
        Returns:
        --------
        bool : True si succès
        """
        if not self.available:
            return False
        
        try:
            full_key = self._make_key(key)
            json_value = json.dumps(value)
            self.client.setex(full_key, timeout, json_value)
            logger.debug(f"💾 Cache SET: {key} (TTL: {timeout}s)")
            return True
        
        except Exception as e:
            logger.error(f"Erreur écriture cache: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Supprime une valeur du cache
        
        Parameters:
        -----------
        key : str
            Clé à supprimer
        
        Returns:
        --------
        bool : True si supprimé
        """
        if not self.available:
            return False
        
        try:
            full_key = self._make_key(key)
            deleted = self.client.delete(full_key)
            logger.debug(f"🗑️  Cache DELETE: {key}")
            return deleted > 0
        
        except Exception as e:
            logger.error(f"Erreur suppression cache: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Supprime toutes les clés correspondant au pattern
        
        Parameters:
        -----------
        pattern : str
            Pattern de clés (ex: 'simulation:*')
        
        Returns:
        --------
        int : Nombre de clés supprimées
        """
        if not self.available:
            return 0
        
        try:
            full_pattern = self._make_key(pattern)
            keys = self.client.keys(full_pattern)
            
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"🗑️  Cache CLEAR: {deleted} clés supprimées ({pattern})")
                return deleted
            
            return 0
        
        except Exception as e:
            logger.error(f"Erreur nettoyage cache: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du cache
        
        Returns:
        --------
        dict : Statistiques
        """
        if not self.available:
            return {'available': False}
        
        try:
            info = self.client.info('stats')
            memory = self.client.info('memory')
            
            return {
                'available': True,
                'keys': self.client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'memory_used': memory.get('used_memory_human', 'N/A'),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        
        except Exception as e:
            logger.error(f"Erreur stats cache: {e}")
            return {'available': False, 'error': str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calcule le taux de réussite du cache"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    def health_check(self) -> bool:
        """Vérifie la santé de Redis"""
        if not self.available:
            return False
        
        try:
            return self.client.ping()
        except:
            return False


def cached(key_prefix: str, timeout: int = 3600):
    """
    Décorateur pour mettre en cache les résultats de fonction
    
    Parameters:
    -----------
    key_prefix : str
        Préfixe de la clé de cache
    timeout : int
        Durée de vie en secondes
    
    Usage:
    ------
    @cached('my_function', timeout=1800)
    def my_function(arg1, arg2):
        # Opération coûteuse
        return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Importer ici pour éviter les imports circulaires
            from flask import current_app
            
            if not hasattr(current_app, 'cache_manager'):
                return func(*args, **kwargs)
            
            cache_manager = current_app.cache_manager
            
            # Générer une clé unique
            cache_key = f"{key_prefix}:{func.__name__}:{hash((args, frozenset(kwargs.items())))}"
            
            # Essayer de récupérer du cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Fonction {func.__name__} servie depuis le cache")
                return cached_result
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Mettre en cache
            cache_manager.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    
    return decorator


class CacheFallback:
    """Cache de secours en mémoire si Redis n'est pas disponible"""
    
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self._update_access(key)
            return self.cache[key]['value']
        return None
    
    def set(self, key: str, value: Any, timeout: int = 3600):
        if len(self.cache) >= self.max_size:
            # Supprimer l'élément le moins récemment utilisé
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
        
        self.cache[key] = {'value': value, 'timeout': timeout}
        self._update_access(key)
    
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
    
    def _update_access(self, key: str):
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
    
    def clear(self):
        self.cache.clear()
        self.access_order.clear()


# Exemple d'utilisation
if __name__ == '__main__':
    # Test du cache
    cache = CacheManager('redis://localhost:6379/0')
    
    # Set
    cache.set('test_key', {'data': 'test'}, timeout=60)
    
    # Get
    result = cache.get('test_key')
    print(f"Résultat: {result}")
    
    # Stats
    stats = cache.get_stats()
    print(f"Stats: {stats}")
    
    # Health check
    healthy = cache.health_check()
    print(f"Redis healthy: {healthy}")