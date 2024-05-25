class LyricsNotFoundException(Exception):
    def __init__(self, status_code=404, message="Lyrics does not exist"):
        self.status_code = status_code
        self.message = message


class MusixmatchException(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
