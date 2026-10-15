grammar: dict = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}

non_terminals_set = set(grammar)

first_set = {non_terminal: set() for non_terminal in grammar}

follow_set = {non_terminal: set() for non_terminal in grammar}


def is_non_terminal(symbol: str):
    return symbol in non_terminals_set

def compute_first_set():
    changed = True
    while changed: # keep going until the sets don't change anymore
        changed = False
        for non_terminal in reversed(list(grammar)): # go through all the non terminals
            rules = grammar.get(non_terminal)
            for derivation in rules: # go through all the derivations of a certain non terminal
                first_symbol = derivation[0]
                if not is_non_terminal(first_symbol): # if first symbol is non-terminal add to first set
                    first_set[non_terminal].add(first_symbol)
                    changed = True
                else: # if the symbol is a non-terminal
                    print(first_set[first_symbol])
                    print(first_set[non_terminal])
                    first_set[non_terminal].union(first_set[first_symbol])
                    changed = True

                

def compute_follow_set():
    pass


compute_first_set()
print(first_set)