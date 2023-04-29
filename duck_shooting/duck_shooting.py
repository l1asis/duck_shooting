import pygame, sys, random

class Text(pygame.sprite.Sprite):
    def __init__(self, text, font: pygame.font.Font, color, pos):
        super().__init__()
        self.image = font.render(text, True, color)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.color = color
    def update(self, text):
        self.image = font.render(text, True, self.color)

class TextVariable(Text):
    def __init__(self, text, value, font: pygame.font.Font, color, pos):
        self.text = text
        self.value = value
        super().__init__(f"{self.text}: {self.value}", font, color, pos)
    def update(self):
        self.image = font.render(f"{self.text}: {self.value}", True, self.color)


class Crosshair(pygame.sprite.Sprite):
    def __init__(self, picture_path):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        self.gunshot = pygame.mixer.Sound(".\\assets\\gunshot.mp3")
        self.gunshot.set_volume(0.2)

    def shoot(self):
        self.gunshot.play()
        shooted = pygame.sprite.spritecollide(crosshair, target_group, dokill=True)
        if shooted:
            score.value += len(shooted)*10
        
    def update(self):
        self.rect.center = pygame.mouse.get_pos()

class Target(pygame.sprite.Sprite):
    def __init__(self, picture_path, pos_x, pos_y):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        self.rect.center = (pos_x, pos_y)

class GameState():
    def __init__(self):
        self.state = "intro"

    def intro(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if play_text.rect.collidepoint(pos):
                    crosshair.shoot()
                    self.state = "level_1"
                elif exit_text.rect.collidepoint(pos):
                    pygame.quit()
                    sys.exit()
    
        screen.blit(background,(0,0))
        text_group.draw(screen)
        crosshair_group.draw(screen)
        crosshair_group.update()
        fps.value = clock.get_fps()
        fps_group.update()
        fps_group.draw(screen)
        pygame.display.flip()
    
    def level_1(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                crosshair.shoot()
    
        screen.blit(background,(0,0))
        target_group.draw(screen)
        score_group.draw(screen)
        score_group.update()
        if score.value >= 300:
            print("You won!")
            self.state = "intro"
        crosshair_group.draw(screen)
        crosshair_group.update()
        pygame.display.flip()

    def state_manager(self):
        if self.state == "intro":
            self.intro()
        elif self.state == "level_1":
            self.level_1()
            

# Display stretching prevention
import prevent_display_stretching

# General setup
pygame.init()
clock = pygame.time.Clock()
game_state = GameState()

# Game Screen
size = width, height = 1280, 720
screen = pygame.display.set_mode(size)

# Intro
distance_text = 45
background = pygame.image.load(".\\assets\\main_menu_bg.png")
font = pygame.font.SysFont("Comic Sans MS", 56, True)
text_group = pygame.sprite.Group()
play_text = Text("Play", font, (255,255,255), (width/2, (height/2)-distance_text))
exit_text = Text("Exit", font, (255,255,255), (width/2, (height/2)+distance_text))
text_group.add((play_text, exit_text))

# FPS
fps_group = pygame.sprite.Group()
fps = TextVariable("FPS", 0, font, (255,255,255), (100,32))
fps_group.add(fps)

# Crosshair
pygame.mouse.set_visible(False)
crosshair = Crosshair(".\\assets\\crosshairs\\crosshair_white_large.png")
crosshair_group = pygame.sprite.Group()
crosshair_group.add(crosshair)

# Level 1
score_group = pygame.sprite.GroupSingle()
score = TextVariable("Score", 0, font, (42,42,42), (130,32))
score_group.add(score)
bullets_used, bullets_max = 0, 5
bullet_group = pygame.sprite.Group()

shooted_targets, targets_to_win = 0, 30


target_group = pygame.sprite.Group()
for target in range(30):
    pos_x, pos_y = random.randrange(32,width-32), random.randrange(32,height-32) # Random position for target
    new_target = Target(".\\assets\\target.png", pos_x, pos_y)
    while pygame.sprite.spritecollide(new_target, target_group, dokill=False): # Checking if the new target slips with another
        pos_x, pos_y = random.randrange(32,width-32), random.randrange(32,height-32)
        new_target = Target(".\\assets\\target.png", pos_x, pos_y)
    target_group.add(new_target)


while True:
    game_state.state_manager()
    clock.tick(60)