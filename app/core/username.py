import re

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")


def validate_username(username: str) -> str:
    username = username.strip().lower()

    if not USERNAME_REGEX.match(username):
        raise ValueError(
            "Username must be 3-30 characters."
            "Only letters, numbers, underscores and dots allowed"
        )
    reserved: set[str] = {"admin", "skillbae", "support", "root", "api", "me", "null"}

    if username in reserved:
        raise ValueError("This is a reserved username")

    return username
