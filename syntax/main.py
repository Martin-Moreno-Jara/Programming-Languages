
grammar: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}

"""
grammar: dict[str, list[list[str]]] = {
    "S": [["A", "B","C"]],
    "A": [["a"],["ε"]],
    "B": [["b"], ["ε"]],
    "C": [["c"]]
}
"""
non_terminals_set: set[str] = set(grammar)

first: dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}

follow: dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}

predict: dict[str, list[set[str]]] = {non_terminal: [] for non_terminal in grammar}



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


def compute_follow_set(
    grammar: dict[str, list[list[str]]],
    first: dict[str, set[str]],
    follow: dict[str, set[str]],
    non_terminals_set: set[str]) -> None:

    is_first_item = True
    while True:
        num_before = sum(len(s) for s in follow.values())
        for A, alpha in grammar.items():
            if is_first_item: # Add the $ end marker to the start symbol by default
                follow[A].add("$") 
                is_first_item = False

            for derivation in alpha: # go through all the derivations of a non terminal A
                for i in range(len(derivation)): # go through all the symbols of each derivation
                    if derivation[i] in non_terminals_set: # ignore terminals and ε
                        B = derivation[i]
                        if i+1 >= len(derivation): # if there are no symbols after B, follow(B) U follow(A) 
                            follow[B] = follow[B]|follow[A]
                            break
                        # get the first of sequence of the sequence following the non-terminal B
                        beta = derivation[i+1:] #
                        seq = first_of_sequence(beta,first,non_terminals_set)
                        follow[B] = follow[B]|(seq - {"ε"})  
                        if "ε" in seq:
                            follow[B] = follow[B]|follow[A]

        if num_before == sum(len(s) for s in follow.values()): 
            break 

def compute_predict_set(grammar: dict[str, list[list[str]]],
                        predict: dict[str, list[set[str]]],
                        first: dict[str, set[str]],
                        follow: dict[str, set[str]],
                        non_terminals_set: set[str]):
    for A, alternatives in grammar.items():
        for derivation in alternatives:
            first_symbol = derivation[0]
            if first_symbol == "ε": # if the production is nullable, add follow
                predict[A].append(follow[A])
            elif not first_symbol in non_terminals_set: # if the production is terminal, add it directly
                predict[A].append({first_symbol})
            else: # it derives a non-terminal
                if "ε" in first[first_symbol]: # if the non-terminal is nullable, add first of that symbol follow of the next 
                    print(first_symbol)
                    print(follow[first_symbol])
                    predict[A].append( (first[first_symbol] - {"ε"}) | follow[first_symbol])
                else: predict[A].append(first[first_symbol] - {"ε"}) # The non-terminal is not nullable

if __name__ == "__main__":
    compute_first_set(grammar, first, non_terminals_set)
    compute_follow_set(grammar,first,follow,non_terminals_set)
    compute_predict_set(grammar,predict,first,follow,non_terminals_set)
    for pred in predict.items():
        print(pred)
    #for NT, T in follow.items():
     #   print(NT, T)
