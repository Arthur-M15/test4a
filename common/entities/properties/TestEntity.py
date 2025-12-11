import common.entities.Entity_c3 as CythonEntity


class TestEntityPy(CythonEntity.TestEntity):
    def __init__(self, app_handler, entity_manager, coord_x, coord_y):
        CythonEntity.TestEntity.__init__(self, app_handler, entity_manager, coord_x, coord_y,
                                         is_moving=True)
        self.draw_img = False
