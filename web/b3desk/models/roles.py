from enum import Enum


class Role(Enum):
    attendee = "invité"
    moderator = "modérateur"
    authenticated = "authentifié"
