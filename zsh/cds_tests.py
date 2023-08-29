from cds_helper import fuzzy_cd


def custom_path_func(path):
    dir_structure = {
        "/": ["work", "personal"],
        "/work": ["gitlab"],
        "/work/gitlab": ["acme-corp"],
        "/work/gitlab/acme-corp": ["project-a", "project-b"],
        "/personal": ["github"],
        "/personal/github": ["alexogeny"],
        "/personal/github/alexogeny": ["skunkworks"],
    }
    return dir_structure.get(path, [])


def test_exact_match():
    assert (
        fuzzy_cd("work/gitlab/acme-corp/project-a", custom_path_func)
        == "/work/gitlab/acme-corp/project-a"
    )


def test_sequence_match():
    assert (
        fuzzy_cd("w/gl/amc/pa", custom_path_func) == "/work/gitlab/acme-corp/project-a"
    )


def test_beginning_match():
    assert (
        fuzzy_cd("wo/git/acme/pro", custom_path_func)
        == "/work/gitlab/acme-corp/project-a"
    )


def test_no_match():
    assert fuzzy_cd("no/match/here", custom_path_func) == ""


if __name__ == "__main__":
    test_exact_match()
    test_sequence_match()
    test_beginning_match()
    test_no_match()
    print("All tests passed!")
