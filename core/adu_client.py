# ADU interface wrapper
class ADUClient:
    def __init__(self):
        self.ready = False  # set True when DLL wired

    def action(self, name: str):
        # map to DLL calls later
        return False
