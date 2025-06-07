# collection of ingredients
class Dish:
    def __init__(self, row):
        self.uuid = row['uuid']
        self.title = row['title']
        self.description = row['description']