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

        self.args = args
        
        self.eg = None
        if self.args.eyetracker:
            self.eg = EyeGaze()
            msg = self.eg.connect(args.eyetracker)
            if msg:
                print msg
                sys.exit()
        
        pygame.mouse.set_visible(False)
        if self.args.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((1024, 768), 0)
        self.width,self.height = self.screen.get_size()
        self.center_x = int(self.width/2)
        self.center_y = int(self.height/2)
        self.offset = int(self.width/3)
        self.offsets = [int(self.center_x - self.offset), int(self.center_x + self.offset)]
        self.worldsurf = self.screen.copy()
        self.worldsurf_rect = self.worldsurf.get_rect()
        obj_width = int(self.center_y * self.args.arrowsize)
        self.obj_widths = [obj_width, int(math.ceil(obj_width*1.5)), int(math.ceil(obj_width*2))]
        self.arrow_font = pygame.font.Font("DTPDingbats.ttf", self.obj_widths[0])
        self.arrows = ['C','B','D']
        self.arrow_text = ['>','^','<']
        self.clock = pygame.time.Clock()
        self.accuracy = []

        self.EVENT_SHOW_CUE = pygame.USEREVENT + 1
        self.EVENT_SHOW_ARROW = pygame.USEREVENT + 2
        self.EVENT_SHOW_MASK = pygame.USEREVENT + 3

        if self.args.logfile:
            self.output = open(args.logfile, 'w')
        else:
            self.output = sys.stdout

    def get_fixation_interval(self):
        return randrange(1500,3500,1)

    def draw_arrow(self, type, size, x):
         arrow = self.arrow_font.render(self.arrows[type], True, (255,255,255))
         arrow_rect = arrow.get_rect()
         arrow_rect.centerx = x
         arrow_rect.centery = self.center_y
         self.worldsurf.blit(arrow, arrow_rect)

    def draw_mask(self, x):
        pygame.draw.rect(self.worldsurf, (128,128,128), (x-self.obj_widths[2]*.6,self.center_y-self.obj_widths[2]*.6,self.obj_widths[2]*1.2,self.obj_widths[2]*1.2),0)

    def draw_cue(self, x, size):
        pygame.draw.rect(self.worldsurf, (255,255,255), (x-size/2,self.center_y-size/2,size,size),0)

    def draw_fixation_cross(self):
        cross_radius = self.center_y / 18
        pygame.draw.line(self.worldsurf, self.fix_color, (self.center_x-cross_radius,self.center_y), (self.center_x+cross_radius, self.center_y), 4)
        pygame.draw.line(self.worldsurf, self.fix_color, (self.center_x,self.center_y-cross_radius), (self.center_x, self.center_y+cross_radius), 4)

    def clear(self):
        self.worldsurf.fill((0,0,0))

    def update_world(self):
        self.screen.blit(self.worldsurf, self.worldsurf_rect)
        pygame.display.flip()

    def process_events(self):
        ret = False
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if len(self.accuracy)>0:
                        self.do_stats()
                    self.cleanup()
                elif self.state == 5:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_UP or event.key == pygame.K_RIGHT:
                        rt = pygame.time.get_ticks() - self.target_time
                        cue_side = 'left'
                        if self.loc1 > self.center_x:
                            cue_side = 'right'
                        result = [self.center_x, self.center_y, self.offset, self.obj_widths[self.size], cue_side, self.mask_time-self.target_time, self.arrow_text[self.answer]]
                        if event.key == pygame.K_LEFT:
                            result.append('<')
                            if self.answer == 2:
                                result.append(1)
                            else:
                                result.append(0)
                        elif event.key == pygame.K_UP:
                            result.append('^')
                            if self.answer == 1:
                                result.append(1)
                            else:
                                result.append(0)
                        elif event.key == pygame.K_RIGHT:
                            result.append('>')
                            if self.answer == 0:
                                result.append(1)
                            else:
                                result.append(0)
                        result.append(rt)
                        self.state = 0
                        self.output.write("%d\t%d\t%d\t%d\t%s\t%d\t%s\t%s\t%d\t%d\n" % tuple(result))
                        self.accuracy.append(result)
                ret = True
            elif event.type == self.EVENT_SHOW_CUE:
                pygame.time.set_timer(self.EVENT_SHOW_CUE, 0)
                self.state = 3
                pygame.time.set_timer(self.EVENT_SHOW_ARROW, 400)
            elif event.type == self.EVENT_SHOW_ARROW:
                pygame.time.set_timer(self.EVENT_SHOW_ARROW, 0)
                self.state = 4
                pygame.time.set_timer(self.EVENT_SHOW_MASK, 150)
                self.target_time = pygame.time.get_ticks()
            elif event.type == self.EVENT_SHOW_MASK:
                pygame.time.set_timer(self.EVENT_SHOW_MASK, 0)
                self.state = 5
		self.mask_time = pygame.time.get_ticks()
        return ret

    def draw_fix(self):
        if self.eg.eg_data:
            pygame.draw.circle(self.worldsurf, (0,228,0), (int(self.eg.fix_data.fix_x), int(self.eg.fix_data.fix_y)), 5, 0)

    def draw_world(self):
        self.clear()
        if self.state == 1 or self.state == 2:
            self.draw_fixation_cross()
        elif self.state == 3:
            self.draw_cue(self.loc1, self.obj_widths[self.size])
        elif self.state == 4:
            self.draw_arrow(self.answer, self.obj_widths[0], self.loc2)
        elif self.state == 5:
            self.draw_mask(self.loc2)
        if self.eg and self.args.showfixation:
            self.draw_fix()
        self.update_world()

    def generate_trial(self):
        self.loc1, self.loc2 = sample(self.offsets,2)
        self.answer = choice([2,1,0])
        self.size = choice([2,1,0])
        self.fix_color = (255,255,0)

    def show_intro(self):

        self.clear()
        intro = pygame.font.Font(None, 24).render("Press Any Key To Begin", True, (255,255,255))
        intro_rect = intro.get_rect()
        intro_rect.centerx = self.center_x
        intro_rect.centery = self.center_y
        self.worldsurf.blit(intro, intro_rect)
        self.update_world()

    def do_stats(self):
        pass

    def run(self):
        self.state = -1
        self.show_intro()
        while not self.process_events(): pass
        if self.eg:
            self.eg.calibrate(self.screen)  
	    self.eg.data_start()
        self.state = 0
        if self.eg:
            self.output.write('center_x\tcenter_y\toffset\tcue_size\tcue_side\ttarget_time\ttarget\tresponse\tcorrect\trt\t1st_saccade_direction\t1st_saccade_latency\n')
        else:
            self.output.write('center_x\tcenter_y\toffset\tcue_size\tcue_side\ttarget_time\ttarget\tresponse\tcorrect\trt\n')
        while True:
            if self.state == 0:
                self.generate_trial()
                if self.eg:
                    self.state = 1
                else:
                    self.state = 2
                    pygame.time.set_timer(self.EVENT_SHOW_CUE, self.get_fixation_interval())
            elif self.state == 1:
                if self.eg.fix_data:
                    xdiff = abs(self.eg.fix_data.fix_x-self.center_x)
                    ydiff = abs(self.eg.fix_data.fix_y-self.center_y)
                    if xdiff <= self.center_y / 16 and ydiff <= self.center_y / 16:
                        self.fix_color = (0,255,0)
                        if self.eg.fix_data.fix_duration > 25: # About 300ms
                            self.state = 2
                            pygame.time.set_timer(self.EVENT_SHOW_CUE, self.get_fixation_interval())
                else:
                    self.fix_color = (255,255,0)
            elif self.state == 2 and self.eg:
                if self.eg.fix_data:
                    xdiff = abs(self.eg.fix_data.fix_x-self.center_x)
                    ydiff = abs(self.eg.fix_data.fix_y-self.center_y)
                    if xdiff > self.center_y / 16 or ydiff > self.center_y / 16:
                        sys.stderr.write('False start, resetting trial.')
                        pygame.time.set_timer(self.EVENT_SHOW_CUE, 0)
                        self.state = 1
                        self.fix_color = (255,0,0)
                elif not self.eg.eg_data.gaze_found:
                    sys.stderr.write('Lost gaze, resetting trial.')
                    pygame.time.set_timer(self.EVENT_SHOW_CUE, 0)
                    self.state = 1
                    self.fix_color = (255,0,0)
            self.clock.tick(30)
            self.process_events()
            self.draw_world()

    def cleanup(self):
        if self.args.logfile:
            self.output.close()
        sys.exit()

def main(args):
    w = World(args)
    while True:
        w.run()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-F', '--fullscreen', action="store_true", dest="fullscreen", help='Run in fullscreen mode.')
    parser.add_argument('-l', '--log', action="store", dest="logfile", help='Pipe results to file instead of stdout.')
    parser.add_argument('-a', '--arrowsize', action="store", dest="arrowsize", default=0.07, help='Arrow size in terms of fraction of screen height.')
    
    try:
        from pycogworks.eyegaze import *
        parser.add_argument('-e', '--eyetracker', action="store", dest="eyetracker", help='Use eyetracker.')
        parser.add_argument('-f', '--fixation', action="store_true", dest="showfixation", help='Overlay fixation.')
    except ImportError:
        pass

    args = parser.parse_args()

    if args.eyetracker:
        try:
            socket.inet_aton(args.eyetracker)
        except socket.error:
            print 'Error: Invalid IP address.'
            sys.exit()
    elif args.showfixation:
        print 'Error: Must enable eyetracker for fixation overlay'
        sys.exit()

    gc.disable()
    pygame.display.init()
    pygame.font.init()
    main(args)
