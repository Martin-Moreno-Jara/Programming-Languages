grammar:dict = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C", "bad"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["ε"]]
}

non_terminals_set = set(grammar)

first_set = {non_terminal:set() for non_terminal in grammar}

follow_set = {non_terminal:set() for non_terminal in grammar}

def is_non_terminal(symbol:str):
    return symbol in non_terminals_set


for non_terminal in reversed(list(grammar)):
    derivations = grammar.get(non_terminal)
    for rule in derivations:
        first_symbol = rule[0]
        if not is_non_terminal(first_symbol):
            first_set[non_terminal].add(first_symbol)

print(first_set)