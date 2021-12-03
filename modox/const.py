
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
    IK_FULL_BODY = "ikFullBody"
    MATRIX_CHANNEL_EFFECT = "ceMatrix"
    MODIFIER_DYNA_PARENT = 'cmDynamicParent'
    COMMAND_REGION_POLYGON = 'cmdRegionPolygon'
    COMMAND_REGION_GESTURE = 'cmdRegionGesture'
    COMMAND_REGION_COMMAND = 'cmdRegionCommand'


class TransformType(object):
    POSITION = 'position'
    ROTATION = 'rotation'
    SCALE = 'scale'


class Notifier(object):
    SELECT_ITEM_DISABLE = ('select.event', 'item element+d')
    SELECT_ITEM_DATATYPE = ('select.event', 'item element+t')
    SELECT_ITEM_LABEL = ('select.event', 'item element+l')
    SELECT_ITEM_VALUE = ('select.event', 'item element+v')
    SELECT_TIME_DISABLE = ('select.event', 'item time+d')
    SELECT_TIME_VALUE = ('select.event', 'item time+v')
    SELECT_VMAP_DISABLE = ('select.event', 'vmap element+d')
    GRAPH_CURRENT_GROUPS_DISABLE = ('graphs.event', 'currentGroups +d')
    GRAPH_CHAN_LINKS_DISABLE = ('graphs.event', 'chanLinks +d')
    GRAPH_CHAN_LINKS_DATATYPE = ('graphs.event', 'chanLinks +t')
    GRAPH_CHAN_LINKS_VALUE = ('graphs.event', 'chanLinks +v')


class GraphName(object):
    COMMAND_REGION_GESTURE = 'cmdRegion.gesture.graph'
    COMMAND_REGION_REGION = 'cmdRegion.region.graph'
    COMMAND_REGION_ITEM_SELECTION = 'cmdRegion.item.selection.graph'


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


class TransformChannels(object):

    PositionX = 'pos.X'
    PositionY = 'pos.Y'
    PositionZ = 'pos.Z'

    RotationX = 'rot.X'
    RotationY = 'rot.Y'
    RotationZ = 'rot.Z'

    ScaleX = 'scl.X'
    ScaleY = 'scl.Y'
    ScaleZ = 'scl.Z'

    PositionAll = [PositionX, PositionY, PositionZ]
    RotationAll = [RotationX, RotationY, RotationZ]
    ScaleAll = [ScaleX, ScaleY, ScaleZ]

    All = PositionAll + RotationAll + ScaleAll


# Form (file) types
class FileForm(object):
    PRESET_ITEM = 'LXPR'
    PRESET_MESH = 'LXPM'
    PRESET_ENVIRONMENT = 'LXPE'

class PresetServerName(object):
    ITEM = '$LXP'
    MESH = '$LXL'
    ENVIRONMENT = '$LXE'

class PresetCategory(object):
    SCENEITEM = 'sceneItem'
    MESH = 'meshLayer'
    MATERIAL = 'material'
    ENVIRONMENT = 'environment'

# preset GUID - whatever it means
class PresetGuid(object):
    ITEM = 'sceneItemPresetDestination'
