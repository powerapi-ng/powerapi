from smartwatts.database.base_db import BaseDB

class Stdout(BaseDB):
    def __init__(self):
        raise NotImplementedError

class Stdin:
    def __init__(self):
        raise NotImplementedError
