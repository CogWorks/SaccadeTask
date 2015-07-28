#!/usr/bin/env python
from __future__ import division

import sys, os, platform

from random import *

import pygletreactor
pygletreactor.install()
from twisted.internet import reactor

from pyglet import font, text, clock, resource
from pyglet.window import key

from cocos.director import *
from cocos.layer import *
from cocos.sprite import *
from cocos.menu import *
from cocos.text import *
from cocos.scenes.transitions import *
from cocos.actions.interval_actions import *
from cocos.actions.base_actions import *
from cocos.actions.instant_actions import *
from cocos.batch import BatchNode
from cocos.collision_model import *
import cocos.euclid as eu
from pyglet.media import StaticSource

from util import hsv_to_rgb, screenshot
from handler import Handler
from menu import BetterMenu, BetterEntryMenuItem
from scene import Scene

from odict import OrderedDict

from pyviewx.client import iViewXClient, Dispatcher
from calibrator import CalibrationLayer, HeadPositionLayer

from pycogworks.logging import get_time, Logger, writeHistoryFile, getDateTimeStamp
from pycogworks.crypto import rin2id
from cStringIO import StringIO
import tarfile
import json

class OptionsMenu(BetterMenu):

    def __init__(self):
        super(OptionsMenu, self).__init__('Options')
        self.screen = director.get_window_size()

        ratio = self.screen[1] / self.screen[0]

        self.font_title['font_name'] = 'DejaVu Sans Mono'
        self.font_title['font_size'] = self.screen[0] / 18
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['font_name'] = 'DejaVu Sans Mono'
        self.font_item['color'] = (255, 255, 255, 255)
        self.font_item['font_size'] = self.screen[1] / 16 * ratio
        self.font_item_selected['font_name'] = 'DejaVu Sans Mono'
        self.font_item_selected['color'] = (0, 0, 255, 255)
        self.font_item_selected['font_size'] = self.screen[1] / 16 * ratio

        self.items = OrderedDict()

        self.items['seed'] = EntryMenuItem('Random Seed:', self.on_seed, director.settings['seed'])
        self.items['fps'] = ToggleMenuItem('Show FPS:', self.on_show_fps, director.show_FPS)
        self.items['fullscreen'] = ToggleMenuItem('Fullscreen:', self.on_fullscreen, director.window.fullscreen)
        self.items['eyetracker'] = ToggleMenuItem("EyeTracker:", self.on_eyetracker, director.settings['eyetracker'])
        self.items['eyetracker_ip'] = EntryMenuItem('EyeTracker IP:', self.on_eyetracker_ip, director.settings['eyetracker_ip'])
        self.items['eyetracker_in_port'] = EntryMenuItem('EyeTracker In Port:', self.on_eyetracker_in_port, director.settings['eyetracker_in_port'])
        self.items['eyetracker_out_port'] = EntryMenuItem('EyeTracker Out Port:', self.on_eyetracker_out_port, director.settings['eyetracker_out_port'])
        self.set_eyetracker_extras(director.settings['eyetracker'])

        self.create_menu(self.items.values(), zoom_in(), zoom_out())

    def on_enter(self):
        super(OptionsMenu, self).on_enter()
        self.orig_values = (director.settings['eyetracker_ip'],
                            director.settings['eyetracker_in_port'],
                            director.settings['eyetracker_out_port'])

    def on_exit(self):
        super(OptionsMenu, self).on_exit()
        new_values = (director.settings['eyetracker_ip'],
                            director.settings['eyetracker_in_port'],
                            director.settings['eyetracker_out_port'])
        if new_values != self.orig_values:
            director.scene.dispatch_event("eyetracker_info_changed")

    def on_seed(self, value):
        director.settings['seed'] = value

    def on_show_fps(self, value):
        director.show_FPS = value

    def on_fullscreen(self, value):
        screen = pyglet.window.get_platform().get_default_display().get_default_screen()
        director.window.set_fullscreen(value, screen)

    def on_experiment(self, value):
        director.settings['experiment'] = value

    def set_eyetracker_extras(self, value):
        self.items['eyetracker_ip'].visible = value
        self.items['eyetracker_in_port'].visible = value
        self.items['eyetracker_out_port'].visible = value

    def on_eyetracker(self, value):
        director.settings['eyetracker'] = value
        self.set_eyetracker_extras(value)

    def on_eyetracker_ip(self, ip):
        director.settings['eyetracker_ip'] = ip

    def on_eyetracker_in_port(self, port):
        director.settings['eyetracker_in_port'] = port

    def on_eyetracker_out_port(self, port):
        director.settings['eyetracker_out_port'] = port

    def on_quit(self):
        self.parent.switch_to(0)

class MainMenu(BetterMenu):

    def __init__(self):
        super(MainMenu, self).__init__("The Saccade Control Task")
        self.screen = director.get_window_size()

        ratio = self.screen[1] / self.screen[0]

        self.font_title['font_name'] = 'DejaVu Sans Mono'
        self.font_title['font_size'] = self.screen[0] / 22
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['font_name'] = 'DejaVu Sans Mono',
        self.font_item['color'] = (255, 255, 255, 255)
        self.font_item['font_size'] = self.screen[1] / 16 * ratio
        self.font_item_selected['font_name'] = 'DejaVu Sans Mono'
        self.font_item_selected['color'] = (0, 0, 255, 255)
        self.font_item_selected['font_size'] = self.screen[1] / 16 * ratio

        self.menu_anchor_y = 'center'
        self.menu_anchor_x = 'center'

        self.items = OrderedDict()

        self.items['mode'] = MultipleMenuItem('Mode: ', self.on_mode, director.settings['modes'], director.settings['modes'].index(director.settings['mode']))
        self.items['player'] = MultipleMenuItem('Player: ', self.on_player, director.settings['players'], director.settings['players'].index(director.settings['player']))
        self.items['start'] = MenuItem('Start', self.on_start)
        self.items['options'] = MenuItem('Options', self.on_options)
        self.items['quit'] = MenuItem('Quit', self.on_quit)

        self.create_menu(self.items.values(), zoom_in(), zoom_out())

    def on_player(self, player):
        director.settings['player'] = director.settings['players'][player]

    def on_mode(self, mode):
        director.settings['mode'] = director.settings['modes'][mode]

    def on_options(self):
        self.parent.switch_to(1)

    def on_start(self):
        if director.settings['player'] == 'Human' and director.settings['mode'] == 'Experiment':
            self.parent.switch_to(2)
        else:
            filebase = "SaccadeTask_%s" % (getDateTimeStamp())
            director.settings['filebase'] = filebase
            director.scene.dispatch_event('start_task')

    def on_quit(self):
        reactor.callFromThread(reactor.stop)

class ParticipantMenu(BetterMenu):

    def __init__(self):
        super(ParticipantMenu, self).__init__("Participant Information")
        self.screen = director.get_window_size()

        ratio = self.screen[1] / self.screen[0]

        self.font_title['font_name'] = 'DejaVu Sans Mono'
        self.font_title['font_size'] = self.screen[0] / 18
        self.font_title['color'] = (255, 255, 255, 255)

        self.font_item['font_name'] = 'DejaVu Sans Mono'
        self.font_item['color'] = (255, 255, 255, 255)
        self.font_item['font_size'] = self.screen[1] / 16 * ratio
        self.font_item_selected['font_name'] = 'DejaVu Sans Mono'
        self.font_item_selected['color'] = (0, 0, 255, 255)
        self.font_item_selected['font_size'] = self.screen[1] / 16 * ratio

        self.menu_anchor_y = 'center'
        self.menu_anchor_x = 'center'

    def on_enter(self):
        super(ParticipantMenu, self).on_enter()
        self.items = OrderedDict()
        self.items['firstname'] = BetterEntryMenuItem('First Name:', self.on_info_change, "", validator=lambda x: x.isalpha())
        self.items['lastname'] = BetterEntryMenuItem('Last Name:', self.on_info_change, "", validator=lambda x: x.isalpha())
        self.items['rin'] = BetterEntryMenuItem('RIN:', self.on_info_change, "", max_length=9, validator=lambda x: unicode(x).isnumeric())
        self.items['start'] = MenuItem('Start', self.on_start)
        self.create_menu(self.items.values(), zoom_in(), zoom_out())
        self.items['start'].visible = False

    def on_exit(self):
        super(ParticipantMenu, self).on_exit()
        for c in self.get_children(): self.remove(c)

    def on_info_change(self, *args, **kwargs):
        firstname = ''.join(self.items['firstname']._value).strip()
        lastname = ''.join(self.items['lastname']._value).strip()
        rin = ''.join(self.items['rin']._value)
        if len(firstname) > 0 and len(lastname) > 0 and len(rin) == 9:
            self.items['start'].visible = True
        else:
            self.items['start'].visible = False

    def on_start(self):
        si = {}
        si['first_name'] = ''.join(self.items['firstname']._value).strip()
        si['last_name'] = ''.join(self.items['lastname']._value).strip()
        si['rin'] = ''.join(self.items['rin']._value)
        si['encrypted_rin'], si['cipher'] = rin2id(si['rin'])
        si['timestamp'] = getDateTimeStamp()
        director.settings['si'] = si
        filebase = "SaccadeTask_%s_%s" % (si['timestamp'], si['encrypted_rin'][:8])
        director.settings['filebase'] = filebase
        writeHistoryFile("data/%s.history" % filebase, si)
        director.scene.dispatch_event('start_task')

    def on_quit(self):
        self.parent.switch_to(0)

class TaskBackground(Layer):

    def __init__(self):
        super(TaskBackground, self).__init__()
        self.screen = director.get_window_size()

    def new_trial(self, current_trial, total_trials):
        for c in self.get_children(): self.remove(c)
        if total_trials:
            self.trial_display = Label("%d of %d" % (current_trial, total_trials), position=(self.screen[0] - 10, 10), font_name='', font_size=18, bold=True, color=(128, 128, 128, 128), anchor_x='right')
        else:
            self.trial_display = Label("%d" % (current_trial), position=(self.screen[0] - 10, 10), font_name='', font_size=18, bold=True, color=(128, 128, 128, 128), anchor_x='right')
        self.add(self.trial_display)

class Task(ColorLayer, pyglet.event.EventDispatcher):

    d = Dispatcher()

    states = ["INIT", "CALIBRATE", "FIXATE", "FIXATING", "RESPOND", "FEEDBACK"]
    STATE_INIT = 0
    STATE_CALIBRATE = 1
    STATE_FIXATE = 2
    STATE_FIXATING = 3
    STATE_RESPOND = 4
    STATE_FEEDBACK = 5

    is_event_handler = True

    def __init__(self, client):
        self.screen = director.get_window_size()
        super(Task, self).__init__(168, 168, 168, 255, self.screen[0], self.screen[1])
        self.state = self.STATE_INIT
        self.client = client
        self.trial_complete = False

    def on_enter(self):
        if isinstance(director.scene, TransitionScene): return

        super(Task, self).on_enter()

        header = []

        if director.settings['mode'] == 'Experiment':
            header += ["datestamp", "encrypted_rin"]

        header += ["system_time", "mode", "trial", "state", "screen_width", "screen_height"]

        if director.settings['eyetracker'] and self.client:
            self.smi_spl_header = [
                "smi_time", "smi_type",
                "smi_sxl", "smi_sxr",
                "smi_syl", "smi_syr",
                "smi_dxl", "smi_dxr",
                "smi_dyl", "smi_dyr",
                "smi_exl", "smi_exr",
                "smi_eyl", "smi_eyr",
                "smi_ezl", "smi_ezr"
            ]
            header += self.smi_spl_header

        self.logger = Logger(header)
        self.tarfile = tarfile.open('data/%s.tar.gz' % director.settings['filebase'], mode='w:gz')

        self.left_off = Label(u'\u25CB', position=(self.width / 8, self.height / 2), font_name='DejaVu Sans Mono', font_size=24, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center')
        self.left_on = Label(u'\u25C9', position=(self.width / 8, self.height / 2), font_name='DejaVu Sans Mono', font_size=24, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center')
        self.center_off = Label(u'\u25CB', position=(self.width / 2, self.height / 2), font_name='DejaVu Sans Mono', font_size=24, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center')
        self.center_on = Label(u'\u25C9', position=(self.width / 2, self.height / 2), font_name='DejaVu Sans Mono', font_size=24, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center')
        self.right_off = Label(u'\u25CB', position=(7 * self.width / 8, self.height / 2), font_name='DejaVu Sans Mono', font_size=24, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center')
        self.right_on = Label(u'\u25C9', position=(7 * self.width / 8, self.height / 2), font_name='DejaVu Sans Mono', font_size=24, color=(0, 0, 0, 255), anchor_x='center', anchor_y='center')

        self.reset_state()
        if director.settings['eyetracker']:
            self.state = self.STATE_CALIBRATE
            self.dispatch_event("start_calibration", self.calibration_ok, self.calibration_bad)
        else:
            self.next_trial()

    def reset_state(self):
        s = int(director.settings['seed'])
        if s > 0:
            seed(s)
        self.current_trial = 0
        self.total_trials = None
        self.fake_cursor = (self.screen[0] / 2, self.screen[1] / 2)

    def calibration_ok(self):
        self.dispatch_event("stop_calibration")
        self.dispatch_event("hide_headposition")
        self.client.addDispatcher(self.d)
        self.next_trial()
        self.client.startFixationProcessing()

    def calibration_bad(self):
        self.dispatch_event("stop_calibration")
        self.logger.close(True)
        self.tarfile.close()
        director.scene.dispatch_event("show_intro_scene")

    def on_exit(self):
        if isinstance(director.scene, TransitionScene): return
        self.client.removeDispatcher(self.d)
        self.client.stopFixationProcessing()
        self.logger.close(True)
        self.tarfile.close()
        super(Task, self).on_exit()

    def next_trial(self):
        if self.current_trial == self.total_trials:
            director.scene.dispatch_event("show_intro_scene")
        else:
            self.log_extra = {
                'screen_width':self.screen[0],
                'screen_height': self.screen[1]
            }
            director.window.set_mouse_visible(False)
            for c in self.get_children():
                self.remove(c)
            self.add(self.left_off)
            self.add(self.center_off)
            self.add(self.right_off)
            self.state = self.STATE_FIXATE
            self.current_trial += 1

    def trial_done(self):
        self.next_trial()

    def show_queue(self):
        if self.state == self.STATE_FIXATING:
            self.remove(self.center_on)
            self.add(self.center_off)
            if randint(0,1):
                self.remove(self.left_off)
                self.add(self.left_on)
            else:
                self.remove(self.right_off)
                self.add(self.right_on)
            self.state = self.STATE_RESPOND

    @d.listen('ET_FIX')
    def iViewXEvent(self, inResponse):
        if self.state == self.STATE_FIXATE:
            if abs(float(inResponse[2])-self.screen[0]/2) < 100 or abs(float(inResponse[3])-self.screen[1]/2) < 100:
                if self.center_off in self.get_children():
                    self.remove(self.center_off)
                if not self.center_on in self.get_children():
                    self.add(self.center_on)
                self.state = self.STATE_FIXATING
                reactor.callLater(2+2*random(), self.show_queue)
        elif self.state == self.STATE_FIXATING:
            if not (abs(float(inResponse[2])-self.screen[0]/2) < 100 or abs(float(inResponse[3])-self.screen[1]/2) < 100):
                if self.center_on in self.get_children():
                    self.remove(self.center_on)
                if not self.center_off in self.get_children():
                    self.add(self.center_off)
                self.state = self.STATE_FIXATE

    @d.listen('ET_SPL')
    def iViewXEvent(self, inResponse):
        eyedata = {}
        eyedata.update(self.log_extra)
        for i, _ in enumerate(self.smi_spl_header):
            eyedata[self.smi_spl_header[i]] = inResponse[i]
        self.logger.write(system_time=get_time(), mode=director.settings['mode'], state=self.states[self.state],
                          trial=self.current_trial, event_source="SMI", event_type="ET_SPL", **eyedata)

    def on_mouse_press(self, x, y, buttons, modifiers):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_key_press(self, symbol, modifiers):
        if self.state <= self.STATE_CALIBRATE: return
        if symbol == key.W and (modifiers & key.MOD_ACCEL):
            self.logger.close(True)
            self.tarfile.close()
            director.scene.dispatch_event("show_intro_scene")
            True

class EyetrackerScrim(ColorLayer):

    def __init__(self):
        self.screen = director.get_window_size()
        super(EyetrackerScrim, self).__init__(0, 0, 0, 224, self.screen[0], self.screen[1])
        l = Label("Reconnecting to eyetracker...", position=(self.screen[0] / 2, self.screen[1] / 2), font_name='', font_size=32, bold=True, color=(255, 255, 255, 255), anchor_x='center', anchor_y='center')
        self.add(l)

class SaccadeTask(object):

    title = "The Williams' Search Task"

    def __init__(self):

        if not os.path.exists("data"): os.mkdir("data")

        pyglet.resource.path.append('resources')
        pyglet.resource.reindex()
        pyglet.resource.add_font('DejaVuSansMono.ttf')
        pyglet.resource.add_font('cutouts.ttf')

        director.set_show_FPS(False)
        director.init(fullscreen=True, caption=self.title, visible=True, resizable=True)

        width = director.window.width
        height = director.window.height

        director.window.set_fullscreen(False)
        director.window.set_size(int(width * .75), int(height * .75))

        director.window.pop_handlers()
        director.window.push_handlers(Handler())

        director.settings = {'seed':'1',
                             'eyetracker': True,
                             'eyetracker_ip': '127.0.0.1',
                             'eyetracker_out_port': '4444',
                             'eyetracker_in_port': '5555',
                             'player': 'Human',
                             'players': ['Human'],
                             'mode': 'Anti',
                             'modes': ['Anti', 'Pro']}
        if 'EYE_TRACKER' in os.environ:
            director.settings['eyetracker_ip'] = os.environ['EYE_TRACKER']

        self.client = None

        self.client = iViewXClient(director.settings['eyetracker_ip'], int(director.settings['eyetracker_out_port']))
        self.listener = reactor.listenUDP(int(director.settings['eyetracker_in_port']), self.client)

        if platform.system() != 'Windows':
            director.window.set_icon(pyglet.resource.image('logo.png'))
            cursor = director.window.get_system_mouse_cursor(director.window.CURSOR_HAND)
            director.window.set_mouse_cursor(cursor)

        # Intro scene and its layers
        self.introScene = Scene()

        self.mainMenu = MainMenu()
        self.optionsMenu = OptionsMenu()
        self.participantMenu = ParticipantMenu()
        self.eyetrackerScrim = EyetrackerScrim()

        self.mplxLayer = MultiplexLayer(self.mainMenu, self.optionsMenu, self.participantMenu)
        self.introScene.add(self.mplxLayer, 1)

        self.introScene.register_event_type('start_task')
        self.introScene.register_event_type('eyetracker_info_changed')
        self.introScene.push_handlers(self)

        # Task scene and its layers
        self.taskScene = Scene()

        self.taskBackgroundLayer = TaskBackground()
        self.taskLayer = Task(self.client)

        self.calibrationLayer = CalibrationLayer(self.client)
        self.calibrationLayer.register_event_type('show_headposition')
        self.calibrationLayer.register_event_type('hide_headposition')
        self.calibrationLayer.push_handlers(self)
        self.headpositionLayer = HeadPositionLayer(self.client)

        self.taskLayer.register_event_type('new_trial')
        self.taskLayer.push_handlers(self.taskBackgroundLayer)
        self.taskLayer.register_event_type('start_calibration')
        self.taskLayer.register_event_type('stop_calibration')
        self.taskLayer.register_event_type('show_headposition')
        self.taskLayer.register_event_type('hide_headposition')
        self.taskLayer.register_event_type('actr_wait_connection')
        self.taskLayer.register_event_type('actr_wait_model')
        self.taskLayer.register_event_type('actr_running')
        self.taskLayer.push_handlers(self)

        self.taskScene.add(self.taskBackgroundLayer)
        self.taskScene.add(self.taskLayer, 1)

        self.taskScene.register_event_type('show_intro_scene')
        self.taskScene.push_handlers(self)

        director.window.set_visible(True)

    def start_calibration(self, on_success, on_failure):
        self.calibrationLayer.on_success = on_success
        self.calibrationLayer.on_failure = on_failure
        self.taskScene.add(self.calibrationLayer, 2)

    def stop_calibration(self):
        self.taskScene.remove(self.calibrationLayer)

    def show_headposition(self):
        self.taskScene.add(self.headpositionLayer, 3)

    def hide_headposition(self):
        if self.headpositionLayer in self.taskScene.get_children():
            self.taskScene.remove(self.headpositionLayer)

    def eyetracker_listen(self, _):
        self.listener = reactor.listenUDP(int(director.settings['eyetracker_in_port']), self.client)
        self.introScene.remove(self.eyetrackerScrim)
        self.introScene.enable_handlers(True)

    def eyetracker_info_changed(self):
        if self.client.remoteHost != director.settings['eyetracker_ip'] or \
        self.client.remotePort != int(director.settings['eyetracker_out_port']):
            self.client.remoteHost = director.settings['eyetracker_ip']
            self.client.remotePort = int(director.settings['eyetracker_out_port'])
        else:
            self.introScene.add(self.eyetrackerScrim, 2)
            self.introScene.enable_handlers(False)
            d = self.listener.stopListening()
            d.addCallback(self.eyetracker_listen)

    def show_intro_scene(self):
        director.window.set_mouse_visible(True)
        self.mplxLayer.switch_to(0)
        director.replace(self.introScene)

    def start_task(self):
        director.window.set_mouse_visible(False)
        director.replace(SplitRowsTransition(self.taskScene))

def main():
    williams = SaccadeTask()
    williams.show_intro_scene()
    reactor.run()
