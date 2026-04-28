"""
Модуль для расчётов аэродинамических параметров модели самолёта
"""
import math

class AerodynamicsCalculator:
    """
    Класс для расчёта аэродинамических характеристик модели самолёта
    """
    
    # Константы
    AIR_DENSITY = 1.225  # кг/м³ при 15°C на уровне моря
    GRAVITY = 9.81  # м/с²
    
    def __init__(self, wing_area, mass, wingspan):
        """
        Инициализация калькулятора
        
        Args:
            wing_area: Площадь крыла (м²)
            mass: Масса самолёта (кг)
            wingspan: Размах крыльев (м)
        """
        self.wing_area = wing_area
        self.mass = mass
        self.wingspan = wingspan
        self.aspect_ratio = (wingspan ** 2) / wing_area
    
    def calculate_lift_coefficient(self, angle_of_attack):
        """
        Расчёт коэффициента подъёмной силы
        
        Args:
            angle_of_attack: Угол атаки (градусы)
            
        Returns:
            float: Коэффициент подъёмной силы (CL)
        """
        angle_rad = math.radians(angle_of_attack)
        # Упрощённая модель
        cl = 1.1 * math.sin(angle_rad) * math.cos(angle_rad)
        return max(0, cl)
    
    def calculate_drag_coefficient(self, cl):
        """
        Расчёт коэффициента сопротивления (полярная диаграмма)
        
        Args:
            cl: Коэффициент подъёмной силы
            
        Returns:
            float: Коэффициент сопротивления (CD)
        """
        cd0 = 0.025  # Коэффициент нулевого сопротивления
        cd_induced = (cl ** 2) / (math.pi * self.aspect_ratio * 0.95)
        return cd0 + cd_induced
    
    def calculate_lift(self, velocity, cl):
        """
        Расчёт подъёмной силы
        
        Args:
            velocity: Скорость (м/с)
            cl: Коэффициент подъёмной силы
            
        Returns:
            float: Подъёмная сила (Н)
        """
        dynamic_pressure = 0.5 * self.AIR_DENSITY * (velocity ** 2)
        lift = dynamic_pressure * self.wing_area * cl
        return lift
    
    def calculate_drag(self, velocity, cd):
        """
        Расчёт силы сопротивления
        
        Args:
            velocity: Скорость (м/с)
            cd: Коэффициент сопротивления
            
        Returns:
            float: Сила сопротивления (Н)
        """
        dynamic_pressure = 0.5 * self.AIR_DENSITY * (velocity ** 2)
        drag = dynamic_pressure * self.wing_area * cd
        return drag
    
    def calculate_stall_speed(self, cl_max=1.2):
        """
        Расчёт скорости сваливания
        
        Args:
            cl_max: Максимальный коэффициент подъёмной силы
            
        Returns:
            float: Скорость сваливания (м/с)
        """
        weight = self.mass * self.GRAVITY
        vs = math.sqrt((2 * weight) / (self.AIR_DENSITY * self.wing_area * cl_max))
        return vs
    
    def calculate_max_speed(self, power_available, cd):
        """
        Расчёт максимальной скорости при заданной мощности
        
        Args:
            power_available: Доступная мощность (Вт)
            cd: Коэффициент сопротивления
            
        Returns:
            float: Максимальная скорость (м/с)
        """
        # V_max = (2 * P / (ρ * S * CD))^(1/3)
        v_max = ((2 * power_available) / (self.AIR_DENSITY * self.wing_area * cd)) ** (1/3)
        return v_max
    
    def calculate_glide_ratio(self, cl, cd):
        """
        Расчёт качества планирования
        
        Args:
            cl: Коэффициент подъёмной силы
            cd: Коэффициент сопротивления
            
        Returns:
            float: Качество планирования (L/D)
        """
        if cd == 0:
            return 0
        return cl / cd
    
    def calculate_turn_radius(self, velocity, load_factor):
        """
        Расчёт радиуса виража
        
        Args:
            velocity: Скорость (м/с)
            load_factor: Коэффициент нагрузки (G)
            
        Returns:
            float: Радиус виража (м)
        """
        g_turn = (load_factor - 1) * self.GRAVITY
        if g_turn <= 0:
            return float('inf')
        radius = (velocity ** 2) / g_turn
        return radius
    
    def calculate_climb_rate(self, excess_power):
        """
        Расчёт вертикальной скорости (скороподъёмность)
        
        Args:
            excess_power: Избыточная мощность (Вт)
            
        Returns:
            float: Скороподъёмность (м/с)
        """
        weight = self.mass * self.GRAVITY
        climb_rate = excess_power / weight
        return climb_rate
    
    def full_analysis(self, velocity, angle_of_attack, power_available):
        """
        Полный анализ аэродинамических характеристик
        
        Args:
            velocity: Скорость (м/с)
            angle_of_attack: Угол атаки (градусы)
            power_available: Доступная мощность (Вт)
            
        Returns:
            dict: Словарь с результатами расчётов
        """
        cl = self.calculate_lift_coefficient(angle_of_attack)
        cd = self.calculate_drag_coefficient(cl)
        lift = self.calculate_lift(velocity, cl)
        drag = self.calculate_drag(velocity, cd)
        glide_ratio = self.calculate_glide_ratio(cl, cd)
        stall_speed = self.calculate_stall_speed()
        
        return {
            'velocity': velocity,
            'angle_of_attack': angle_of_attack,
            'cl': cl,
            'cd': cd,
            'lift': lift,
            'drag': drag,
            'glide_ratio': glide_ratio,
            'stall_speed': stall_speed,
            'weight': self.mass * self.GRAVITY
        }