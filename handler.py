import time

from util import screenshot

from pyglet.window import key

from cocos.director import director

class Handler(object):
    def __init__(self):
        super(Handler, self).__init__()

    def on_key_press(self, symbol, modifiers):
        if symbol == key.F and (modifiers & key.MOD_ACCEL):
            director.window.set_fullscreen(not director.window.fullscreen)
            return True

        elif symbol == key.X and (modifiers & key.MOD_ACCEL):
            director.show_FPS = not director.show_FPS
            return True

        elif symbol == key.S and (modifiers & key.MOD_ACCEL):
            screenshot().save('screenshot-%d.png' % (int(time.time())))
            return True
