from nailpolish import PINK, PURPLE, RESET


def host_name():
    import os

    user = os.getenv("USER", "user")
    host = os.uname().nodename
    return f"{PINK}{user}{PURPLE}@{PINK}{host}{RESET}"


if __name__ == "__main__":
    print(host_name())
