class CantGetInitializedObjectError(Exception):
    def __init__(self, object_name: str):
        self.object_name = object_name

    def __str__(self):
        return f"Can't get initialized object: {self.object_name}"
