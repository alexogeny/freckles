import os


def sequence_match_check(dir_name, query):
    last_index = -1
    for q in query:
        index = dir_name.find(q, last_index + 1)
        if index == -1:
            return False
        last_index = index
    return True


def find_best_match(dir_list, query):
    dir_list = [d for d in dir_list if not os.path.isfile(d)]
    exact_match = [d for d in dir_list if query.lower() == d.lower()]
    if exact_match:
        return exact_match[0]
    beginning_match = [d for d in dir_list if d.lower().startswith(query.lower())]
    if beginning_match:
        return beginning_match[0]

    sequence_match = [
        d for d in dir_list if sequence_match_check(d.lower(), query.lower())
    ]
    if sequence_match:
        return sequence_match[0]

    return None


def fuzzy_cd(query, custom_path_func=None):
    path = "/"
    if custom_path_func is None:
        path = os.path.expanduser("~")
    if not query:
        return path
    if query.startswith('.'):
        path = os.getcwd()
        if query.count('.') == 1:
            query = query[1:]
        else:
            num_levels_up = query.count('.')
            for _ in range(num_levels_up - 1):
                path = os.path.dirname(path)
            query = query[num_levels_up:]
    query_parts = query.split("/")
    for q in query_parts:
        if not q:
            continue
        dir_list = (
            os.listdir(path) if custom_path_func is None else custom_path_func(path)
        )
        match = find_best_match(dir_list, q)
        if match:
            path = os.path.join(path, match)
        else:
            return ""
    return path
