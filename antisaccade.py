#!/usr/bin/env python

from __future__ import division
from random import randrange, choice, sample
import pygame
import math
import gc
import sys
import time

class World(object):
    """Task Environment"""
    
    def __init__(self):
        super(World, self).__init__()
        pygame.mouse.set_visible(False)
        self.screen = pygame.display.set_mode((1024, 768), 0)
        width,height = self.screen.get_size()
        self.center_x = width/2
        self.center_y = height/2
        self.offsets = [self.center_x - width/3, self.center_x + width/3]
        self.worldsurf = self.screen.copy()
        self.worldsurf_rect = self.worldsurf.get_rect()
        self.obj_width = int(self.center_y / 10)
        self.arrow_font = pygame.font.Font("ARROW_FONTS.ttf", self.obj_width)
        self.arrows = [u'\uf045',u'\uf046',u'\uf047',u'\uf048'] # Right, Up, Left, Down
        self.clock = pygame.time.Clock()
        self.accuracy = []
        
    def get_fixation_interval(self):
        return randrange(1500,3500,1)
    
    def draw_arrow(self, type, x):
         arrow = self.arrow_font.render(self.arrows[type], True, (255,255,255))
         arrow_rect = arrow.get_rect()
         arrow_rect.centerx = x
         arrow_rect.centery = self.center_y
         self.worldsurf.blit(arrow, arrow_rect)

    def draw_mask(self, x):
        pygame.draw.rect(self.worldsurf, (255,255,255), (x-self.obj_width/2,self.center_y-self.obj_width/2,self.obj_width,self.obj_width),0)
        
    def draw_cue(self, x):
        pygame.draw.rect(self.worldsurf, (255,255,255), (x-self.obj_width/2,self.center_y-self.obj_width/2,self.obj_width,self.obj_width),0)
        
    def draw_fixation_cross(self):
        cross_radius = self.center_y / 18
        pygame.draw.line(self.worldsurf, (255,0,0), (self.center_x-cross_radius,self.center_y), (self.center_x+cross_radius, self.center_y), 4)
        pygame.draw.line(self.worldsurf, (255,0,0), (self.center_x,self.center_y-cross_radius), (self.center_x, self.center_y+cross_radius), 4)
        
    def clear(self):
        self.worldsurf.fill((0,0,0))
        
    def update_world(self):
        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        pygame.display.flip()
        
    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    mean = sum(self.accuracy)/len(self.accuracy)
                    if len(self.accuracy)>1:
                        print '~~~~Accuracy~~~~'
                        print 'Mean:\t%f' % (mean)
                        print 'StdDev:\t%f' % (math.sqrt(sum((x-mean)**2 for x in self.accuracy)/len(self.accuracy)))
                    sys.exit()
                if self.state == 4:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_UP or event.key == pygame.K_RIGHT:
                        if event.key == pygame.K_LEFT and self.answer == 2:
                            self.accuracy.append(1)
                        elif event.key == pygame.K_UP and self.answer == 1:
                            self.accuracy.append(1)
                        elif event.key == pygame.K_RIGHT and self.answer == 0:
                            self.accuracy.append(1)
                        else:
                            self.accuracy.append(0)
                        self.state = 0
                elif self.state < 4:
                    self.state += 1
                    
    def draw_world(self):
        self.clear()
        if self.state == 1:
            self.draw_fixation_cross()
        elif self.state == 2:
            self.draw_cue(self.loc1)
        elif self.state == 3:
            self.draw_arrow(self.answer, self.loc2)
        elif self.state == 4:
            self.draw_mask(self.loc2)
        self.update_world()
        
    def generate_trial(self):
        self.loc1, self.loc2 = sample(self.offsets,2)
        self.answer = choice([2,1,0])
            
    def run(self):
        self.state = 0
        while True:
            if self.state == 0:
                self.generate_trial()
                self.state = 1
            self.clock.tick(30)
            self.draw_world()
            self.process_events()
        
        #time.sleep(self.get_fixation_interval()/1000.0)
        #self.clear()
        
        #time.sleep(0.4)
        #self.clear()
        
        #time.sleep(0.15)
        #self.clear()
        

            

def main():
    w = World()
    while True:
        w.run()

if __name__ == '__main__':
    gc.disable()
    pygame.display.init()
    pygame.font.init()
    main()