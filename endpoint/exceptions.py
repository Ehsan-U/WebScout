

class DuplicateTaskException(Exception):
    def __init__(self, message='task already seen'):
        self.message = message

    def __str__(self):
        return self.message


class Task404Exception(Exception):
    def __init__(self, message='task has not enqueued yet'):
        self.message = message

    def __str__(self):
        return self.message