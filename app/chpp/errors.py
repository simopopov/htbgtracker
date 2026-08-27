class CHPPError(Exception):
    """A CHPP-level error (the XML error envelope), not a transport failure."""

    def __init__(self, code: int, message: str = ""):
        self.code = code
        self.message = message
        super().__init__(f"CHPP error {code}: {message}")


class NotAuthorizedByOwner(CHPPError):
    """Error 59 — owner-scoped data requested for a team the authorising user
    does not own. A normal branch: 'this trainer has not connected yet'."""


def error_for_code(code: int, message: str = "") -> CHPPError:
    if code == 59:
        return NotAuthorizedByOwner(code, message)
    return CHPPError(code, message)
