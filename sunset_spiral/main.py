import math
import sys
import pygame
from typing import Tuple, List

# Constants
WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 700
BACKGROUND_COLOR = (30, 30, 30)

# Mouse interaction constants
MOUSE_INFLUENCE_RADIUS = 150
MOUSE_RIPPLE_DURATION = 30  # frames
CLICK_EFFECT_DURATION = 60  # frames
DRAG_SENSITIVITY = 0.003

# Temperature simulation parameters
class TemperatureConfig:
    ANNUAL_AVERAGE = 2.5
    AMPLITUDE = 22.5
    DAILY_VARIATION = 3
    TEMP_RANGE = (-20, 25)  # Temperature range

class DNAConfig:
    POINTS_COUNT = 900
    BASE_RADIUS = 320
    RADIUS_VARIATION = 200
    BASE_WIDTH = 140
    WIDTH_VARIATION = 60
    LIGHT_DIR = (0.3, -0.7, 0.6)
    
    # Mouse interaction parameters
    MOUSE_DISTORTION_STRENGTH = 0.3
    CLICK_EXPANSION_FACTOR = 1.5
    ROTATION_SPEED = 0.8

def get_body_temp(t: float) -> float:
    """
    Simulate perceived temperature changes in Inner Mongolia over a year
    
    Args:
        t: Time parameter
        
    Returns:
        Simulated temperature value (°C)
    """
    # Calculate day of year (0-364)
    day_of_year = (t * 0.05) % 365
    
    # Seasonal temperature variation (sine wave simulation)
    # Minimum at day 0 (mid-winter), maximum at day 180 (mid-summer)
    seasonal_temp = (TemperatureConfig.ANNUAL_AVERAGE + 
                    TemperatureConfig.AMPLITUDE * 
                    math.sin((day_of_year - 30) / 365 * 2 * math.pi))
    
    # Add daily variation (simulate day/night temperature difference)
    hour = (t * 1.2) % 24
    daily_variation = (TemperatureConfig.DAILY_VARIATION * 
                      math.sin((hour - 6) / 24 * 2 * math.pi))
    
    return seasonal_temp + daily_variation

def temp_to_color(temp: float) -> Tuple[int, int, int]:
    """
    Map temperature value to color (blue to red gradient)
    
    Args:
        temp: Temperature value
        
    Returns:
        RGB color tuple
    """
    min_temp, max_temp = TemperatureConfig.TEMP_RANGE
    # Normalize temperature to [0,1] range
    normalized_temp = (temp - min_temp) / (max_temp - min_temp)
    normalized_temp = max(0.0, min(1.0, normalized_temp))
    
    # Color mapping: cold (blue) to warm (red)
    red = int(5 + 175 * normalized_temp)
    green = int(10 + 45 * normalized_temp)  # Adjust green component for smoother transition
    blue = int(100 + 55 * (1 - normalized_temp))
    
    return (red, green, blue)

def calculate_mobius_point(theta: float, wfrac: float, radius: float, width: float) -> Tuple[float, float, float]:
    """
    Calculate point coordinates on Möbius strip
    
    Args:
        theta: Angle parameter
        wfrac: Width parameter
        radius: Base radius
        width: Band width
        
    Returns:
        3D coordinates (x, y, z)
    """
    cos_theta_2 = math.cos(theta / 2)
    sin_theta_2 = math.sin(theta / 2)
    
    x = (radius + width * wfrac * cos_theta_2) * math.cos(theta)
    y = (radius + width * wfrac * cos_theta_2) * math.sin(theta)
    z = width * wfrac * sin_theta_2
    
    return x, y, z

def project_3d_to_2d(x: float, y: float, z: float) -> Tuple[float, float]:
    """
    Project 3D coordinates to 2D screen coordinates
    
    Args:
        x, y, z: 3D coordinates
        
    Returns:
        Screen coordinates (x, y)
    """
    persp = 0.86 + 0.0015 * z
    screen_x = CENTER[0] + x * persp
    screen_y = CENTER[1] + y * persp - 0.7 * z
    
    return screen_x, screen_y

def calculate_lighting_intensity(theta: float, light_dir: Tuple[float, float, float]) -> float:
    """
    Calculate lighting intensity
    
    Args:
        theta: Angle parameter
        light_dir: Lighting direction vector
        
    Returns:
        Lighting intensity coefficient
    """
    nx = math.cos(theta / 2) * math.cos(theta)
    ny = math.cos(theta / 2) * math.sin(theta)
    nz = math.sin(theta / 2)
    
    dot_product = nx * light_dir[0] + ny * light_dir[1] + nz * light_dir[2]
    return max(0.6, dot_product)

def blend_colors(color1: Tuple[int, int, int], color2: Tuple[int, int, int], 
                blend_factor: float) -> Tuple[int, int, int]:
    """
    Blend two colors
    
    Args:
        color1, color2: Colors to blend
        blend_factor: Blend coefficient (0-1)
        
    Returns:
        Blended color
    """
    return tuple(int(color1[i] * (1 - blend_factor) + color2[i] * blend_factor) 
                for i in range(3))

class MouseEffect:
    """Manage mouse interaction effects"""
    
    def __init__(self):
        self.position = (0, 0)
        self.click_effects = []  # Store click effects
        self.is_dragging = False
        self.drag_start = (0, 0)
        self.rotation_offset = 0.0
        self.view_offset_x = 0.0
        self.view_offset_y = 0.0
        
    def update_position(self, pos: Tuple[int, int]):
        """Update mouse position"""
        self.position = pos
        
    def add_click_effect(self, pos: Tuple[int, int]):
        """Add click effect"""
        self.click_effects.append({
            'pos': pos,
            'time': 0,
            'max_radius': MOUSE_INFLUENCE_RADIUS * 1.2
        })
        
    def start_drag(self, pos: Tuple[int, int]):
        """Start dragging"""
        self.is_dragging = True
        self.drag_start = pos
        
    def end_drag(self):
        """End dragging"""
        self.is_dragging = False
        
    def update_drag(self, pos: Tuple[int, int]):
        """Update drag state"""
        if self.is_dragging:
            dx = pos[0] - self.drag_start[0]
            dy = pos[1] - self.drag_start[1]
            
            # Horizontal drag controls rotation
            self.rotation_offset += dx * DRAG_SENSITIVITY
            
            # Vertical drag controls view offset
            self.view_offset_y += dy * 0.5
            
            self.drag_start = pos
            
    def update_effects(self):
        """Update all effects"""
        # Update click effects
        self.click_effects = [
            effect for effect in self.click_effects 
            if effect['time'] < CLICK_EFFECT_DURATION
        ]
        
        for effect in self.click_effects:
            effect['time'] += 1
            
    def get_mouse_influence(self, point_pos: Tuple[float, float]) -> float:
        """Calculate mouse influence strength on specified point"""
        dx = point_pos[0] - self.position[0]
        dy = point_pos[1] - self.position[1]
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > MOUSE_INFLUENCE_RADIUS:
            return 0.0
            
        # Use smooth decay function
        influence = 1.0 - (distance / MOUSE_INFLUENCE_RADIUS) ** 2
        return max(0.0, influence)
        
    def get_click_influence(self, point_pos: Tuple[float, float]) -> float:
        """Calculate click effect influence on specified point"""
        total_influence = 0.0
        
        for effect in self.click_effects:
            dx = point_pos[0] - effect['pos'][0]
            dy = point_pos[1] - effect['pos'][1]
            distance = math.sqrt(dx * dx + dy * dy)
            
            # Calculate ripple effect
            progress = effect['time'] / CLICK_EFFECT_DURATION
            ripple_radius = effect['max_radius'] * progress
            
            if abs(distance - ripple_radius) < 20:  # ripple width
                ripple_strength = (1.0 - progress) * 0.3
                total_influence += ripple_strength
                
        return min(1.0, total_influence)

def draw_dna_helix(screen: pygame.Surface, t: float, temp: float, mouse_effect: MouseEffect):
    """
    Draw DNA helix structure with mouse interaction
    
    Args:
        screen: Pygame surface object
        t: Time parameter
        temp: Current temperature
        mouse_effect: Mouse interaction effects
    """
    # Calculate dynamic parameters based on temperature and mouse
    temp_factor = (temp + 20) / 45
    mobius_radius = DNAConfig.BASE_RADIUS + DNAConfig.RADIUS_VARIATION * temp_factor
    mobius_width = DNAConfig.BASE_WIDTH + DNAConfig.WIDTH_VARIATION * math.sin(t * 0.7)
    
    # Temperature-dependent colors
    base_color1 = (int(100 + 95 * temp_factor), 150, 255)
    base_color2 = (255, int(50 + 55 * temp_factor), 120)
    
    # Pre-calculate lighting direction
    light_dir = DNAConfig.LIGHT_DIR
    
    # Optimization: reduce repetitive calculations within loops
    points_per_loop = DNAConfig.POINTS_COUNT
    width_steps = 21
    
    for i in range(points_per_loop):
        # 添加鼠标旋转偏移
        theta = 2 * math.pi * i / points_per_loop + mouse_effect.rotation_offset
        
        # Pre-calculate trigonometric values
        cos_theta = math.cos(theta)
        sin_theta = math.sin(theta)
        cos_theta_2 = math.cos(theta / 2)
        sin_theta_2 = math.sin(theta / 2)
        
        # Pre-calculate lighting intensity
        lighting = calculate_lighting_intensity(theta, light_dir)
        
        for j in range(width_steps):
            wfrac = j / (width_steps - 1) - 0.5  # -0.5 to 0.5
            
            # Calculate 3D coordinates
            x, y, z = calculate_mobius_point(theta, wfrac, mobius_radius, mobius_width)
            
            # Project to 2D with mouse view offset
            screen_x, screen_y = project_3d_to_2d(x, y, z)
            screen_x += mouse_effect.view_offset_x
            screen_y += mouse_effect.view_offset_y
            
            # 计算鼠标影响
            mouse_influence = mouse_effect.get_mouse_influence((screen_x, screen_y))
            click_influence = mouse_effect.get_click_influence((screen_x, screen_y))
            
            # 应用鼠标扭曲效果
            if mouse_influence > 0:
                dx = mouse_effect.position[0] - screen_x
                dy = mouse_effect.position[1] - screen_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                if distance > 0:
                    # 吸引效果
                    attraction_force = mouse_influence * DNAConfig.MOUSE_DISTORTION_STRENGTH
                    screen_x += dx * attraction_force * 0.1
                    screen_y += dy * attraction_force * 0.1
            
            # Calculate color blending with mouse effects
            blend = (wfrac + 0.5) * 0.7 + 0.3 * (i / points_per_loop)
            base_color = blend_colors(base_color1, base_color2, blend)
            
            # 添加鼠标颜色影响
            if mouse_influence > 0.1:
                # 鼠标附近的点变得更亮
                brightness_boost = 1.0 + mouse_influence * 0.5
                base_color = tuple(min(255, int(c * brightness_boost)) for c in base_color)
            
            # Add click effect color changes
            if click_influence > 0:
                # Click ripple makes color tend to white
                white_blend = click_influence * 0.4
                base_color = blend_colors(base_color, (255, 255, 255), white_blend)
            
            # Apply lighting
            final_color = tuple(int(c * lighting) for c in base_color)
            
            # 动态点大小 - 鼠标影响下点变大
            point_size = 2 + int(mouse_influence * 3) + int(click_influence * 2)
            
            # Draw point
            pygame.draw.circle(screen, final_color, (int(screen_x), int(screen_y)), point_size)

class DNAVisualizer:
    """Main DNA visualization class with mouse interaction"""
    
    def __init__(self):
        self.screen = None
        self.clock = None
        self.running = False
        self.time = 0.0
        self.mouse_effect = MouseEffect()
        self.show_help = True
        self.help_fade_timer = 300  # 显示帮助文本的时间
        
    def initialize(self):
        """Initialize Pygame and window"""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('Sunset Spiral - Interactive DNA Art')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.running = True
        
    def handle_events(self):
        """Handle Pygame events including mouse interaction"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_h or event.key == pygame.K_F1:
                    # 切换帮助显示
                    self.show_help = not self.show_help
                elif event.key == pygame.K_r:
                    # 重置视图
                    self.mouse_effect.rotation_offset = 0.0
                    self.mouse_effect.view_offset_x = 0.0
                    self.mouse_effect.view_offset_y = 0.0
                elif event.key == pygame.K_SPACE:
                    # 暂停/继续动画
                    pass  # 可以添加暂停功能
            
            elif event.type == pygame.MOUSEMOTION:
                # 更新鼠标位置
                self.mouse_effect.update_position(event.pos)
                if self.mouse_effect.is_dragging:
                    self.mouse_effect.update_drag(event.pos)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键
                    self.mouse_effect.add_click_effect(event.pos)
                    self.mouse_effect.start_drag(event.pos)
                elif event.button == 3:  # Right click - add ripple effect
                    self.mouse_effect.add_click_effect(event.pos)
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左键释放
                    self.mouse_effect.end_drag()
                    
            elif event.type == pygame.MOUSEWHEEL:
                # 鼠标滚轮控制视图缩放（通过调整半径）
                zoom_factor = 1.1 if event.y > 0 else 0.9
                DNAConfig.BASE_RADIUS = max(100, min(500, int(DNAConfig.BASE_RADIUS * zoom_factor)))
    
    def update(self):
        """Update animation state and mouse effects"""
        self.time += 0.06
        self.mouse_effect.update_effects()
        
        # 减少帮助文本显示时间
        if self.help_fade_timer > 0:
            self.help_fade_timer -= 1
            if self.help_fade_timer == 0:
                self.show_help = False
    
    def render(self):
        """Render current frame with mouse effects"""
        self.screen.fill(BACKGROUND_COLOR)
        temp = get_body_temp(self.time)
        
        # 绘制主要的DNA螺旋结构
        draw_dna_helix(self.screen, self.time, temp, self.mouse_effect)
        
        # 绘制鼠标光标效果
        self.draw_mouse_cursor()
        
        # 绘制点击波纹效果
        self.draw_click_effects()
        
        # 绘制UI信息
        self.draw_ui()
        
        pygame.display.flip()
        
    def draw_mouse_cursor(self):
        """绘制鼠标光标周围的视觉效果"""
        mouse_x, mouse_y = self.mouse_effect.position
        
        # 绘制鼠标影响范围
        if 0 <= mouse_x <= WIDTH and 0 <= mouse_y <= HEIGHT:
            # 外圈 - 影响范围指示
            pygame.draw.circle(self.screen, (50, 50, 255), 
                             (mouse_x, mouse_y), MOUSE_INFLUENCE_RADIUS, 2)
            
            # 内圈 - 鼠标位置
            pulse = int(20 + 10 * math.sin(self.time * 5))
            pygame.draw.circle(self.screen, (255, 255, 255), 
                             (mouse_x, mouse_y), pulse, 2)
                             
    def draw_click_effects(self):
        """Draw click ripple effects"""
        for effect in self.mouse_effect.click_effects:
            progress = effect['time'] / CLICK_EFFECT_DURATION
            radius = int(effect['max_radius'] * progress)
            alpha = max(0, 128 - int(128 * progress))
            
            if alpha > 5 and radius > 0:
                # Draw single subtle ripple
                color = (255, 25, 100)
                pygame.draw.circle(self.screen, color, 
                                 effect['pos'], radius, 1)
                                
    def draw_ui(self):
        """绘制用户界面信息"""
        # 绘制当前状态信息
        temp = get_body_temp(self.time)
        temp_text = f"Temperature: {temp:.1f}°C"
        temp_surface = self.small_font.render(temp_text, True, (200, 200, 200))
        self.screen.blit(temp_surface, (10, 10))
        
            
    def draw_help_text(self, alpha: int):
        """Draw help text"""
        help_lines = [
            "Mouse Controls:",
            "• Move - Influence nearby particles",
            "• Left click - Create ripple effect",
            "• Right click - Single ripple",
            "• Drag - Rotate and move view",
            "• Scroll - Zoom view",
            "Keyboard Controls:",
            "• H/F1 - Toggle help",
            "• R - Reset view",
            "• ESC - Exit"
        ]
        
        # Create semi-transparent background
        help_width = 300
        help_height = len(help_lines) * 22 + 20
        help_bg = pygame.Surface((help_width, help_height))
        help_bg.set_alpha(min(alpha, 180))
        help_bg.fill((20, 20, 20))
        self.screen.blit(help_bg, (WIDTH - help_width - 20, HEIGHT - help_height - 20))
        
        # Draw help text
        for i, line in enumerate(help_lines):
            color = (255, 255, 100) if line.endswith('Controls:') else (200, 200, 200)
            if alpha < 255:
                color = tuple(int(c * alpha / 255) for c in color)
                
            text_surface = self.small_font.render(line, True, color)
            self.screen.blit(text_surface, (WIDTH - help_width - 10, HEIGHT - help_height - 10 + i * 22))
    
    def run(self):
        """Main loop"""
        self.initialize()
        
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.render()
                self.clock.tick(FPS)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        pygame.quit()
        sys.exit()

def main():
    """Main function"""
    visualizer = DNAVisualizer()
    visualizer.run()

if __name__ == '__main__':
    main()