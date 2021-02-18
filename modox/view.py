

import lx
import lxu
import modo


class ViewUtils(object):

    MAX_VIEWPORT_WIDTH = 16384
    MAX_VIEWPORT_HEIGHT = 8192

    @classmethod
    def get3DPositionFromMouseOver3DView(cls):
        """ Gets 3d position from under mouse in 3d view.
        
        Due to the way viewport service work this can still return some
        position even if mouse is not really over a 3d viewport but over
        some other part of MODO UI. Go figure.

        Returns
        -------
        modo.Vector3, None
            None is returned when mouse is not over valid 3d view.
            Note that in MODO some parts of UI work as 3d view even though
            they are not in user's sense (script editor, info panel at the bottom of layout).
        """
        viewService = lx.service.View3Dport()
        mouseView, x, y = viewService.Mouse()

        # Some views that are cleary not model views but still return valid index
        # and space will return fixed 0,0 coordinates.
        # We used that to further filter out invalid view.
        if x <= 0 or y <= 0:
            return None

        # It may also happen that coordinates are ridiculously big.
        # The numbers here are arbitrary, I'm setting it to 16K horizontally and 8k vertically.
        # It should be enough for some time.
        if x >= cls.MAX_VIEWPORT_WIDTH or y >= cls.MAX_VIEWPORT_HEIGHT:
            return None

        # Index -1 means no 3d view but it really happens rarely that -1 is returned
        # for whatever reason. Most of MODO UI still returns 0 or other valid number.
        # It could be because of QT view qualifying as model 3d view?
        # So this is initial check only, it works poorly.
        if mouseView < 0:
            return None
    
        # We need to initialise the view and check if it's really a valid 3d view.
        # The intialisation will fail if mouse is not over 3d view.
        # That's the best way to check if we're really over 3d view.
        try:
            view = lx.object.View3D(viewService.View(mouseView))
        except IndexError:
            return None
    
        # Confirm the space, 3d view is of MO3D type.
        space = lxu.decodeID4(view.Space())
        if space != 'MO3D':
            return None
    
        # Pos can also be None in some cases.
        pos = lx.eval("query view3dservice mouse.pos ?")
        if pos is None:
            return None
        return modo.Vector3(pos)