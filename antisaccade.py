#!/usr/bin/env python

from __future__ import division
from random import randrange, choice, sample
import socket
import argparse
import pygame
import math
import gc
import sys
import time

class World(object):
    """Task Environment"""
    
    def __init__(self, args):
        super(World, self).__init__()
        pygame.mouse.set_visible(False)
        if args.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((1024, 768), 0)
        width,height = self.screen.get_size()
        self.center_x = width/2
        self.center_y = height/2
        self.offsets = [self.center_x - width/3, self.center_x + width/3]
        self.worldsurf = self.screen.copy()
        self.worldsurf_rect = self.worldsurf.get_rect()
        obj_width = int(self.center_y / 10)
        self.obj_widths = [int(math.floor(obj_width*.5)), obj_width, int(math.ceil(obj_width*1.5))]
        self.arrow_fonts = [pygame.font.Font("ARROW_FONTS.ttf", self.obj_widths[0]),
                            pygame.font.Font("ARROW_FONTS.ttf", self.obj_widths[1]),
                            pygame.font.Font("ARROW_FONTS.ttf", self.obj_widths[2])]
        self.arrows = [u'\uf045',u'\uf046',u'\uf047',u'\uf048'] # Right, Up, Left, Down
        self.clock = pygame.time.Clock()
        self.accuracy = []
        
        self.EVENT_SHOW_CUE = pygame.USEREVENT + 1
        self.EVENT_SHOW_ARROW = pygame.USEREVENT + 2
        self.EVENT_SHOW_MASK = pygame.USEREVENT + 3
        
    def get_fixation_interval(self):
        return randrange(1500,3500,1)
    
    def draw_arrow(self, type, size, x):
         arrow = self.arrow_fonts[size].render(self.arrows[type], True, (255,255,0))
         arrow_rect = arrow.get_rect()
         arrow_rect.centerx = x
         arrow_rect.centery = self.center_y
         self.worldsurf.blit(arrow, arrow_rect)

    def draw_mask(self, x):
        pygame.draw.rect(self.worldsurf, (0,0,255), (x-self.obj_widths[2]/2,self.center_y-self.obj_widths[2]/2,self.obj_widths[2],self.obj_widths[2]),0)
        
    def draw_cue(self, x):
        pygame.draw.rect(self.worldsurf, (255,255,0), (x-self.obj_widths[2]/2,self.center_y-self.obj_widths[2]/2,self.obj_widths[2],self.obj_widths[2]),0)
        
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
                    if len(self.accuracy)>1:
                        mean = sum(self.accuracy)/len(self.accuracy)
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
                elif self.state > -1 and self.state < 4:
                    self.state += 1
                return True
            elif event.type == self.EVENT_SHOW_CUE:
                pygame.time.set_timer(self.EVENT_SHOW_CUE, 0)
                self.state = 2
                pygame.time.set_timer(self.EVENT_SHOW_ARROW, 400)
            elif event.type == self.EVENT_SHOW_ARROW:
                pygame.time.set_timer(self.EVENT_SHOW_ARROW, 0)
                self.state = 3
                pygame.time.set_timer(self.EVENT_SHOW_MASK, 150)
            elif event.type == self.EVENT_SHOW_MASK:
                pygame.time.set_timer(self.EVENT_SHOW_MASK, 0)
                self.state = 4
                    
    def draw_world(self):
        self.clear()
        if self.state == 1:
            self.draw_fixation_cross()
        elif self.state == 2:
            self.draw_cue(self.loc1)
        elif self.state == 3:
            self.draw_arrow(self.answer, self.size, self.loc2)
        elif self.state == 4:
            self.draw_mask(self.loc2)
        self.update_world()
        
    def generate_trial(self):
        self.loc1, self.loc2 = sample(self.offsets,2)
        self.answer = choice([2,1,0])
        self.size = choice([2,1,0])
        
    def show_intro(self):
        self.clear()
        intro = pygame.font.Font(None, 24).render("Press Any Key To Begin", True, (255,255,255))
        intro_rect = intro.get_rect()
        intro_rect.centerx = self.center_x
        intro_rect.centery = self.center_y
        self.worldsurf.blit(intro, intro_rect)
        self.update_world()
    
    def run(self):
        self.state = -1
        self.show_intro()
        while not self.process_events(): pass
        self.state = 0
        while True:
            if self.state == 0:
                self.generate_trial()
                self.state = 1
                pygame.time.set_timer(self.EVENT_SHOW_CUE, self.get_fixation_interval())
            self.clock.tick(30)
            self.draw_world()
            self.process_events()

def main(args):
    w = World(args)
    while True:
        w.run()

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-F', '--fullscreen', action="store_true", dest="fullscreen", help='Run in fullscreen mode.')
    parser.add_argument('-e', '--eyetracker', action="store", dest="eyetracker", help='Use eyetracker.')
    args = parser.parse_args()
    
    if args.eyetracker:
        try:
            socket.inet_aton(args.eyetracker)
            from eyegaze import *
        except socket.error:
            print 'Invalid IP address.'
            sys.exit()
            
    gc.disable()
    pygame.display.init()
    pygame.font.init()
    main(args)