import numpy as np
import pygame
import random
import os
from pygame import transform
from pygame.constants import K_SPACE
from tensorflow import keras
from keras import Sequential
from keras.layers import Dense, Activation

pygame.font.init()

TOTAL_POPULATION = 8
valhalla = []
highest_fitness = -1
best_weights = []
generation = 1
high_score = 0

FPS = 60
WIN_WIDTH = 800
WIN_HEIGHT = 800
PIPE_SEPARATION = 600
BASE_HEIGHT = WIN_HEIGHT - 80

BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(
        os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(
        os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(
        os.path.join('imgs', 'bird3.png'))),
]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(
    os.path.join('imgs', 'pipe.png')))
BASE_IMG = transform.scale(pygame.image.load(
    os.path.join('imgs', 'base.png')), (WIN_WIDTH, 265))
BG_IMG = transform.scale(pygame.image.load(
    os.path.join('imgs', 'bg.png')), (WIN_WIDTH, WIN_HEIGHT))

STAT_FONT = pygame.font.SysFont("comicsans", 50)   

def create_model():
    # model = Sequential()
    # model.add(Dense(3, input_shape=(3,)))
    # model.add(Activation('relu'))

    # model.add(Dense(7, input_shape = (3,)))
    # model.add(Activation('relu'))

    # model.add(Dense(1, input_shape= (7,)))
    # model.add(Activation('sigmoid'))

    # model.compile(loss='mse', optimizer='adam')

    # return model
    model = keras.Sequential([
        keras.layers.Dense(3, input_shape = (3,)),
        keras.layers.Dense(7, activation="relu"),
        keras.layers.Dense(1, activation="sigmoid")
    ])
    model.compile(optimizer="adam", loss="mse")

    return model




class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    JUMP_VELOCITY = -10.5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]
        self.brain = create_model()
        self.fitness = 0

    def should_jump(self, nearest_pipe):
        bird_height = self.y
        vertical_distance_to_top_pipe = abs(self.y - nearest_pipe.height)
        vertical_distance_to_bottom_pipe = abs(self.y - nearest_pipe.bottom)
        inputs = np.asarray([
            bird_height/BASE_HEIGHT,
            vertical_distance_to_top_pipe/BASE_HEIGHT,
            vertical_distance_to_bottom_pipe/BASE_HEIGHT,
            ])
        inputs = np.atleast_2d(inputs)
        probability = self.brain.predict(inputs, 1)[0]
        
        return probability >= .5   

    def jump(self):
        self.vel = self.JUMP_VELOCITY
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        if d >= 16:
            d = 16

        if d < 0:
            d -= 2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4+1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
    
    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))
    
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True
        
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        
        if (self.x1 + self.WIDTH < 0):
            self.x1 = self.x2 + self.WIDTH

        if (self.x2 + self.WIDTH < 0):
            self.x2 = self.x1 + self.WIDTH  

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

def draw_window(win, birds, pipes, base, score):
    global generation
    global high_score
    if (score > high_score):
        high_score = score

    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: "+str(score), 1, (255,255,255))
    win.blit(text, (WIN_WIDTH - 10- text.get_width(), 10))

    text = STAT_FONT.render("Alive: "+str(len(birds)), 1, (255,255,255))
    win.blit(text, (10, 10))

    text = STAT_FONT.render("Gen: "+str(generation), 1, (255,255,255))
    win.blit(text, (10, 40))

    text = STAT_FONT.render("High Score: "+str(high_score), 1, (255,255,255))
    win.blit(text, (10, 80))

    base.draw(win)

    for bird in birds:
        bird.draw(win)

    if (len(birds) == 0):
        text = STAT_FONT.render("Game Over", 1, (255,255,255))
        win.blit(text, ((WIN_WIDTH/2)-(text.get_width()/2), WIN_HEIGHT/2))

    pygame.display.update()

def get_pipe_separation():
    return PIPE_SEPARATION
    # return random.randrange(400, 600)

def handle_player_actions(bird, keys_pressed):
    if (keys_pressed[K_SPACE]):
        bird.jump()

def main(birds):
    global valhalla
    base = Base(BASE_HEIGHT)
    pipes = [Pipe(900), Pipe(900+PIPE_SEPARATION)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while  run:
        clock.tick(FPS)
        current_pipe_separation = get_pipe_separation()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            # run = False
            game_over()
            # break

        keys_pressed = pygame.key.get_pressed()    
        for x, bird in enumerate(birds):
            bird.move()
            bird.fitness += 1
            # handle_player_actions(bird, keys_pressed)

            if bird.should_jump(pipes[pipe_ind]):
                bird.jump()

        add_pipe = False
        rem = []
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    bird.fitness -= 1
                    valhalla.append(bird)
                    birds.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True
                    bird.fitness += 25    

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()
        
        if add_pipe:
            score += 1
            pipes.append(Pipe(pipes[-1].x + current_pipe_separation))

        for r in rem:
            pipes.remove(r)   

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= WIN_HEIGHT-80 or bird.y < 0:
                bird.fitness -= 1
                valhalla.append(bird)
                birds.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score)

def get_the_fittest_parents():
    global valhalla
    return [valhalla[-1], valhalla[-2]]
    parent1 = random.randint(0,TOTAL_POPULATION-1)
    parent2 = random.randint(0,TOTAL_POPULATION-1)
    for i in range(TOTAL_POPULATION):
        if valhalla[i].fitness >= valhalla[parent1].fitness:
            parent1 = i

    for j in range(TOTAL_POPULATION):
        if j != parent1:
            if valhalla[j].fitness >= valhalla[parent2].fitness:
                parent2 = j
    print('Fittest parent index = ', [parent1, parent2])            

    return (valhalla[parent1], valhalla[parent2])

def crossover_parents(parent1, parent2):
    weight1 = parent1.brain.get_weights()
    weight2 = parent2.brain.get_weights()

    new_weight1 = weight1
    new_weight2 = weight2

    gene = random.randint(0, len(new_weight2)-1)

    new_weight1[gene] = weight2[gene]
    new_weight2[gene] = weight1[gene]

    return np.asarray([new_weight1, new_weight2])

def model_mutate(weights):
    for i in range(len(weights)):
        for j in range(len(weights[i])):
            if( random.uniform(0,1) > .85):
                change = random.uniform(-.5,.5)
                weights[i][j] += change
                # print('model mutaed once')
                
    return weights   

def game_over():
    global highest_fitness
    global best_weights
    global generation
    updated = False
    for bird in valhalla:
        if (bird.fitness >= highest_fitness):
            updated = True
            highest_fitness = bird.fitness
            best_weights = bird.brain.get_weights()

    print('highest_fitness = ', highest_fitness)


    parent1, parent2 = get_the_fittest_parents()
    print('last_parent_fitness = ', parent1.fitness)
    new_weights = []
    for i in range(TOTAL_POPULATION//2):
        cross_over_weights = crossover_parents(parent1, parent2)
        
        new_weights.append(model_mutate(cross_over_weights[0]))
        new_weights.append(model_mutate(cross_over_weights[1]))

        if updated == False:
            new_weights[-1] = best_weights
    
    new_gen_birds = []
    for i in range(len(new_weights)):
        new_gen_bird = Bird(230, 350)
        new_gen_bird.brain.set_weights(new_weights[i])
        new_gen_birds.append(new_gen_bird)

    generation += 1
    main(new_gen_birds) 


def run():
    birds = []
    for i in range(TOTAL_POPULATION):
        birds.append(Bird(230, 350))
    main(birds)


if __name__ == "__main__":
    run()