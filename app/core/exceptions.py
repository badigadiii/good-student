class LectureBotError(Exception):
    pass


class LectureClientError(LectureBotError):
    pass


class LectureJoinError(LectureClientError):
    pass
