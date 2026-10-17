grammar: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}

non_terminals_set: set[str] = set(grammar)

first: dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}

follow = {non_terminal: set() for non_terminal in grammar}



def first_of_sequence(
    derivations: list[str],
    first: dict[str, set[str]],
    non_terminals_set: set[str]) -> set[str]:

    seq_first = set()
    terminal_found = False
    for i in range(len(derivations)):
        symbol = derivations[i]
        if not symbol in non_terminals_set or symbol == "ε": # if terminal or "ε", add directly and break the cycle
            seq_first.add(symbol)
            terminal_found = True
            break
        else: # If the symbol is a non-terminal itself
            seq_first = seq_first| (first[symbol] - {"ε"})  # join with first(symbol) - ε
            if not "ε" in first[symbol]: #if the derived non-terminal is not nullable, the search can end
                terminal_found = True
                break
    if not terminal_found: seq_first.add("ε") # if all derivable non-terminals are nullable, A produces "ε" as well
    return seq_first


def compute_first_set(
    grammar: dict[str, list[list[str]]],
    first: dict[str, set[str]],
    non_terminals_set: set[str]) -> None:

    while True:
        num_before = sum(len(s) for s in first.values())
        for A, alpha in reversed(grammar.items()):
            for derivation in alpha:
                seq = first_of_sequence(derivation, first, non_terminals_set)
                first[A]= first[A]|seq
        if num_before == sum(len(s) for s in first.values()): 
           break


def compute_follow_set():
    pass


if __name__ == "__main__":
    compute_first_set(grammar, first, non_terminals_set)
    for NT, T in first.items():
        print(NT, T)
