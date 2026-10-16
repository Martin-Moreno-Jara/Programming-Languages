grammar: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}

non_terminals_set: set[str] = set(grammar)

first: dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}

follow = {non_terminal: set() for non_terminal in grammar}



def first_of_sequence(
    A: str,
    derivations: list[str],
    first: dict[str, set[str]],
    non_terminals_set: set[str],
) -> None:
    for alpha in derivations: # alpha is each possible derivation of a non-terminal
        if alpha[0] == "ε": # adding ε if it is a direct derivation
            first[A].add("ε")  
        else: # terminal or non-terminal
            terminal_found = False
            for i in range(len(alpha)):
                symbol = alpha[i]
                if not symbol in non_terminals_set: # if terminal, add directly and break the cycle
                    first[A].add(symbol)
                    terminal_found = True
                    break
                else: # If the symbol is a non-terminal itself
                    first[A] = first[A] | (first[symbol] - {"ε"})  # join with first(symbol) - ε
                    if not "ε" in first[symbol]: #if the derived non-terminal is not nullable, the search can end
                        terminal_found = True
                        break
            if not terminal_found: first[A].add("ε") # if all derivable non-terminals are nullable, A produces "ε" as well


def compute_first_set(
    grammar: dict[str, list[list[str]]],
    first: dict[str, set[str]],
    non_terminals_set: set[str],
) -> None:
    is_changed = True
    while is_changed:
        is_changed = False
        first_before = first
        for A, alpha in reversed(grammar.items()):
            first_of_sequence(A, alpha, first, non_terminals_set)
        if first_before != first:
            is_changed = True


def compute_follow_set():
    pass


if __name__ == "__main__":
    compute_first_set(grammar, first, non_terminals_set)
    for NT, T in first.items():
        print(NT, T)
