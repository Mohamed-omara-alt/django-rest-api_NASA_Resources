class DefenseCalculator:
    """حساب تأثير استراتيجيات الدفاع"""
    
    @staticmethod
    def calculate_defense_impact(defense_choice, impact, current_systems):
        """
        حساب تأثير الدفاع على الأنظمة
        
        Args:
            defense_choice: رقم الاستراتيجية (1-4)
            impact: تأثير التوهج الشمسي
            current_systems: dict بالقيم الحالية للأنظمة
        
        Returns:
            dict بالقيم الجديدة والنقاط
        """
        power_grid = current_systems.get('power_grid', 100)
        satellites = current_systems.get('satellites', 100)
        communications = current_systems.get('communications', 100)
        
        points_cost = 0
        
        if defense_choice == 1:  # Satellite Shields
            satellites = max(0, min(100, satellites - impact['satellites'] + 15))
            power_grid = max(0, power_grid - impact['power'])
            communications = max(0, communications - impact['comm'])
            points_cost = 10
            
        elif defense_choice == 2:  # Grid Protection
            power_grid = max(0, min(100, power_grid - impact['power'] + 20))
            satellites = max(0, satellites - impact['satellites'])
            communications = max(0, communications - impact['comm'])
            points_cost = 15
            
        elif defense_choice == 3:  # Communications Boost
            communications = max(0, min(100, communications - impact['comm'] + 12))
            power_grid = max(0, power_grid - impact['power'])
            satellites = max(0, satellites - impact['satellites'])
            points_cost = 8
            
        elif defense_choice == 4:  # Integrated Defense
            power_grid = max(0, min(100, power_grid - impact['power'] + 10))
            satellites = max(0, min(100, satellites - impact['satellites'] + 8))
            communications = max(0, min(100, communications - impact['comm'] + 10))
            points_cost = 20
        
        earth_health = (power_grid + satellites + communications) // 3
        
        return {
            'power_grid': power_grid,
            'satellites': satellites,
            'communications': communications,
            'earth_health': earth_health,
            'points_cost': points_cost
        }