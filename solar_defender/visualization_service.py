import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Wedge, Rectangle
from io import BytesIO
import base64
from django.core.files.base import ContentFile
from .models import GameSession, Mission

class VisualizationService:
    def __init__(self, session):
        self.session = session
        self.missions = session.missions.all().order_by('phase_number')
        
        # Professional colors
        self.colors = {
            'excellent': '#00ff88',
            'good': '#66ff66',
            'warning': '#ffcc00',
            'danger': '#ff6600',
            'critical': '#ff0044',
            'info': '#00ffff'
        }
        
        plt.style.use('dark_background')
        plt.rcParams['font.size'] = 11
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
    
    def generate_all_charts(self):
        """توليد جميع الرسوم البيانية"""
        charts = {
            'flare_distribution': self.create_flare_distribution(),
            'intensity_timeline': self.create_intensity_timeline(),
            'systems_status': self.create_systems_status(),
            'impact_comparison': self.create_impact_comparison(),
            'performance_gauge': self.create_performance_gauge(),
            'earth_impact_map': self.create_earth_impact_map(),
            'mission_log': self.create_mission_log()
        }
        
        return charts
    
    def create_flare_distribution(self):
        """توزيع التوهجات الشمسية - Pie Chart"""
        flares = [mission.flare for mission in self.missions]
        flare_classes = [flare.flare_class for flare in flares]
        class_counts = pd.Series(flare_classes).value_counts()
        
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#0a0a0a')
        
        colors_map = {
            'A': '#00ff88', 'B': '#66ff66', 'C': '#ffcc00',
            'M': '#ff6600', 'X': '#ff0044'
        }
        colors = [colors_map.get(c, '#ffffff') for c in class_counts.index]
        
        wedges, texts, autotexts = ax.pie(
            class_counts.values,
            labels=class_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            textprops={'color': 'white', 'fontsize': 12, 'weight': 'bold'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2.5}
        )
        
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(11)
            autotext.set_weight('bold')
        
        ax.set_title('Solar Flare Distribution',
                    color='#00ffff', fontsize=13, pad=15, weight='bold')
        
        return self._fig_to_base64(fig)
    
    def create_intensity_timeline(self):
        """الجدول الزمني للشدة"""
        flares = [mission.flare for mission in self.missions]
        intensities = [flare.intensity for flare in flares]
        times = range(len(intensities))
        classes = [flare.class_type for flare in flares]
        
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='#0a0a0a')
        
        ax.plot(times, intensities, color='#00ffff', linewidth=3, alpha=0.7, zorder=2)
        ax.fill_between(times, intensities, alpha=0.3, color='#00ffff', zorder=1)
        
        color_map = {
            'A': '#00ff88', 'B': '#66ff66', 'C': '#ffcc00',
            'M': '#ff6600', 'X': '#ff0044'
        }
        
        for t, intensity, flare_class in zip(times, intensities, classes):
            color = color_map.get(flare_class[0], '#ffffff')
            size = intensity * 100 + 150
            ax.scatter(t, intensity, c=color, s=size, alpha=0.9,
                      edgecolors='white', linewidths=2.5, zorder=3)
            
            ax.annotate(flare_class, (t, intensity),
                       xytext=(0, 12), textcoords='offset points',
                       ha='center', fontsize=10, color='white', weight='bold',
                       bbox=dict(boxstyle='round,pad=0.5',
                                facecolor=color, alpha=0.8,
                                edgecolor='white', linewidth=1.5))
        
        ax.set_title('Flare Intensity Timeline',
                    color='#00ffff', fontsize=13, weight='bold')
        ax.set_ylabel('Intensity', color='white', fontsize=11)
        ax.set_xlabel('Flare Sequence', color='white', fontsize=11)
        ax.grid(True, alpha=0.3, color='#00ffff', linestyle=':', linewidth=1)
        ax.tick_params(colors='white')
        ax.set_facecolor('#0a0a0a')
        
        return self._fig_to_base64(fig)
    
    def create_systems_status(self):
        """حالة أنظمة الأرض"""
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#0a0a0a')
        
        systems = ['Power', 'Satellites', 'Communications']
        values = [
            self.session.power_grid,
            self.session.satellites,
            self.session.communications
        ]
        
        colors = []
        for v in values:
            if v >= 75:
                colors.append('#00ff88')
            elif v >= 50:
                colors.append('#ffcc00')
            elif v >= 25:
                colors.append('#ff6600')
            else:
                colors.append('#ff0044')
        
        bars = ax.barh(systems, values, color=colors, alpha=0.85,
                      edgecolor='white', linewidth=2.5)
        
        for bar, value in zip(bars, values):
            ax.text(value + 2, bar.get_y() + bar.get_height()/2,
                   f'{value}%', va='center', fontsize=12,
                   fontweight='bold', color='white')
        
        ax.set_xlim(0, 110)
        ax.set_title('Earth Systems Status',
                    color='#00ffff', fontsize=13, pad=10, weight='bold')
        ax.grid(True, alpha=0.2, axis='x', color='#00ffff', linestyle=':')
        ax.tick_params(colors='white')
        ax.set_facecolor('#0a0a0a')
        
        return self._fig_to_base64(fig)
    
    def create_impact_comparison(self):
        """مقارنة التأثيرات"""
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#0a0a0a')
        
        flare_impacts = []
        flare_labels = []
        flare_colors = []
        
        color_map = {
            'A': '#00ff88', 'B': '#66ff66', 'C': '#ffcc00',
            'M': '#ff6600', 'X': '#ff0044'
        }
        
        for mission in self.missions[:5]:
            impact = mission.flare.calculate_impact()
            total_impact = impact['power'] + impact['satellites'] + impact['comm']
            flare_impacts.append(total_impact)
            flare_labels.append(mission.flare.class_type)
            flare_colors.append(color_map.get(mission.flare.flare_class, '#ffffff'))
        
        bars = ax.bar(flare_labels, flare_impacts, color=flare_colors,
                     alpha=0.85, edgecolor='white', linewidth=2.5)
        
        for bar, impact in zip(bars, flare_impacts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 3,
                   str(impact), ha='center', va='bottom',
                   fontsize=11, fontweight='bold', color='white')
        
        ax.set_title('Flare Impact Comparison',
                    color='#00ffff', fontsize=13, pad=10, weight='bold')
        ax.set_ylabel('Total Impact', color='white', fontsize=11)
        ax.grid(True, alpha=0.2, axis='y', color='#00ffff', linestyle=':')
        ax.tick_params(colors='white')
        ax.set_facecolor('#0a0a0a')
        
        return self._fig_to_base64(fig)
    
    def create_performance_gauge(self):
        """مقياس الأداء"""
        fig, ax = plt.subplots(figsize=(6, 6), facecolor='#0a0a0a')
        
        max_score = self.missions.count() * 25
        performance = (self.session.score / max_score * 100) if max_score > 0 else 0
        
        circle_bg = Circle((0.5, 0.5), 0.4, color='#1a1a1a', transform=ax.transAxes)
        ax.add_patch(circle_bg)
        
        theta1 = 180
        theta2 = 180 - (performance * 1.8)
        
        if performance >= 75:
            color = '#00ff88'
            status = 'Excellent'
        elif performance >= 50:
            color = '#ffcc00'
            status = 'Good'
        elif performance >= 25:
            color = '#ff6600'
            status = 'Fair'
        else:
            color = '#ff0044'
            status = 'Poor'
        
        wedge = Wedge((0.5, 0.5), 0.4, theta2, theta1,
                     transform=ax.transAxes, color=color, alpha=0.8)
        ax.add_patch(wedge)
        
        ax.text(0.5, 0.55, f'{performance:.0f}%',
               transform=ax.transAxes, ha='center', va='center',
               fontsize=36, fontweight='bold', color=color)
        ax.text(0.5, 0.42, status,
               transform=ax.transAxes, ha='center', va='center',
               fontsize=14, color='white', weight='bold')
        
        ax.set_title('Performance Gauge',
                    color='#00ffff', fontsize=13, pad=10, weight='bold')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        return self._fig_to_base64(fig)
    
    def create_earth_impact_map(self):
        """خريطة تأثير الأرض"""
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='#0a0a0a')
        
        theta = np.linspace(0, 2*np.pi, 100)
        x_earth = np.cos(theta)
        y_earth = np.sin(theta)
        
        ax.fill(x_earth, y_earth, color='#1a4d80', alpha=0.9, zorder=1)
        ax.plot(x_earth, y_earth, color='#00ffff', linewidth=4, zorder=2)
        
        for lat in np.linspace(-0.8, 0.8, 5):
            x_lat = np.cos(theta) * np.sqrt(max(0, 1 - lat**2))
            y_lat = np.ones_like(theta) * lat
            ax.plot(x_lat, y_lat, color='#00ffff', alpha=0.3, linewidth=1.5)
        
        dangerous_flares = [m.flare for m in self.missions if m.flare.flare_class in ['M', 'X']]
        
        if dangerous_flares:
            for i, radius in enumerate([1.15, 1.3, 1.45]):
                alpha = 0.5 - i*0.1
                color = '#ff0044' if any(f.flare_class == 'X' for f in dangerous_flares) else '#ff6600'
                circle = Circle((0, 0), radius, fill=False,
                              edgecolor=color, linewidth=3,
                              linestyle='--', alpha=alpha, zorder=3)
                ax.add_patch(circle)
            
            aurora_theta = np.linspace(np.pi/6, 5*np.pi/6, 50)
            for pole in [1, -1]:
                x_aurora = 1.2 * np.cos(aurora_theta)
                y_aurora = pole * 1.2 * np.abs(np.sin(aurora_theta))
                ax.plot(x_aurora, y_aurora, color='#00ff88',
                       linewidth=4, alpha=0.8, zorder=4)
        
        ax.text(0, 0, 'EARTH', ha='center', va='center',
               fontsize=20, color='white', weight='bold',
               bbox=dict(boxstyle='round,pad=1',
                        facecolor='#0a0a0a', alpha=0.8,
                        edgecolor='#00ffff', linewidth=3))
        
        ax.set_title('Planetary Impact Map',
                    color='#00ffff', fontsize=13, pad=10, weight='bold')
        ax.set_xlim(-1.8, 1.8)
        ax.set_ylim(-1.8, 1.8)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_facecolor('#0a0a0a')
        
        return self._fig_to_base64(fig)
    
    def create_mission_log(self):
        """سجل المهمات"""
        fig, ax = plt.subplots(figsize=(8, 6), facecolor='#0a0a0a')
        ax.axis('off')
        ax.set_title('Mission Log',
                    color='#00ffff', fontsize=13, pad=10, weight='bold')
        
        y_pos = 0.9
        strategy_names = {
            1: "Satellite Shields",
            2: "Grid Protection",
            3: "Comm Boost",
            4: "Integrated Defense"
        }
        
        for mission in self.missions[:5]:
            status = "✅" if mission.success else "⚠️"
            strategy = strategy_names.get(mission.defense_choice, "?")
            text = f"{status} {mission.flare.class_type}: {strategy}"
            
            ax.text(0.1, y_pos, text, transform=ax.transAxes,
                   fontsize=11, color='white', weight='bold',
                   bbox=dict(boxstyle='round,pad=0.5',
                            facecolor='#1a1a1a', alpha=0.8,
                            edgecolor='#00ffff', linewidth=1))
            y_pos -= 0.18
        
        ax.set_facecolor('#0a0a0a')
        
        return self._fig_to_base64(fig)
    
    def _fig_to_base64(self, fig):
        """تحويل Figure إلى Base64"""
        buffer = BytesIO()
        fig.savefig(buffer, format='png', dpi=150, facecolor='#0a0a0a', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        return f"data:image/png;base64,{image_base64}"