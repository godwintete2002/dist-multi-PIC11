"""
Module Thermodynamics - Calculs thermodynamiques
"""
import numpy as np
from scipy.optimize import fsolve


class ThermodynamicPackage:
    """Package thermodynamique pour calculs d'équilibre et propriétés de mélanges"""
    
    def __init__(self, compounds):
        self.compounds = compounds
        self.n_comp = len(compounds)
        self.compound_names = [c.name for c in compounds]
        
    def K_values(self, T, P, x=None):
        """Calcule tous les coefficients K à T et P"""
        K = np.array([comp.K_value(T, P) for comp in self.compounds])
        return K
    
    def relative_volatilities(self, T, P, ref_index=-1):
        """Calcule les volatilités relatives"""
        K = self.K_values(T, P)
        K_ref = K[ref_index]
        alpha = K / K_ref
        return alpha
    
    def bubble_temperature(self, P, x, T_guess=None, tol=1e-6, max_iter=100):
        """Calcule la température de bulle"""
        x = np.array(x)
        
        if T_guess is None:
            T_guess = np.sum([x[i] * self.compounds[i].Tb for i in range(self.n_comp)])
        
        def equation(T):
            K = self.K_values(T, P)
            return np.sum(K * x) - 1.0
        
        try:
            T_bubble = fsolve(equation, T_guess, full_output=False)[0]
            K = self.K_values(T_bubble, P)
            y = K * x
            y = y / np.sum(y)
            return T_bubble, y
        except:
            return T_guess, x.copy()
    
    def dew_temperature(self, P, y, T_guess=None):
        """Calcule la température de rosée"""
        y = np.array(y)
        
        if T_guess is None:
            T_guess = np.sum([y[i] * self.compounds[i].Tb for i in range(self.n_comp)])
        
        def equation(T):
            K = self.K_values(T, P)
            return np.sum(y / K) - 1.0
        
        try:
            T_dew = fsolve(equation, T_guess, full_output=False)[0]
            K = self.K_values(T_dew, P)
            x = y / K
            x = x / np.sum(x)
            return T_dew, x
        except:
            return T_guess, y.copy()
    
    def mixture_enthalpy_liquid(self, T, x, T_ref=298.15):
        """Calcule l'enthalpie du mélange liquide"""
        H_L = np.sum([x[i] * self.compounds[i].enthalpy_liquid(T, T_ref) 
                     for i in range(self.n_comp)])
        return H_L
    
    def mixture_enthalpy_vapor(self, T, y, T_ref=298.15):
        """Calcule l'enthalpie du mélange vapeur"""
        H_V = np.sum([y[i] * self.compounds[i].enthalpy_vapor(T, T_ref) 
                     for i in range(self.n_comp)])
        return H_V