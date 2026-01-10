"""
Module Shortcut Methods - Méthodes simplifiées (Fenske, Underwood, Gilliland, Kirkbride)
"""
import numpy as np
from scipy.optimize import brentq


class ShortcutDistillation:
    """Méthodes simplifiées de dimensionnement"""
    
    def __init__(self, thermo_package, F, z_F, P=101325):
        self.thermo = thermo_package
        self.F = F
        self.z_F = np.array(z_F)
        self.P = P
        self.n_comp = len(z_F)
        self._identify_key_components()
        
    def _identify_key_components(self):
        """Identifie les composés clés (léger et lourd)"""
        T_avg = np.mean([comp.Tb for comp in self.thermo.compounds])
        alpha = self.thermo.relative_volatilities(T_avg, self.P)
        sorted_indices = np.argsort(alpha)[::-1]
        
        threshold = 0.01
        for idx in sorted_indices:
            if self.z_F[idx] > threshold:
                self.LK_idx = idx
                break
        
        for idx in sorted_indices[::-1]:
            if self.z_F[idx] > threshold:
                self.HK_idx = idx
                break
    
    def material_balance(self, recovery_LK_D=0.95, recovery_HK_B=0.95):
        """Calcule les bilans matières globaux"""
        LK_in_feed = self.F * self.z_F[self.LK_idx]
        HK_in_feed = self.F * self.z_F[self.HK_idx]
        
        LK_in_D = recovery_LK_D * LK_in_feed
        LK_in_B = LK_in_feed - LK_in_D
        HK_in_B = recovery_HK_B * HK_in_feed
        HK_in_D = HK_in_feed - HK_in_B
        
        d = np.zeros(self.n_comp)
        b = np.zeros(self.n_comp)
        
        d[self.LK_idx] = LK_in_D
        d[self.HK_idx] = HK_in_D
        b[self.LK_idx] = LK_in_B
        b[self.HK_idx] = HK_in_B
        
        for i in range(self.n_comp):
            if i != self.LK_idx and i != self.HK_idx:
                T_avg = np.mean([comp.Tb for comp in self.thermo.compounds])
                alpha = self.thermo.relative_volatilities(T_avg, self.P)
                
                if alpha[i] > alpha[self.LK_idx]:
                    d[i] = self.F * self.z_F[i]
                    b[i] = 0
                elif alpha[i] < alpha[self.HK_idx]:
                    d[i] = 0
                    b[i] = self.F * self.z_F[i]
                else:
                    ratio = (alpha[i] - alpha[self.HK_idx]) / (alpha[self.LK_idx] - alpha[self.HK_idx])
                    d[i] = ratio * self.F * self.z_F[i]
                    b[i] = (1 - ratio) * self.F * self.z_F[i]
        
        D = np.sum(d)
        B = np.sum(b)
        x_D = d / D
        x_B = b / B
        
        self.D = D
        self.B = B
        self.x_D = x_D
        self.x_B = x_B
        
        return D, B, x_D, x_B
    
    def fenske_equation(self):
        """Calcule le nombre minimum de plateaux (Fenske)"""
        T_top = self.thermo.compounds[self.LK_idx].Tb
        T_bottom = self.thermo.compounds[self.HK_idx].Tb
        T_avg = (T_top + T_bottom) / 2
        
        alpha = self.thermo.relative_volatilities(T_avg, self.P)
        alpha_LK_HK = alpha[self.LK_idx] / alpha[self.HK_idx]
        
        ratio_D = self.x_D[self.LK_idx] / self.x_D[self.HK_idx]
        ratio_B = self.x_B[self.LK_idx] / self.x_B[self.HK_idx]
        
        N_min = np.log(ratio_D / ratio_B) / np.log(alpha_LK_HK)
        
        self.N_min = N_min
        self.alpha_avg = alpha_LK_HK
        
        return N_min, alpha_LK_HK
    
    def underwood_method(self, q=1.0):
        """Calcule le reflux minimum (Underwood)"""
        T_avg = np.mean([comp.Tb for comp in self.thermo.compounds])
        alpha = self.thermo.relative_volatilities(T_avg, self.P)
        
        def equation1(theta):
            return np.sum(alpha * self.z_F / (alpha - theta)) - (1 - q)
        
        alpha_HK = alpha[self.HK_idx]
        alpha_LK = alpha[self.LK_idx]
        
        try:
            theta = brentq(equation1, alpha_HK + 0.01, alpha_LK - 0.01)
        except:
            theta = (alpha_HK + alpha_LK) / 2
        
        R_min_plus_1 = np.sum(alpha * self.x_D / (alpha - theta))
        R_min = max(R_min_plus_1 - 1, 0.5)
        
        self.R_min = R_min
        self.theta = theta
        
        return R_min, theta
    
    def gilliland_correlation(self, R):
        """Calcule le nombre de plateaux (Gilliland)"""
        X = (R - self.R_min) / (R + 1)
        exponent = (1 + 54.4*X) * (X - 1) / ((11 + 117.2*X) * np.sqrt(X + 1e-10))
        Y = 1 - np.exp(exponent)
        N = self.N_min + Y / (1 - Y + 1e-10)
        return N
    
    def kirkbride_equation(self, N_total):
        """Détermine la position du plateau d'alimentation (Kirkbride)"""
        ratio_term = (self.B / self.D) * \
                    (self.z_F[self.HK_idx] / self.z_F[self.LK_idx]) * \
                    (self.x_B[self.LK_idx] / self.x_D[self.HK_idx])**2
        
        log_ratio = 0.206 * np.log(ratio_term + 1e-10)
        N_R_over_N_S = np.exp(log_ratio)
        
        N_S = N_total / (1 + N_R_over_N_S)
        N_R = N_total - N_S
        feed_stage = int(np.ceil(N_R)) + 1
        
        return int(np.ceil(N_R)), int(np.floor(N_S)), feed_stage
    
    def complete_shortcut_design(self, recovery_LK_D=0.95, recovery_HK_B=0.95,
                                 R_factor=1.3, q=1.0, efficiency=0.70):
        """Dimensionnement complet par méthodes simplifiées"""
        
        # 1. Bilans matières
        D, B, x_D, x_B = self.material_balance(recovery_LK_D, recovery_HK_B)
        
        # 2. Fenske
        N_min, alpha_avg = self.fenske_equation()
        
        # 3. Underwood
        R_min, theta = self.underwood_method(q)
        
        # 4. Gilliland
        R = R_factor * R_min
        N_theoretical = self.gilliland_correlation(R)
        
        # 5. Plateaux réels
        N_real = int(np.ceil(N_theoretical / efficiency))
        
        # 6. Kirkbride
        N_R, N_S, feed_stage = self.kirkbride_equation(N_real)
        
        # 7. Débits internes
        L = R * D
        V = L + D
        L_prime = L + self.F * q
        V_prime = V
        
        results = {
            'D': D,
            'B': B,
            'x_D': x_D,
            'x_B': x_B,
            'N_min': N_min,
            'alpha_avg': alpha_avg,
            'R_min': R_min,
            'theta': theta,
            'R': R,
            'N_theoretical': N_theoretical,
            'N_real': N_real,
            'efficiency': efficiency,
            'N_R': N_R,
            'N_S': N_S,
            'feed_stage': feed_stage,
            'L': L,
            'V': V,
            'L_prime': L_prime,
            'V_prime': V_prime,
            'recovery_LK_D': recovery_LK_D,
            'recovery_HK_B': recovery_HK_B
        }
        
        return results