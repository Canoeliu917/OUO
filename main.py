import math
import sys
import pygame
from typing import Tuple, List

# Constants
WIDTH, HEIGHT = 900, 900
CENTER = (WIDTH // 2, HEIGHT // 2)
FPS = 360
BACKGROUND_COLOR = (30, 30, 30)

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

def draw_dna_helix(screen: pygame.Surface, t: float, temp: float):
    """
    Draw DNA helix structure
    
    Args:
        screen: Pygame surface object
        t: Time parameter
        temp: Current temperature
    """
    # Calculate dynamic parameters based on temperature
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
        theta = 2 * math.pi * i / points_per_loop
        
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
            
            # Project to 2D
            screen_x, screen_y = project_3d_to_2d(x, y, z)
            
            # Calculate color blending
            blend = (wfrac + 0.5) * 0.7 + 0.3 * (i / points_per_loop)
            base_color = blend_colors(base_color1, base_color2, blend)
            
            # Apply lighting
            final_color = tuple(int(c * lighting) for c in base_color)
            
            # Draw point
            pygame.draw.circle(screen, final_color, (int(screen_x), int(screen_y)), 2)

class DNAVisualizer:
    """Main DNA visualization class"""
    
    def __init__(self):
        self.screen = None
        self.clock = None
        self.running = False
        self.time = 0.0
        
    def initialize(self):
        """Initialize Pygame and window"""
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption('DNA Temperature Rhythm Art - Optimized')
        self.clock = pygame.time.Clock()
        self.running = True
        
    def handle_events(self):
        """Handle Pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update(self):
        """Update animation state"""
        self.time += 0.06
    
    def render(self):
        """Render current frame"""
        self.screen.fill(BACKGROUND_COLOR)
        temp = get_body_temp(self.time)
        draw_dna_helix(self.screen, self.time, temp)
        pygame.display.flip()
    
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