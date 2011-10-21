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
        
    def get_fixation_interval(self):
        return randrange(1500,3500,1)
    
    def draw_arrow(self, type, x):
         arrow = self.arrow_font.render(self.arrows[type], True, (255,255,255))
         arrow_rect = arrow.get_rect()
         arrow_rect.centerx = x
         arrow_rect.centery = self.center_y
         self.screen.blit(arrow, arrow_rect)
         pygame.display.flip()

    def draw_mask(self, x):
        pygame.draw.rect(self.worldsurf, (255,255,255), (x-self.obj_width/2,self.center_y-self.obj_width/2,self.obj_width,self.obj_width),0)
        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        pygame.display.flip()
        
    def draw_cue(self, x):
        pygame.draw.rect(self.worldsurf, (255,255,255), (x-self.obj_width/2,self.center_y-self.obj_width/2,self.obj_width,self.obj_width),0)
        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        pygame.display.flip()
        
    def draw_fixation_cross(self):
        cross_radius = self.center_y / 18
        pygame.draw.line(self.worldsurf, (255,0,0), (self.center_x-cross_radius,self.center_y), (self.center_x+cross_radius, self.center_y), 4)
        pygame.draw.line(self.worldsurf, (255,0,0), (self.center_x,self.center_y-cross_radius), (self.center_x, self.center_y+cross_radius), 4)
        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        pygame.display.flip()
        
    def clear(self):
        self.worldsurf.fill((0,0,0))
        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        pygame.display.flip()
        
    def run(self):
        loc1, loc2 = sample(self.offsets,2)
        answer = choice([2,1,0])
        self.clear()
        self.draw_fixation_cross()
        time.sleep(self.get_fixation_interval()/1000.0)
        self.clear()
        self.draw_cue(loc1)
        time.sleep(0.4)
        self.clear()
        self.draw_arrow(answer, loc2)
        time.sleep(0.15)
        self.clear()
        self.draw_mask(loc2)
        cont = True
        while cont:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        sys.exit()
                    elif event.key == pygame.K_LEFT and answer == 2:
                        print 'correct'
                    elif event.key == pygame.K_UP and answer == 1:
                        print 'correct'
                    elif event.key == pygame.K_RIGHT and answer == 0:
                        print 'correct'
                    else:
                        print 'incorrect'
                    cont = False

def main():
    w = World()
    while True:
        w.run()

if __name__ == '__main__':
    gc.disable()
    pygame.display.init()
    pygame.font.init()
    main()