import pygame
from blink_detection import Blink_Detector

# Inicializamos pygame
pygame.init()

FPS = 60
WIDTH, HEIGHT = 350, 500
clock = pygame.time.Clock()

ICON = pygame.image.load("imgs/edificio.png")

# Colores
BLUE_DARKED = (7,8,23)
WHITE = (220,220,220)

# Sombra con transparencia (alpha=100)
TRANSPARENT_SHADOW_COLOR = (175,221,227,100)  
TRANSPARENT_SHADOW_COLOR_GAME_OVER = (220,0,0,100)  

# Fuentes
font = pygame.font.Font(None, 70)
font_25 = pygame.font.Font(None, 25)
font_15 = pygame.font.Font(None, 18)

class Floor:
    height = 20
    velocity = 3
    def __init__(self, x, y, width):
        self.x = x
        self.y = y
        self.width = width 
        self.rect = pygame.Rect(self.x, self.y, self.width, Floor.height)
        self.floor_sound = pygame.mixer.Sound("sounds/floor.mp3")
    
    def move(self, screen):
        self.x += Floor.velocity
        if self.x + self.width > screen.get_width() or self.x < 0:
            Floor.velocity *= -1
            self.floor_sound.play()
        self.rect.x = self.x

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect)

    def draw_shadow(self, screen, transparent_color):
        # Crear una superficie para la sombra con transparencia
        shadow_surface = pygame.Surface((self.width, self.y), pygame.SRCALPHA)  # El SRCALPHA habilita la transparencia
        shadow_surface.fill(transparent_color)  # Establecer el color con transparencia

        # Dibujar la sombra sobre el piso
        screen.blit(shadow_surface, (self.x, 0))
    
    def on_screen(self, screen):
        return self.y < screen.get_height()

class Game:
    def __init__(self):
        # Configuracion de la pantalla
        self.screen = pygame.display.set_mode((WIDTH,HEIGHT))
        pygame.display.set_caption("Tower Builder Game")
        pygame.display.set_icon(ICON)

        self.running_game = True
        self.game_over = False
        self.floors = []                # Lista de pisos
        self.current_floor = None       # Piso en movimiento
        self.score = 0                  # Puntuacion
        self.camera_offset = 0          # Desplazamiento vertical de la cámara
        self.camera_limit = HEIGHT//2   # Límite para desplazar la cámara
        self.best_score = self.load_best_score()
        self.new_record_flag = False

        # Creamos el primer piso fijo
        base_floor_width = 300
        base_floor = Floor(self.screen.get_width()//2 - base_floor_width//2, self.screen.get_height() - Floor.height, base_floor_width)
        self.floors.append(base_floor)

        # Creamos el primer piso en movimiento
        self.add_new_moving_floor()

        # Instanciar el detector de parpadeos
        self.blink_control_enable = False
        self.blink_detector = Blink_Detector()

        # Cargar sonidos del juego
        self.success_sound = pygame.mixer.Sound("sounds/success_1.mp3")
        self.game_over_sound = pygame.mixer.Sound("sounds/gameover.mp3")

        # Textos no dinamicos
        self.game_over_text = font_25.render("Game Over!", True, WHITE)
        self.restart_message = font_25.render("Press SPACE to restart", True, WHITE)
        self.new_record_message = font_25.render("New Best! :D", True, WHITE)

    @staticmethod
    def load_best_score():
        try:
            with open("best_score.txt", "r") as file:
                return int(file.read())
        except FileNotFoundError:
            return 0

    def save_best_score(self):
        with open("best_score.txt", "w") as file:
            file.write(str(self.best_score))
    
    def add_new_moving_floor(self):
        # Crear un nuevo piso encima del último piso fijo
        last_floor = self.floors[-1]
        new_floor = Floor(0, last_floor.y - Floor.height, last_floor.width)
        self.current_floor = new_floor

    def update_camera(self):
        # Verificar si el último piso fijo está por encima del límite
        last_floor = self.floors[-1]
        if last_floor.y < self.camera_limit:
            # Calcular el desplazamiento necesario
            offset = self.camera_limit - last_floor.y
            self.camera_offset += offset

            # Desplazar todos los pisos hacia abajo
            for floor in self.floors:
                floor.y += offset
                floor.rect.y = floor.y

            # Desplazar el piso actual en movimiento si existe
            if self.current_floor:
                self.current_floor.y += offset
                self.current_floor.rect.y = self.current_floor.y

        # Eliminar pisos no visibles de la lista
        self.floors = [floor for floor in self.floors if floor.on_screen(self.screen)]
    
    def stop_current_floor(self):
        last_floor = self.floors[-1]
        overlap = max(0, min(self.current_floor.x + self.current_floor.width, last_floor.x + last_floor.width) - max(self.current_floor.x, last_floor.x))
        
        if overlap > 0:
            # Ajustar el ancho y posición del piso actual
            self.current_floor.width = overlap
            self.current_floor.x = max(self.current_floor.x, last_floor.x)
            self.current_floor.rect.width = overlap
            self.current_floor.rect.x = self.current_floor.x

            # Agregar el piso actual a la lista de pisos fijos
            self.floors.append(self.current_floor)

            # Incrementar el puntaje y generar un nuevo piso en movimiento
            self.score += 1
            self.success_sound.play()
            self.add_new_moving_floor()

            # Actualizar la posición de la cámara
            self.update_camera()
        else:
            # Terminar el juego si no hay solapamiento
            self.game_over = True
            self.game_over_sound.play()

            if self.score > self.best_score:
                self.new_record_flag = True
                self.best_score = self.score
                self.save_best_score()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running_game = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running_game = False
                if event.key == pygame.K_SPACE:
                    if self.game_over:
                        self.restart()
                    else:
                        self.stop_current_floor()

                # Tecla para des/habilitar el control por parpadeo
                if event.key == pygame.K_q:
                    self.blink_control_enable = not self.blink_control_enable
            
        if self.blink_control_enable and self.blink_detector.detect_blink():
            if self.game_over:
                self.restart()
            else:
                self.stop_current_floor()

    def restart(self):
        self.game_over = False
        self.floors = []                # Lista de pisos
        self.current_floor = None       # Piso en movimiento
        self.score = 0                  # Puntuacion
        self.new_record_flag = False

        # Creamos el primer piso fijo
        base_floor_width = 300
        base_floor = Floor(self.screen.get_width()//2 - base_floor_width//2, self.screen.get_height() - Floor.height, base_floor_width)
        self.floors.append(base_floor)

        # Creamos el primer piso en movimiento
        self.add_new_moving_floor()

    def update(self):
        # Si el jugador ha perdido no se tiene que actualizar el estado del juego
        if self.game_over:
            return
        
        # Mover el piso actual
        if self.current_floor:
            self.current_floor.move(self.screen)

    def draw(self):
        # Dibujar escenario
        self.screen.fill(BLUE_DARKED)

        # Dibujar todos los pisos fijos
        for floor in self.floors:
            floor.draw(self.screen)

        if self.current_floor:
            self.current_floor.draw(self.screen)
            # Dibujar la sombra del último piso colocado
            if not self.game_over:
                self.floors[-1].draw_shadow(self.screen, TRANSPARENT_SHADOW_COLOR)
            else:
                self.floors[-1].draw_shadow(self.screen, TRANSPARENT_SHADOW_COLOR_GAME_OVER)

        # Escribimos mensaje de game over
        if self.game_over:
            self.screen.blit(self.game_over_text, (self.screen.get_width() // 2 - self.game_over_text.get_width() // 2, 70))
            self.screen.blit(self.restart_message, (self.screen.get_width() // 2 - self.restart_message.get_width() // 2, 95))

            if self.new_record_flag:
                self.screen.blit(self.new_record_message, (self.screen.get_width() // 2 - self.new_record_message.get_width() // 2, 120))
        
        cv_control = font_15.render(f"[Q] Computer Vision - {self.blink_control_enable}", True, WHITE)
        self.screen.blit(cv_control, (5,5))
        best_score_text = font_15.render(f"Best: {self.best_score}", True, WHITE)
        self.screen.blit(best_score_text, (5,20))

        # Escribir el Score
        score_text = font.render(str(self.score), True, WHITE)
        self.screen.blit(score_text, (self.screen.get_width()//2 - score_text.get_width()//2,20))

        # Actualizamos la pantalla
        pygame.display.update()

    def run(self):
        while self.running_game:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)
        pygame.quit()

game = Game()
game.run()