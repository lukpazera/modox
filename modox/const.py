
import lx

class ItemVisible(object):
    """ Item visibility has 4 possible states.
    """
    DEFAULT = 0
    YES = 1
    NO = 2
    NO_CHILDREN = 3

class ItemType(object):
    WEIGHT_CONTAINER = "weightContainer"
    DEFORM_FOLDER = "deformFolder"
    IK_23BAR_SOLVER = "cmIK2Bar3Bar"
    GROUP = "group"
    GROUP_LOCATOR = "groupLocator"

class TransformType(object):
    POSITION = 'position'
    ROTATION = 'rotation'
    SCALE = 'scale'

class Notifier(object):
    SELECT_ITEM_DISABLE = ('select.event', 'item element+d')
    SELECT_ITEM_DATATYPE = ('select.event', 'item element+t')
    SELECT_VMAP_DISABLE = ('select.event', 'vmap element+d')
    
class FormCommandList(object):
    """ Form command list special mark ups.
    
    DIVIDER adds a simple line divider.
    However, if you add a label to the divider it becomes a labelled divider in the form.
    """
    DIVIDER = '- '

class VertexMapTransferMethod(object):
    RAYCAST = "raycast"
    DISTANCE = "distance"

class ChannelType(object):
    NONE = 0
    INTEGER = 1
    FLOAT = 2
    GRADIENT = 3
    STORAGE = 4
    EVAL = 5