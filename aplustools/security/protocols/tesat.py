def _step_through(dic):
    curr_dict = dic
    while True:
        try:
            key, value = next(iter(curr_dict.items()))
            yield key
            curr_dict = value
        except StopIteration:
            break


def _get_all(levels):
    curr_config = []
    for level in levels:
        curr_config.append(level[0])

    all_getter = ["table", "column", "row"][len(curr_config)]
    print(all_getter)


encryption_config = {"table1": {"ALL": {}}}


levels = []
for config, level in zip(_step_through(encryption_config), ["table", "column", "row"]):
    if isinstance(config, tuple):
        levels.append((config, level))
    else:
        levels.append((config, level) if config != "ALL" else (_get_all(levels), level))

print(levels)
