import sys, random, time
import gc
import pygame

from collections import defaultdict

class Text(pygame.sprite.Sprite):
    def __init__(self, text, font: pygame.font.Font, color, pos):
        super().__init__()
        self.image = font.render(text, True, color).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.pos = pos
        self.color = color
    def update(self, text):
        self.image = font.render(text, True, self.color).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

class TextVariable(Text):
    def __init__(self, text, value, font: pygame.font.Font, color, pos):
        self.text = text
        self.value = value
        super().__init__(f"{self.text}{self.value}", font, color, pos)
    def update(self):
        self.image = font.render(f"{self.text}{self.value}", True, self.color).convert_alpha()


class Bonus(Text):
    def __init__(self, font: pygame.font.Font, color, pos):
        super().__init__("", font, color, pos)
        self.next_at = None
        self.bonus = 0
        self.total_shot = 0
        self.opacity = 255

    def set_interval(self, last_shot_at):
        seconds = bonuses_timings[self.total_shot]
        if seconds:
            self.next_at = last_shot_at + seconds
        else:
            self.next_at = None

    def streak(self, points: int):
        self.bonus = points
        funny_text = f"{random.choice(fun_text_templates)} {bonuses_text[self.total_shot]}"
        self.image = font.render(funny_text, True, self.color).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.opacity = 255

    def break_streak(self):
        self.bonus = 0
        self.total_shot = 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def update(self):
        if self.next_at:
            if time.time() > self.next_at:
                self.total_shot = 0
                self.next_at = None
        if self.opacity > 0:
            self.opacity -= 3
            self.image.set_alpha(self.opacity)

    def __str__(self):
        return f"<Bonus({self.bonus})>"
    def __add__(self, value):
        self.bonus += value
    def __radd__(self, value):
        return value + self.bonus
    def __sub__(self, value):
        self.bonus -= value
    def __rsub__(self, value):
        return value - self.bonus
    def __mul__(self, value):
        self.bonus *= value
    def __rmul__(self, value):
        return value * self.bonus
    

class Spritesheet():
    def __init__(self, sheet_path):
        self.sheet = pygame.image.load(sheet_path).convert_alpha()
    def get_frames(self, width, height) -> list[pygame.Surface]:
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
    COUNTDOWN = pygame.USEREVENT + 0
    def __init__(self, event, seconds, loops):
        self.event = event
        self.seconds = seconds
        self.milis = int(seconds * 1000)
        self.loops = loops
        pygame.time.set_timer(self.event, self.milis, self.loops)

    def stop(self):
        pygame.time.set_timer(self.event, 0, 0)

class CountdownTimer(Timer):
    def __init__(self, event=Timer.COUNTDOWN, seconds=1, loops=45):
        super().__init__(event, seconds, loops)
        self.group = pygame.sprite.GroupSingle()
        self.text = TextVariable("Time: ", self.loops, font, (255,255,255), (600,32))
        self.group.add(self.text)

    def reset(self):
        pygame.time.set_timer(self.event, self.milis, self.loops)
        self.text.value = self.loops

    def draw(self, screen):
        self.group.update()
        self.group.draw(screen)

    def get_seconds(self):
        return self.text.value
        

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

        self.last_shot_at = None
        self.bonus = Bonus(font2, (255,255,255), (width/2, 200))

    def shoot(self, targets):
        self.last_shot_at = time.time()
        self.gunshot.play()
        shooted = pygame.sprite.spritecollide(crosshair, targets, dokill=False)
        if shooted:
            shot_count = defaultdict(int)
            for target in shooted:
                if target.animation != Target.ANIMATION_SHOOTED:
                    target.use_animation(Target.ANIMATION_SHOOTED, 1)
                    shot_count[target.target_type] += 1
            return self.calculate_score(shot_count)
        else:
            return 0

    def calculate_score(self, shot_count: dict) -> int:
        score = sum([target_to_score[target]*t_count for target,t_count in shot_count.items()])
        self.bonus.total_shot += sum(shot_count.values())
        local_total_shot = sum(shot_count.values())
        if local_total_shot >= 1 and (2 <= self.bonus.total_shot < 6):
            if not self.bonus.next_at:
                self.bonus.streak(bonuses[self.bonus.total_shot])
            else:
                if self.last_shot_at <= self.bonus.next_at:
                    self.bonus.streak(bonuses[self.bonus.total_shot])
                else:
                    self.bonus.break_streak()
        elif self.bonus.total_shot >= 6:
            if self.last_shot_at <= self.bonus.next_at:
                self.bonus.streak(bonuses[self.bonus.total_shot])
            else:
                self.bonus.break_streak()
        else:
            self.bonus.bonus = 0

        self.bonus.set_interval(self.last_shot_at)

        return score + self.bonus

    def empty_shoot(self):
        self.empty_gunshot.play()

    def reload(self):
        self.reload_sound.play()
        
    def update(self):
        self.rect.center = pygame.mouse.get_pos()


class FallingObject(pygame.sprite.Sprite):
    DUCK_WHITE = 0
    DUCK_YELLOW = 1
    DUCK_BROWN = 2
    def __init__(self, type_, pos_x, pos_y):
        super().__init__()
        self.original_image = pygame.transform.gaussian_blur(falling_mappings[type_], 6, False)
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        self.position = pygame.math.Vector2(pos_x, pos_y)
        self.direction = pygame.math.Vector2(0, 1)
        self.speed = random.randint(150, 280)
        self.angle_speed = random.randint(150, 280)
        self.angle = 0

    def update(self, dt):
        if self.angle_speed != 0:
            # Rotate the direction vector and then the image.
            #self.direction.rotate_ip(self.angle_speed)
            self.angle += self.angle_speed * dt
            self.image = pygame.transform.rotate(self.original_image, -self.angle)
            self.rect = self.image.get_rect(center=self.rect.center)
        # Update the position vector and the rect.
        self.position += self.direction * self.speed * dt
        self.rect.center = self.position

        if self.rect.top > height:
            self.kill()

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
        self.score_opacity -= 255 * dt

        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.frames):
            if self.times_repeat:
                self.times_repeat -= 1
            else:
                self.kill_()
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
            self.kill_()

    def kill_(self):
        self.kill()
        del self
        gc.collect()


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
            

class Intro():
    def __init__(self):
        self.state = "intro"
        self.prev_time = time.time()
        self.background = pygame.transform.gaussian_blur(pygame.image.load(".\\assets\\hud\\blue_background(1280x720).png").convert(), 6)
        #self.wooden_menu = pygame.image.load(".\\assets\\hud\\wooden_menu_bar_2.png").convert()
        self.text_group = pygame.sprite.Group()
        self.title_text = Text("DUCK SHOOTING", font, (255,190,0), (width/2, (height/2)-170))
        self.play_text = Text("Play", font, (255,255,255), (width/2, (height/2)-45))
        self.exit_text = Text("Exit", font, (255,255,255), (width/2, (height/2)+45))
        self.text_group.add((self.title_text, self.play_text, self.exit_text))
        self.falling_objects_group = pygame.sprite.Group()
        self.generate_objects(random.randint(0,2), 1)

    def generate_objects(self, type_, count):
        for num in range(count):
            pos_x, pos_y = random.randrange(30,width-30), 0
            object_ = FallingObject(type_, pos_x, pos_y)
            self.falling_objects_group.add(object_)
        self.delay_objects(self.prev_time)

    def delay_objects(self, start_time):
        random.seed()
        cooldown_seconds = random.uniform(0.1, 1.5)
        self.next_objects_at = start_time + cooldown_seconds

    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = pygame.mouse.get_pos()
                if self.play_text.rect.collidepoint(pos):
                    crosshair.gunshot.play()
                    self.state = "load_level"
                elif self.exit_text.rect.collidepoint(pos):
                    pygame.quit()
                    sys.exit()
        self.update()

    def update(self):
        dt = time.time() - self.prev_time
        self.prev_time = time.time()

        screen.blit(self.background,(0,0))
        self.falling_objects_group.draw(screen)
        self.falling_objects_group.update(dt)
        if self.prev_time >= self.next_objects_at:
            self.generate_objects(random.randint(0,2), 1)
        #screen.blit(self.wooden_menu,(width/2-self.wooden_menu.get_width()/2, height-self.wooden_menu.get_height()))

        self.text_group.draw(screen)
        crosshair_group.draw(screen)
        crosshair_group.update()
        pygame.display.flip()


class EndLevel():
    def __init__(self):
        self.state = "endlevel"
        self.background = pygame.image.load(".\\assets\\hud\\blue_background(1280x720).png").convert()
        self.text_group = pygame.sprite.Group()
        self.text_game_over = Text("Time out! Game is over!", font, (255,255,255), (width/2, 150))
        self.text_score = TextVariable("Your score: ", None, font, (255,255,255), (width/2, 300))
        self.text_press_continue = Text("Press `Enter` to continue...", font, (255,255,255), (width/2, 450))
        self.text_group.add((self.text_game_over, self.text_score, self.text_press_continue))
    
    def event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    crosshair.gunshot.play()
                    self.state = "intro"
        self.update()

    def update(self):
        screen.blit(self.background,(0,0))
        self.text_group.draw(screen)
        crosshair_group.draw(screen)
        crosshair_group.update()
        pygame.display.flip()

    def update_score(self, score):
        self.text_score.value = score
        self.text_score.update()

class Level1():
    def __init__(self):
        # State
        self.state = "running"
        self.prev_time = time.time()

        # HUD
        self.load_hud()
        self.score = Score()
        self.bullets = Bullets(6)

        # Duration and Events
        self.duration = 60
        self.timer = CountdownTimer(loops=self.duration)

        # Targets
        self.target_group = pygame.sprite.Group()
        self.generate_targets(Target.RED_ONE, 20)

    def restart(self):
        self.state = "running"
        self.prev_time = time.time()
        self.score.score.value = 0
        self.bullets.loaded()
        self.timer.reset()

        self.target_group.empty()
        self.generate_targets(Target.RED_ONE, 20)

    def load_hud(self):
        self.background = pygame.image.load(".\\assets\\hud\\blue_background(1280x720).png").convert()
        self.curtain_left = pygame.image.load(".\\assets\\hud\\curtain_left.png").convert_alpha()
        self.curtain_right = pygame.image.load(".\\assets\\hud\\curtain_right.png").convert_alpha()
        self.curtain_straight = pygame.image.load(".\\assets\\hud\\curtain_straight.png").convert_alpha()
        self.curtain_top = pygame.image.load(".\\assets\\hud\\curtain_top.png").convert_alpha()
        self.rifle = pygame.image.load(".\\assets\\hud\\rifle.png").convert_alpha()
        self.table = pygame.image.load(".\\assets\\hud\\table.png").convert_alpha()

    def delay_targets(self, start_time):
        random.seed()
        cooldown_seconds = random.uniform(0.1, 1.5)
        self.next_targets_at = start_time + cooldown_seconds

    def generate_targets(self, target_type, count):
        for num in range(count):
            pos_x, pos_y = random.randrange(110,width-110), 465
            target = Target(target_type, pos_x, pos_y)
            if pygame.sprite.spritecollide(target, self.target_group, dokill=0):
                continue
            else:
                self.target_group.add(target)
        self.delay_targets(self.prev_time)

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
            elif event.type == Timer.COUNTDOWN:
                self.timer.text.value -= 1
                if not self.timer.text.value:
                    self.state = "endlevel"

    def update(self):
        dt = time.time() - self.prev_time
        self.prev_time = time.time()

        screen.blit(self.background,(0,0))

        if self.prev_time >= self.next_targets_at:
            self.generate_targets(Target.RED_ONE, random.randint(1,2))

        self.target_group.update(dt)
        self.target_group.draw(screen)

        screen.blit(self.table,(0,height-self.table.get_height()))
        screen.blit(self.rifle,(self.table.get_rect().centerx, self.table.get_rect().centery+self.rifle.get_height()*1.25))
        screen.blit(self.curtain_left,(0,50))
        screen.blit(self.curtain_right,(width-self.curtain_right.get_width(),50))
        screen.blit(self.curtain_top,((self.curtain_straight.get_width()-self.curtain_top.get_width())/2, self.curtain_straight.get_rect().centery+20))
        screen.blit(self.curtain_straight,(0,0))

        self.bullets.draw(screen)
        crosshair.bonus.update()
        crosshair.bonus.draw(screen)
        self.score.draw(screen)
        self.timer.draw(screen)
        crosshair_group.update()
        crosshair_group.draw(screen)

        pygame.display.flip()


class GameState():
    def __init__(self):
        self.state = "intro"
        self.intro = Intro()
        self.endlevel = EndLevel()
        self.level = None
    
    def load_level(self):
        self.state = "level1"
        if not self.level:
            self.level = Level1()
        else:
            self.level.restart()

    def state_manager(self):
        if self.state == "intro":
            self.intro.event()
            if self.intro.state != "intro":
                self.intro.falling_objects_group.empty()
                self.state = self.intro.state
                self.intro.state = "intro"
        elif self.state == "load_level":
            self.load_level()
        elif self.state.startswith("level"):
            self.level.event()
            self.level.update()
            if self.level.state == "endlevel":
                self.state = self.level.state
                self.score = self.level.score.score.value
                self.endlevel.update_score(self.score)
        elif self.state == "endlevel":
            self.endlevel.event()
            if self.endlevel.state != "endlevel":
                self.state = self.endlevel.state
                self.endlevel.state = "endlevel"
            

# Display stretching prevention
import prevent_display_stretching

# General setup
pygame.init()
clock = pygame.time.Clock()

# Game Screen
size = width, height = 1280, 720
screen = pygame.display.set_mode(size)

# Fonts
font = pygame.font.SysFont("Comic Sans MS", 56, True)
font2 = pygame.font.SysFont("Comic Sans MS", 22, True)

# Crosshair
pygame.mouse.set_visible(False)
crosshair = Crosshair(".\\assets\\crosshairs\\crosshair_white_large.png")
crosshair_group = pygame.sprite.Group()
crosshair_group.add(crosshair)

# Spritesheets & Other
duck_white = pygame.image.load(".\\assets\\ducks\\test_duck_white.png").convert_alpha()
duck_yellow = pygame.image.load(".\\assets\\ducks\\test_duck_yellow.png").convert_alpha()
duck_brown = pygame.image.load(".\\assets\\ducks\\test_duck_brown.png").convert_alpha()
falling_mappings = {FallingObject.DUCK_WHITE: duck_white,
                    FallingObject.DUCK_YELLOW: duck_yellow,
                    FallingObject.DUCK_BROWN: duck_brown}

red_target_frames = Spritesheet(".\\assets\\targets\\target2_spritesheet_360degree.png").get_frames(104, 190)
target_to_score = {Target.RED_ONE: 10, Target.DUCK: 15}
fun_text_templates = ["Wow!!", "You're crazy!", "GOD OF DUCKS?!?", "Sweet :)"]
bonuses = {2: 5, 3: 10, 4: 15, 5: 25, 6: 50} # 2t - +5, 3t - +10, 4t - +15, 5t - +25
bonuses_timings = {0: None, 1: 0.475, 2: 0.330, 3: 0.265, 4: 0.205, 5: 0.150}
bonuses_text = {2:"Two targets! +5 points!", 3:"Three targets! +10 points!", 
                           4:"Four targets? +15 points!", 5:"FIVE TARGETS!! +25 points!",
                           6:"SIX TARGETS?????? I have no words. +50 points"}

# Game State Manager
game_state = GameState()

while 1:
    game_state.state_manager()
    clock.tick(60)