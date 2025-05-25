from App import EntityGroup


class Entity(EntityGroup):
    def __init__(self, app_handler, size, timer_group=1, update_count_offset=0):
        super().__init__(app_handler, size)
        self.timer_group = timer_group
        self.is_alive = True

    def process(self):
        pass

class EntityManager:
    def __init__(self, max_modulo=60):
        self.entities = EntityList()
        self.max_modulo = max_modulo
        self.frame_counter = 0

    def update(self):
        if self.frame_counter >= self.max_modulo:
            self.frame_counter = 0

        for modulo, entity_list in self.entities.items():
            local_counter = 0
            local_modulo = self.frame_counter % modulo
            for entity in entity_list:
                entity_modulo = local_counter % modulo
                local_counter += 1
                if entity_modulo == local_modulo:
                    entity.process()
        self.frame_counter += 1

    def add(self, entity):
        self.entities[entity.timer_group].append(entity)


class EntityList:
    def __init__(self):
        self.entities = {}

    def __getitem__(self, item):
        if self.entities.get(item):
            return self.entities.get(item)
        return []

    def items(self):
        return self.entities.items()

