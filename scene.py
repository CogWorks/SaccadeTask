from pyglet.event import EventDispatcher
from cocos.scene import Scene as CocosScene

class Scene(CocosScene, EventDispatcher):

    def __init__(self, *args, **kwargs):
        super(Scene, self).__init__(*args, **kwargs)
