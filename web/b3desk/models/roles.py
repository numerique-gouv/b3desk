from enum import StrEnum


class Role(StrEnum):
    attendee = "attendee"
    moderator = "moderator"
    authenticated = "authenticated"
