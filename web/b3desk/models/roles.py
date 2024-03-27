from enum import Enum


class Role(Enum):
    attendee = "attendee"
    moderator = "moderator"
    authenticated = "authenticated"
