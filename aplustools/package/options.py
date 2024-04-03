def stuffs(people, options, solution=None, solutions=None):
    if solution is None:
        solution = []
    if solutions is None:
        solutions = []

    if len(solution) == 3:
        if set(solution) not in solutions:
            solutions.append(set(solution))
    else:
        for i in range(len(people)):
            for j in range(len(options)):
                # Check if the current pair is unique in this solution
                if people[i] not in [p for p, _ in solution] and options[j] not in [o for _, o in solution]:
                    # Recursively build the solution with the new pair
                    stuffs(options, people, solution + [(people[i], options[j])], solutions)
        # for i, person in enumerate(people):
        #     for j, option in enumerate(options):
        #         new_people, new_options = people[:], options[:]
        #         # Recursively build the solution with the new pair
        #         stuffs(new_people.remove(person) or new_people, new_options.remove(option) or new_options, solution
        #                + [(person, option)], solutions)
    return solutions


def count_solutions(solutions):
    good = middle = bad = rest = 0

    for solution in solutions:
        matches = [(p, o) for p, o in solution if o in ["jason-bad", "junifer-bad"]]
        if len(matches) == 2 and all(p in ["jason", "junifer"] for p, _ in matches):
            good += 1
        elif len(matches) >= 1 and any(p == "carl" for p, _ in matches):
            middle += 1
        elif ("jason", "dg") in solution:
            bad += 1
        else:
            rest += 1

    total = len(solutions)
    return {
        "Good": (good, good / total),
        "Middle": (middle, middle / total),
        "Bad": (bad, bad / total),
        "Rest": (rest, rest / total)
    }


my_options = ["dg", "jason-bad", "junifer-bad"]
my_people = ["carl", "jason", "junifer"]

sols = stuffs(my_people, my_options)
counts = count_solutions(sols)

for category, (count, proportion) in counts.items():
    print(f"{category}: {count} (~{proportion:.2%})")
