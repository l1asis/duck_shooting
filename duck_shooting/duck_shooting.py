import sys, random
import pygame

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


class Score():
    def __init__(self):
        self.group = pygame.sprite.GroupSingle()
        self.score = TextVariable("Score", 0, font, (255,255,255), (130,32))
        self.group.add(self.score)

    def update(self, num):
        self.score.value += num

    def draw(self, screen):
        self.group.draw(screen)
        self.group.update()

class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, pos_x, pos_y):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = (pos_x, pos_y)

class Bullets():
    def __init__(self, max) -> None:
        self.distance_x, self.distance_y = 20, 15
        self.used, self.max_used = 0, max

        self.images = {"loaded": pygame.image.load(".\\assets\\bullets\\icon_bullet_silver_long.png"),
                       "empty": pygame.image.load(".\\assets\\bullets\\icon_bullet_empty_long.png")}
        for bullet_type in self.images.keys():
            self.images[bullet_type] = pygame.transform.smoothscale_by(self.images[bullet_type], 1.45)

        self.group = pygame.sprite.Group()
        for num in range(1, self.max_used+1):
            self.group.add(Bullet(self.images["loaded"],
                                  1280-(self.images["loaded"].get_width()*num) - self.distance_x*num,
                                  720-(self.images["loaded"].get_height()) - self.distance_y ))
    
    def draw(self, screen):
        self.group.draw(screen)

    def shooted(self, used_bullet):
        for index, bullet in enumerate(self.group):
            if index == used_bullet:
                bullet.image = self.images["empty"]
    
    def loaded(self):
        for bullet in self.group:
            bullet.image = self.images["loaded"]
        self.used = 0


class Timer():
    ENDLEVEL = pygame.USEREVENT + 0
    def __init__(self, event, seconds, loops):
        milis = seconds * 1000
        self.start_ticks = pygame.time.get_ticks()
        self.group = pygame.sprite.GroupSingle()
        self.timer = TextVariable("Time", 0, font, (255,255,255), (600,32))
        self.group.add(self.timer)
        pygame.time.set_timer(event, milis, loops)

    def get_seconds(self):
        now_ticks = pygame.time.get_ticks()
        seconds = (now_ticks - self.start_ticks) // 1000
        return seconds
    
    def draw(self, screen):
        self.timer.value = self.get_seconds()
        self.group.update()
        self.group.draw(screen)

class Crosshair(pygame.sprite.Sprite):
    def __init__(self, picture_path):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        self.gunshot = pygame.mixer.Sound(".\\assets\\gunshot.mp3")
        self.empty_gunshot = pygame.mixer.Sound(".\\assets\\empty-gunshot.mp3")
        self.reload_sound = pygame.mixer.Sound(".\\assets\\reload.mp3")
        self.gunshot.set_volume(0.2)
        self.empty_gunshot.set_volume(0.2)
        self.reload_sound.set_volume(0.2)
        self.update_targets(pygame.sprite.Group())

    def shoot(self):
        self.gunshot.play()
        shooted = pygame.sprite.spritecollide(crosshair, self.targets, dokill=True)
        if shooted:
            return len(shooted)*10
        else:
            return 0
        
    def empty_shoot(self):
        self.empty_gunshot.play()

    def reload(self):
        self.reload_sound.play()
        
    def update(self):
        self.rect.center = pygame.mouse.get_pos()

    def update_targets(self, targets):
        self.targets = targets


class Target(pygame.sprite.Sprite):
    def __init__(self, picture_path, pos_x, pos_y):
        super().__init__()
        self.image = pygame.image.load(picture_path)
        self.rect = self.image.get_rect()
        self.rect.center = (pos_x, pos_y)

class Level1():
    def __init__(self):
        self.state = "active"

        self.timer = Timer(Timer.ENDLEVEL, 20, 1)
        self.score = Score()
        self.bullets = Bullets(6)

        self.target_group = pygame.sprite.Group()
        for target in range(30):
            pos_x, pos_y = random.randrange(32,width-32), random.randrange(32,height-32) # Random position for target
            new_target = Target(".\\assets\\target.png", pos_x, pos_y)
            while pygame.sprite.spritecollide(new_target, self.target_group, dokill=False): # Checking if the new target slips with another
                pos_x, pos_y = random.randrange(32,width-32), random.randrange(32,height-32)
                new_target = Target(".\\assets\\target.png", pos_x, pos_y)
            self.target_group.add(new_target)

        crosshair.update_targets(self.target_group)

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.bullets.used != self.bullets.max_used:
                    self.score.update(crosshair.shoot())
                    self.bullets.shooted(self.bullets.used)
                    self.bullets.used += 1
                else:
                    crosshair.empty_shoot()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.bullets.used == self.bullets.max_used:
                    crosshair.reload()
                    self.bullets.loaded()
            elif event.type == Timer.ENDLEVEL:
                print(f"Time out! Your score is: {self.score.score.value}")
                self.state = "inactive"

    def update(self):
        screen.blit(background,(0,0))
        self.target_group.draw(screen)
        self.bullets.draw(screen)
        self.score.draw(screen)
        self.timer.draw(screen)
        crosshair_group.draw(screen)
        crosshair_group.update()
        pygame.display.flip()


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
                    self.state = "load_level"
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
    
    def load_level(self):
        self.level = Level1()
        self.state = "level1"

    def state_manager(self):
        if self.state == "intro":
            self.intro()
        elif self.state == "load_level":
            self.load_level()
        elif self.state.startswith("level"):
            self.level.event()
            self.level.update()
            if self.level.state == "inactive":
                self.state = "intro"
        
            

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


while True:
    game_state.state_manager()
    clock.tick(60)