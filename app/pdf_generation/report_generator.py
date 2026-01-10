"""
Générateur de Rapports PDF Amélioré
====================================
Version améliorée avec gestion des erreurs et graphiques intégrés
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether, Frame, PageTemplate
)
from reportlab.pdfgen import canvas
from datetime import datetime
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Générateur de rapports PDF professionnels avec graphiques"""
    
    def __init__(self):
        self.pagesize = A4
        self.width, self.height = self.pagesize
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        self.temp_dir = tempfile.mkdtemp()
    
    def _create_custom_styles(self):
        """Crée des styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=10
        ))
    
    def _create_header_footer(self, canvas_obj, doc):
        """Crée l'en-tête et le pied de page"""
        canvas_obj.saveState()
        
        # En-tête
        canvas_obj.setFont('Helvetica-Bold', 10)
        canvas_obj.setFillColor(colors.HexColor('#1e3a8a'))
        canvas_obj.drawString(
            inch, 
            self.height - 0.5*inch, 
            "Rapport de Simulation - Distillation Multicomposants"
        )
        
        # Ligne
        canvas_obj.setStrokeColor(colors.HexColor('#2563eb'))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(
            inch, 
            self.height - 0.65*inch, 
            self.width - inch, 
            self.height - 0.65*inch
        )
        
        # Pied de page
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.setFillColor(colors.grey)
        canvas_obj.drawString(
            inch, 
            0.5*inch, 
            f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        canvas_obj.drawRightString(
            self.width - inch, 
            0.5*inch, 
            f"Page {canvas_obj.getPageNumber()}"
        )
        canvas_obj.drawCentredString(
            self.width / 2, 
            0.5*inch, 
            "Prof. BAKHER Zine Elabidine - UH1"
        )
        
        canvas_obj.restoreState()
    
    def _create_material_balance_chart(self, results):
        """Crée le graphique de bilan matière"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        streams = ['Alimentation', 'Distillat', 'Résidu']
        flows = [
            results.get('feed_flow', 100),
            results['results']['D'],
            results['results']['B']
        ]
        colors_bars = ['#3b82f6', '#10b981', '#ef4444']
        
        bars = ax.bar(streams, flows, color=colors_bars, alpha=0.8, edgecolor='black', linewidth=2)
        
        for bar, flow in zip(bars, flows):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2., 
                height,
                f'{flow:.1f}\nkmol/h',
                ha='center', 
                va='bottom', 
                fontweight='bold'
            )
        
        ax.set_ylabel('Débit (kmol/h)', fontsize=12, fontweight='bold')
        ax.set_title('Bilans Matières', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        chart_path = os.path.join(self.temp_dir, 'material_balance.png')
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def _create_composition_chart(self, results):
        """Crée le graphique de composition"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        compounds = results.get('compounds', ['Comp 1', 'Comp 2', 'Comp 3'])
        x_D = [x * 100 for x in results['results']['x_D']]
        x_B = [x * 100 for x in results['results']['x_B']]
        
        x = np.arange(len(compounds))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, x_D, width, label='Distillat', 
                       color='#10b981', alpha=0.8, edgecolor='black')
        bars2 = ax.bar(x + width/2, x_B, width, label='Résidu', 
                       color='#ef4444', alpha=0.8, edgecolor='black')
        
        ax.set_xlabel('Composé', fontsize=12, fontweight='bold')
        ax.set_ylabel('Fraction molaire (%)', fontsize=12, fontweight='bold')
        ax.set_title('Compositions des Produits', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(compounds)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        chart_path = os.path.join(self.temp_dir, 'composition.png')
        plt.tight_layout()
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_report(self, results, output_path):
        """
        Génère le rapport PDF complet
        
        Parameters:
        -----------
        results : dict
            Résultats de la simulation
        output_path : str or Path
            Chemin du fichier PDF de sortie
        
        Returns:
        --------
        str : Chemin du fichier généré
        """
        try:
            logger.info("Début génération PDF")
            
            # Créer le document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=self.pagesize,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=1.5*inch,
                bottomMargin=inch
            )
            
            story = []
            
            # ================================================================
            # PAGE DE GARDE
            # ================================================================
            story.append(Spacer(1, 2*inch))
            
            title = Paragraph(
                "RAPPORT DE SIMULATION<br/>DISTILLATION MULTICOMPOSANTS",
                self.styles['CustomTitle']
            )
            story.append(title)
            story.append(Spacer(1, 0.5*inch))
            
            # Informations
            info_data = [
                ['Système:', results.get('system_name', 'BTX')],
                ['Date:', datetime.now().strftime('%d/%m/%Y %H:%M')],
                ['Session ID:', results.get('session_id', 'N/A')],
                ['Méthode:', 'Méthodes Simplifiées']
            ]
            
            info_table = Table(info_data, colWidths=[3*inch, 3*inch])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWHEIGHT', (0, 0), (-1, -1), 30),
            ]))
            
            story.append(info_table)
            story.append(PageBreak())
            
            # ================================================================
            # RÉSUMÉ EXÉCUTIF
            # ================================================================
            story.append(Paragraph("1. RÉSUMÉ EXÉCUTIF", self.styles['CustomHeading2']))
            
            summary = f"""
            Cette simulation a dimensionné une colonne de distillation pour un mélange de 
            {len(results.get('compounds', []))} composés. Le nombre de plateaux réels 
            calculé est de <b>{results['results']['N_real']}</b> avec un reflux opératoire 
            de <b>{results['results']['R']:.3f}</b>.
            """
            story.append(Paragraph(summary, self.styles['CustomBody']))
            story.append(Spacer(1, 0.3*inch))
            
            # Résultats clés
            key_data = [
                ['Paramètre', 'Valeur', 'Unité'],
                ['Plateaux réels', str(results['results']['N_real']), 'plateaux'],
                ['Reflux opératoire', f"{results['results']['R']:.3f}", '-'],
                ['Plateau alimentation', str(results['results']['feed_stage']), '-'],
                ['Débit distillat', f"{results['results']['D']:.2f}", 'kmol/h'],
                ['Débit résidu', f"{results['results']['B']:.2f}", 'kmol/h'],
            ]
            
            key_table = Table(key_data, colWidths=[3*inch, 2*inch, 1.5*inch])
            key_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), 
                 [colors.white, colors.HexColor('#f0f9ff')])
            ]))
            
            story.append(key_table)
            story.append(PageBreak())
            
            # ================================================================
            # BILANS MATIÈRES
            # ================================================================
            story.append(Paragraph("2. BILANS MATIÈRES", self.styles['CustomHeading2']))
            
            # Tableau de bilan
            balance_data = [
                ['Composé', 'Alim. (kmol/h)', 'Dist. (kmol/h)', 'Résidu (kmol/h)', 'Récup. D (%)']
            ]
            
            feed_flow = results.get('feed_flow', 100)
            compounds = results.get('compounds', ['Comp 1', 'Comp 2', 'Comp 3'])
            feed_comp = results.get('feed_composition', [0.33, 0.33, 0.34])
            
            for i, comp in enumerate(compounds):
                F_i = feed_flow * feed_comp[i]
                D_i = results['results']['D'] * results['results']['x_D'][i]
                B_i = results['results']['B'] * results['results']['x_B'][i]
                recovery = (D_i / F_i * 100) if F_i > 0 else 0
                
                balance_data.append([
                    comp,
                    f"{F_i:.2f}",
                    f"{D_i:.2f}",
                    f"{B_i:.2f}",
                    f"{recovery:.1f}"
                ])
            
            # Total
            balance_data.append([
                'TOTAL',
                f"{feed_flow:.2f}",
                f"{results['results']['D']:.2f}",
                f"{results['results']['B']:.2f}",
                '-'
            ])
            
            balance_table = Table(balance_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.2*inch])
            balance_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), 
                 [colors.white, colors.HexColor('#faf5ff')]),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e9d5ff')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ]))
            
            story.append(balance_table)
            story.append(Spacer(1, 0.5*inch))
            
            # Graphique bilan matière
            try:
                chart_path = self._create_material_balance_chart(results)
                img = Image(chart_path, width=5*inch, height=3*inch)
                story.append(img)
            except Exception as e:
                logger.error(f"Erreur création graphique bilan: {e}")
            
            story.append(PageBreak())
            
            # ================================================================
            # COMPOSITIONS
            # ================================================================
            story.append(Paragraph("3. COMPOSITIONS DES PRODUITS", self.styles['CustomHeading2']))
            
            # Graphique composition
            try:
                comp_chart_path = self._create_composition_chart(results)
                img = Image(comp_chart_path, width=5*inch, height=3*inch)
                story.append(img)
            except Exception as e:
                logger.error(f"Erreur création graphique composition: {e}")
            
            story.append(PageBreak())
            
            # ================================================================
            # RÉSULTATS DIMENSIONNEMENT
            # ================================================================
            story.append(Paragraph("4. RÉSULTATS DU DIMENSIONNEMENT", self.styles['CustomHeading2']))
            
            design_text = f"""
            <b>4.1 Équation de Fenske (Reflux Total)</b><br/>
            N<sub>min</sub> = {results['results']['N_min']:.2f} plateaux<br/>
            α<sub>avg</sub> = {results['results'].get('alpha_avg', 2.4):.3f}<br/><br/>
            
            <b>4.2 Méthode d'Underwood (Reflux Minimum)</b><br/>
            R<sub>min</sub> = {results['results']['R_min']:.3f}<br/>
            θ = {results['results'].get('theta', 1.5):.3f}<br/><br/>
            
            <b>4.3 Corrélation de Gilliland</b><br/>
            Avec un facteur de reflux de {results['results']['R'] / results['results']['R_min']:.2f}× R<sub>min</sub>:<br/>
            N<sub>théorique</sub> = {results['results'].get('N_theoretical', 13):.2f} plateaux<br/>
            Efficacité = {results['results'].get('efficiency', 0.7)*100:.0f}%<br/>
            N<sub>réel</sub> = {results['results']['N_real']} plateaux<br/><br/>
            
            <b>4.4 Équation de Kirkbride (Position Alimentation)</b><br/>
            Plateau d'alimentation: {results['results']['feed_stage']}<br/>
            Plateaux rectification: {results['results'].get('N_R', 10)}<br/>
            Plateaux épuisement: {results['results'].get('N_S', 9)}
            """
            
            story.append(Paragraph(design_text, self.styles['CustomBody']))
            story.append(PageBreak())
            
            # ================================================================
            # RECOMMANDATIONS
            # ================================================================
            story.append(Paragraph("5. RECOMMANDATIONS", self.styles['CustomHeading2']))
            
            recommendations = f"""
            <b>5.1 Points d'attention</b><br/>
            • Vérifier les propriétés thermodynamiques des composés<br/>
            • Valider l'efficacité de {results['results'].get('efficiency', 0.7)*100:.0f}%<br/>
            • Effectuer une simulation MESH rigoureuse<br/>
            • Optimiser le reflux pour minimiser les coûts<br/><br/>
            
            <b>5.2 Prochaines étapes</b><br/>
            1. Simulation MESH avec modèles thermodynamiques précis<br/>
            2. Dimensionnement hydraulique (diamètre, hauteur)<br/>
            3. Dimensionnement des équipements auxiliaires<br/>
            4. Analyse économique complète<br/>
            5. Validation avec Aspen Plus ou ProII
            """
            
            story.append(Paragraph(recommendations, self.styles['CustomBody']))
            
            # ================================================================
            # GÉNÉRATION DU PDF
            # ================================================================
            doc.build(
                story, 
                onFirstPage=self._create_header_footer, 
                onLaterPages=self._create_header_footer
            )
            
            logger.info(f"PDF généré avec succès: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}", exc_info=True)
            raise
        
        finally:
            # Nettoyer les fichiers temporaires
            try:
                for file in Path(self.temp_dir).glob('*'):
                    file.unlink()
                Path(self.temp_dir).rmdir()
            except Exception as e:
                logger.warning(f"Erreur nettoyage fichiers temp: {e}")


# Fonction helper pour l'API
def generate_simulation_report(results, output_path):
    """
    Fonction helper pour générer un rapport
    
    Parameters:
    -----------
    results : dict
        Résultats de simulation
    output_path : str or Path
        Chemin de sortie
    
    Returns:
    --------
    str : Chemin du fichier généré
    """
    generator = ReportGenerator()
    return generator.generate_report(results, output_path)