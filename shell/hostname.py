from nailpolish import pink, purple, reset


def host_name():
    import os

    user = os.getenv("USER", "user")
    host = os.uname().nodename
    return f"{pink}{user}{purple}@{pink}{host}{reset}"


if __name__ == "__main__":
    print(host_name())
