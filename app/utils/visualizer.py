"""
Module de visualisation - Génération d'images PNG
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif
import matplotlib.pyplot as plt
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SimulationVisualizer:
    """Générateur d'images pour les résultats de simulation"""
    
    def __init__(self, output_dir='results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.colors = ['#3b82f6', '#10b981', '#ef4444', '#f59e0b', '#8b5cf6']
    
    def generate_all_plots(self, results, compounds, session_id):
        """
        Génère tous les graphiques et retourne les chemins
        
        Returns:
        --------
        dict : Chemins des images générées
        """
        plots = {}
        
        try:
            # 1. Bilans matières
            plots['material_balance'] = self.plot_material_balance(
                results, compounds, session_id
            )
            
            # 2. Compositions
            plots['compositions'] = self.plot_compositions(
                results, compounds, session_id
            )
            
            # 3. Résultats détaillés
            plots['detailed_results'] = self.plot_detailed_results(
                results, session_id
            )
            
            # 4. Distribution des composés
            plots['distribution'] = self.plot_distribution(
                results, compounds, session_id
            )
            
            # 5. Diagramme de la colonne
            plots['column_diagram'] = self.plot_column_diagram(
                results, session_id
            )
            
            logger.info(f"✅ {len(plots)} graphiques générés pour {session_id}")
            
        except Exception as e:
            logger.error(f"Erreur génération graphiques: {e}", exc_info=True)
        
        return plots
    
    def plot_material_balance(self, results, compounds, session_id):
        """Graphique des bilans matières"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        streams = ['Alimentation', 'Distillat', 'Résidu']
        flows = [results['feed_flow'], results['results']['D'], results['results']['B']]
        colors = ['#3b82f6', '#10b981', '#ef4444']
        
        bars = ax.bar(streams, flows, color=colors, alpha=0.8, edgecolor='black', linewidth=2)
        
        for bar, flow in zip(bars, flows):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 2,
                   f'{flow:.1f} kmol/h',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_ylabel('Débit (kmol/h)', fontsize=13, fontweight='bold')
        ax.set_title('Bilans Matières - Débits des Flux', 
                    fontsize=15, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax.set_ylim([0, max(flows) * 1.15])
        
        plt.tight_layout()
        
        filename = f'material_balance_{session_id}.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)
    
    def plot_compositions(self, results, compounds, session_id):
        """Graphique des compositions"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(compounds))
        width = 0.35
        
        x_D = [x * 100 for x in results['results']['x_D']]
        x_B = [x * 100 for x in results['results']['x_B']]
        
        bars1 = ax.bar(x - width/2, x_D, width, 
                      label='Distillat', color='#10b981', 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        bars2 = ax.bar(x + width/2, x_B, width, 
                      label='Résidu', color='#ef4444', 
                      alpha=0.8, edgecolor='black', linewidth=1.5)
        
        # Annotations
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{height:.1f}%',
                       ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xlabel('Composé', fontsize=13, fontweight='bold')
        ax.set_ylabel('Fraction Molaire (%)', fontsize=13, fontweight='bold')
        ax.set_title('Compositions Molaires des Produits', 
                    fontsize=15, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(compounds, fontsize=11)
        ax.legend(fontsize=11, loc='upper right')
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        ax.set_ylim([0, 100])
        
        plt.tight_layout()
        
        filename = f'compositions_{session_id}.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)
    
    def plot_detailed_results(self, results, session_id):
        """Tableau détaillé des résultats"""
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')
        
        table_data = [
            ['Paramètre', 'Valeur', 'Unité', 'Méthode'],
            ['Nₘᵢₙ', f"{results['results']['N_min']:.2f}", 'plateaux', 'Fenske (Reflux total)'],
            ['Rₘᵢₙ', f"{results['results']['R_min']:.3f}", '-', 'Underwood'],
            ['θ', f"{results['results']['theta']:.3f}", '-', 'Racine Underwood'],
            ['R opératoire', f"{results['results']['R']:.3f}", '-', 
             f"{results['results']['R']/results['results']['R_min']:.2f}× Rₘᵢₙ"],
            ['N théorique', f"{results['results']['N_min']:.2f}", 'plateaux', 'Gilliland'],
            ['Efficacité', f"{results['results']['efficiency']*100:.0f}", '%', 'Donnée'],
            ['N réel', f"{results['results']['N_real']}", 'plateaux', 'N théo / Efficacité'],
            ['N rectification', f"{results['results']['N_R']}", 'plateaux', 'Kirkbride'],
            ['N épuisement', f"{results['results']['N_S']}", 'plateaux', 'Kirkbride'],
            ['Plateau alim.', f"{results['results']['feed_stage']}", '-', 'Kirkbride'],
            ['Débit distillat', f"{results['results']['D']:.2f}", 'kmol/h', 'Bilan matière'],
            ['Débit résidu', f"{results['results']['B']:.2f}", 'kmol/h', 'Bilan matière'],
            ['αₘₒᵧ (LK/HK)', f"{results['results']['alpha_avg']:.3f}", '-', 'Volatilité relative']
        ]
        
        table = ax.table(cellText=table_data, cellLoc='left', loc='center',
                        colWidths=[0.35, 0.20, 0.15, 0.30])
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.2)
        
        # Style de l'en-tête
        for i in range(4):
            cell = table[(0, i)]
            cell.set_facecolor('#2563eb')
            cell.set_text_props(weight='bold', color='white', fontsize=12)
        
        # Alternance de couleurs
        for i in range(1, len(table_data)):
            for j in range(4):
                cell = table[(i, j)]
                if i % 2 == 0:
                    cell.set_facecolor('#f0f9ff')
                cell.set_text_props(fontsize=10)
                if j == 1:  # Colonne valeur
                    cell.set_text_props(weight='bold')
        
        ax.set_title('Résultats Détaillés du Dimensionnement', 
                    fontsize=16, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        filename = f'detailed_results_{session_id}.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)
    
    def plot_distribution(self, results, compounds, session_id):
        """Distribution des composés entre distillat et résidu"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        feed_flow = results['feed_flow']
        feed_comp = results['feed_composition']
        
        F_values = [feed_flow * fc for fc in feed_comp]
        D_values = [results['results']['D'] * xd for xd in results['results']['x_D']]
        B_values = [results['results']['B'] * xb for xb in results['results']['x_B']]
        
        x = np.arange(len(compounds))
        width = 0.25
        
        bars1 = ax.bar(x - width, F_values, width, label='Alimentation',
                      color='#3b82f6', alpha=0.8, edgecolor='black')
        bars2 = ax.bar(x, D_values, width, label='Distillat',
                      color='#10b981', alpha=0.8, edgecolor='black')
        bars3 = ax.bar(x + width, B_values, width, label='Résidu',
                      color='#ef4444', alpha=0.8, edgecolor='black')
        
        ax.set_xlabel('Composé', fontsize=13, fontweight='bold')
        ax.set_ylabel('Débit (kmol/h)', fontsize=13, fontweight='bold')
        ax.set_title('Distribution des Composés', 
                    fontsize=15, fontweight='bold', pad=20)
        ax.set_xticks(x)
        ax.set_xticklabels(compounds, fontsize=11)
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, axis='y', linestyle='--')
        
        plt.tight_layout()
        
        filename = f'distribution_{session_id}.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)
    
    def plot_column_diagram(self, results, session_id):
        """Diagramme simplifié de la colonne"""
        fig, ax = plt.subplots(figsize=(8, 10))
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1])
        ax.axis('off')
        
        # Corps de la colonne
        from matplotlib.patches import FancyBboxPatch, Rectangle
        
        col_width = 0.3
        col_height = 0.6
        col_x = 0.35
        col_y = 0.2
        
        column = FancyBboxPatch((col_x, col_y), col_width, col_height,
                               boxstyle="round,pad=0.01", 
                               edgecolor='black', facecolor='lightblue',
                               linewidth=3)
        ax.add_patch(column)
        
        # Informations
        info_text = f"""COLONNE DE DISTILLATION

N total = {results['results']['N_real']} plateaux
Reflux = {results['results']['R']:.2f}
N rectif. = {results['results']['N_R']}
N épuisement = {results['results']['N_S']}
Plateau alim. = {results['results']['feed_stage']}

D = {results['results']['D']:.1f} kmol/h
B = {results['results']['B']:.1f} kmol/h"""
        
        ax.text(0.5, 0.5, info_text, fontsize=11, ha='center', va='center',
               family='monospace', fontweight='bold',
               bbox=dict(boxstyle='round', facecolor='white', 
                        edgecolor='black', linewidth=2, alpha=0.9))
        
        ax.set_title('Schéma de la Colonne', fontsize=15, fontweight='bold', pad=20)
        
        plt.tight_layout()
        
        filename = f'column_diagram_{session_id}.png'
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(filepath)