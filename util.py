import colorsys

from pyglet.gl import *

from cocos.director import director

from PIL import Image

def hsv_to_rgb(h, s, v):
    return tuple(map(lambda x: int(x * 255), list(colorsys.hsv_to_rgb(h / 360., s / 100., v / 100.))))

def screenshot():
    window = director.window.get_size()
    buffer = (GLubyte * (3 * window[0] * window[1]))(0)
    glReadPixels(0, 0, window[0], window[1], GL_RGB, GL_UNSIGNED_BYTE, buffer)
    image = Image.fromstring(mode="RGB", size=(window[0], window[1]), data=buffer)
    image = image.transpose(Image.FLIP_TOP_BOTTOM)
    return image
