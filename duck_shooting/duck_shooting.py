import sys, random, time
import pygame

from typing import List
from collections import defaultdict

from debug import debug

class Text(pygame.sprite.Sprite):
    def __init__(self, text, font: pygame.font.Font, color, pos):
        super().__init__()
        self.image = font.render(text, True, color).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.color = color
    def update(self, text):
        self.image = font.render(text, True, self.color).convert_alpha()

class TextVariable(Text):
    def __init__(self, text, value, font: pygame.font.Font, color, pos):
        self.text = text
        self.value = value
        super().__init__(f"{self.text}{self.value}", font, color, pos)
    def update(self):
        self.image = font.render(f"{self.text}{self.value}", True, self.color).convert_alpha()


class Spritesheet():
    def __init__(self, sheet_path):
        self.sheet = pygame.image.load(sheet_path).convert_alpha()
    def get_frames(self, width, height) -> List[pygame.Surface]:
        frames = []
        top = 0
        for left in range(0, self.sheet.get_width(), width):
            frames.append(self.sheet.subsurface(left, top, width, height).convert_alpha())
        return frames


class Score():
    def __init__(self):
        self.group = pygame.sprite.GroupSingle()
        self.score = TextVariable("Score: ", 0, font, (255,255,255), (130,32))
        self.group.add(self.score)

    def update(self, num):
        self.score.value += num

    def draw(self, screen):
        self.group.update()
        self.group.draw(screen)

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

        self.images = {"loaded": pygame.image.load(".\\assets\\bullets\\icon_bullet_silver_long.png").convert_alpha(),
                       "empty": pygame.image.load(".\\assets\\bullets\\icon_bullet_empty_long.png").convert_alpha()}
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
    REMOVETARGET = pygame.USEREVENT + 1
    GENERATETARGET = pygame.USEREVENT + 2
    def __init__(self, event, seconds, loops):
        self.seconds = seconds
        milis = int(self.seconds * 1000)
        pygame.time.set_timer(event, milis, loops)

    def init_text(self):
        self.created_at = time.time()
        self.group = pygame.sprite.GroupSingle()
        self.text = TextVariable("Time: ", 0, font, (255,255,255), (600,32))
        self.group.add(self.text)

    def get_seconds(self):
        now = int(time.time() - self.created_at)
        return now
    
    def draw(self, screen):
        self.text.value = self.seconds - self.get_seconds()
        self.group.update()
        self.group.draw(screen)

    @classmethod
    def delay_generate_targets(self):
        cooldown_seconds = random.uniform(0.1, 1.5)
        Timer(Timer.GENERATETARGET, cooldown_seconds, 0)
        

class Crosshair(pygame.sprite.Sprite):
    def __init__(self, picture_path):
        super().__init__()
        self.image = pygame.image.load(picture_path).convert_alpha()
        self.rect = self.image.get_rect()
        self.gunshot = pygame.mixer.Sound(".\\assets\\sounds\\gunshot.mp3")
        self.empty_gunshot = pygame.mixer.Sound(".\\assets\\sounds\\empty-gunshot.mp3")
        self.reload_sound = pygame.mixer.Sound(".\\assets\\sounds\\reload.mp3")
        self.gunshot.set_volume(0.2)
        self.empty_gunshot.set_volume(0.2)
        self.reload_sound.set_volume(0.2)

        self.bonus_positives = defaultdict(int)
        self.last_bonus_at = time.time()
        self.bonus_text_created_at = time.time()
        self.block_score_on_targets = None
        self.bonus_text = None
        self.bonus_text_opacity = 255

    def shoot(self, targets):
        self.gunshot.play()
        shooted = pygame.sprite.spritecollide(crosshair, targets, dokill=False)
        if shooted:
            positives = defaultdict(int)
            for target in shooted:
                if target.animation != Target.ANIMATION_SHOOTED:
                    target.use_animation(Target.ANIMATION_SHOOTED, 1)
                    positives[target.target_type] += 1
                    self.bonus_positives[target.target_type] += 1
            return self.calculate_score(positives)
        else:
            return 0
    
    def calculate_score(self, positives) -> int:
        score_to_add = sum([target_to_score[target_type]*positives[target_type] 
                                for target_type in positives])
        return score_to_add

    def bonus_score(self) -> int:
        if time.time() - self.last_bonus_at <= 0.85:
            shot_targets_count = sum(self.bonus_positives.values())
            if shot_targets_count > 1 and self.block_score_on_targets != shot_targets_count:
                self.block_score_on_targets = shot_targets_count
                bonus = target_bonuses[shot_targets_count]
                self.bonus_text = Text(f"{random.choice(fun_text_templates)} {target_multipliers_text[shot_targets_count]}",
                            font2, (255,255,255), (width/2, 200))
                self.bonus_text_created_at = time.time()
                self.bonus_text_opacity = 255
                return bonus
            else:
                return 0
        else:
            self.bonus_positives.clear()
            self.block_score_on_targets = None
            self.last_bonus_at = time.time()
            return 0

    def empty_shoot(self):
        self.empty_gunshot.play()

    def reload(self):
        self.reload_sound.play()
        
    def update(self):
        self.rect.center = pygame.mouse.get_pos()

class Target(pygame.sprite.Sprite):
    RED_ONE = 0
    DUCK = 1
    ANIMATION_IDLE = 10
    ANIMATION_SHOOTED = 11
    def __init__(self, target_type, pos_x, pos_y):
        super().__init__()
        self.target_type = target_type
        self.created_at = time.time()
        self.disappear_after = random.uniform(1,3)
        
        # animation
        self.animation = Target.ANIMATION_IDLE
        self.frames = self.get_frames(self.target_type)
        self.frame_index = 0

        # image & rect
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

        # score text
        self.score = TextVariable("+", target_to_score[self.target_type], font, (255,255,255),
                                  (self.rect.centerx+20, self.rect.centery-140))
        self.score_opacity = 255

        # movement
        self.direction = 1
        self.move_speed = 235
        self.animation_speed = 70

        self.pos = pygame.math.Vector2(self.rect.topleft)

    def use_animation(self, animation, times_repeat=0):
        self.animation = animation
        self.times_repeat = times_repeat

    def animate_shooted(self, dt):
        screen.blit(self.score.image, (self.rect.centerx+20, self.rect.centery-140))
        self.score.image.set_alpha(self.score_opacity)
        self.score.image.convert_alpha()
        self.score_opacity -= 5

        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            if self.times_repeat:
                self.times_repeat -= 1
            else:
                self.kill()
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def animate_disappeared(self, dt):
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[-int(self.frame_index)]

        self.pos.y += self.direction * self.move_speed * dt
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)
        if self.rect.top > 560:
            self.kill()

    @classmethod
    def get_frames(self, target_type):
        if target_type == Target.RED_ONE:
            return red_target_frames
        elif target_type == Target.DUCK:
            return NotImplemented

    def update(self, dt):
        if self.animation == Target.ANIMATION_SHOOTED:
            self.animate_shooted(dt)
        elif self.animation == Target.ANIMATION_IDLE:
            if time.time() - self.created_at > self.disappear_after:
                self.animate_disappeared(dt)
            


class Level1():
    def __init__(self):
        # State
        self.state = "active"
        self.prev_time = time.time()

        # HUD
        self.load_hud()
        self.score = Score()
        self.bullets = Bullets(6)

        # Duration and Events
        self.duration = 45
        self.timer = Timer(Timer.ENDLEVEL, self.duration, 1)
        self.timer.init_text()

        # Targets
        self.target_group = pygame.sprite.Group()
        self.generate_targets(Target.RED_ONE, 15)
        Timer.delay_generate_targets()

    def load_hud(self):
        self.background = pygame.image.load(".\\assets\\hud\\blue_background(1280x720).png").convert()
        self.curtain_left = pygame.image.load(".\\assets\\hud\\curtain_left.png").convert_alpha()
        self.curtain_right = pygame.image.load(".\\assets\\hud\\curtain_right.png").convert_alpha()
        self.curtain_straight = pygame.image.load(".\\assets\\hud\\curtain_straight.png").convert_alpha()
        self.curtain_top = pygame.image.load(".\\assets\\hud\\curtain_top.png").convert_alpha()
        self.rifle = pygame.image.load(".\\assets\\hud\\rifle.png").convert_alpha()
        self.table = pygame.image.load(".\\assets\\hud\\table.png").convert_alpha()

    def generate_targets(self, target_type, count):
        for target in range(count):
            pos_x, pos_y = random.randrange(110,width-110), 465 # Random position for target
            new_target = Target(target_type, pos_x, pos_y)
            if pygame.sprite.spritecollide(new_target, self.target_group, dokill=False):
                continue
            else:
                self.target_group.add(new_target)

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.bullets.used != self.bullets.max_used:
                    self.score.update(crosshair.shoot(self.target_group))
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
            elif event.type == Timer.GENERATETARGET:
                random.seed()
                self.generate_targets(Target.RED_ONE, random.randint(1,2))
                Timer.delay_generate_targets()

    def update(self):
        dt = time.time() - self.prev_time
        self.prev_time = time.time()

        screen.blit(self.background,(0,0))

        self.target_group.update(dt)
        self.target_group.draw(screen)

        screen.blit(self.table,(0,height-self.table.get_height()))
        screen.blit(self.rifle,(self.table.get_rect().centerx, self.table.get_rect().centery+self.rifle.get_height()*1.25))
        screen.blit(self.curtain_left,(0,50))
        screen.blit(self.curtain_right,(width-self.curtain_right.get_width(),50))
        screen.blit(self.curtain_top,((self.curtain_straight.get_width()-self.curtain_top.get_width())/2, self.curtain_straight.get_rect().centery+20))
        screen.blit(self.curtain_straight,(0,0))

        self.bullets.draw(screen)
        bonus_score = crosshair.bonus_score()
        if bonus_score:
            self.score.update(bonus_score)
        if crosshair.bonus_text:
            if time.time() - crosshair.bonus_text_created_at > 1.05:
                crosshair.bonus_text_opacity -= 5
                crosshair.bonus_text.image.set_alpha(crosshair.bonus_text_opacity)
                crosshair.bonus_text.image.convert_alpha()
            screen.blit(crosshair.bonus_text.image, crosshair.bonus_text.rect)
        self.score.draw(screen)
        self.timer.draw(screen)
        crosshair_group.update()
        crosshair_group.draw(screen)
        pygame.display.update()


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
                    crosshair.gunshot.play()
                    self.state = "load_level"
                elif exit_text.rect.collidepoint(pos):
                    pygame.quit()
                    sys.exit()
    
        screen.blit(background,(0,0))
        text_group.draw(screen)
        crosshair_group.draw(screen)
        crosshair_group.update()
        #debug(clock.get_fps())
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
background = pygame.image.load(".\\assets\\hud\\blue_background(1280x720).png").convert()
font = pygame.font.SysFont("Comic Sans MS", 56, True)
font2 = pygame.font.SysFont("Comic Sans MS", 32, True)
text_group = pygame.sprite.Group()
play_text = Text("Play", font, (255,255,255), (width/2, (height/2)-distance_text))
exit_text = Text("Exit", font, (255,255,255), (width/2, (height/2)+distance_text))
text_group.add((play_text, exit_text))

# Crosshair
pygame.mouse.set_visible(False)
crosshair = Crosshair(".\\assets\\crosshairs\\crosshair_white_large.png")
crosshair_group = pygame.sprite.Group()
crosshair_group.add(crosshair)

#Spritesheets
red_target_frames = Spritesheet(".\\assets\\targets\\target2_spritesheet_360degree.png").get_frames(104, 190)
target_to_score = {Target.RED_ONE: 10, Target.DUCK: 15}
fun_text_templates = ["Wow!!", "You're crazy!", "GOD OF DUCKS?!?", "Sweet :)"]
target_bonuses = {2: 5, 3: 10, 4: 15, 5: 25, 6: 50} # 2t - +5, 3t - +10, 4t - +15, 5t - +25
target_multipliers_text = {2:"Two targets! +5 points!", 3:"Three targets! +10 points!", 
                           4:"Four targets? +15 points!", 5:"FIVE TARGETS!! +25 points!",
                           6:"SIX TARGETS?????? I have no words. +50 points"}


while 1:
    game_state.state_manager()
    clock.tick(60)