grammar: dict[str,list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}

non_terminals_set = set(grammar)

first = {non_terminal: set() for non_terminal in grammar}

follow = {non_terminal: set() for non_terminal in grammar}


def is_non_terminal(symbol: str):
    return symbol in non_terminals_set and symbol != "ε"

def first_of_sequence(A:str,derivations:list[str]) -> None:
    for alpha in derivations:
        first_symbol= alpha[0] 
        if first_symbol == "ε": first[A].add("ε") # adding ε if it is a direct derivation
        elif first_symbol not in non_terminals_set: first[A].add(first_symbol) # add terminal directly
        else: 
            first[A] = first[A]|(first[first_symbol] - {"ε"}) # if first symbol is not terminal, join f(A)Uf(a) - {ε}

            for i in range(len(alpha)):
                symbol = alpha[i]
                if not is_non_terminal(symbol): # If a subsequent symbol is a terminal, add it and end the processing
                    first[A].add(symbol)
                    break
                elif "ε" in first[symbol]: # If the non terminal in the derivation is nullable
                    if i+1 >= len(alpha): # if there is no more symbols after that nullable one, add ε to first of A
                        first[A].add("ε")
                    else: first[A] = first[A]|(first[alpha[i+1]] - {"ε"})
                

def compute_first_set():    
    for A,alpha in reversed(grammar.items()):
        first_of_sequence(A,alpha)

def compute_follow_set():
    pass

compute_first_set()
for NT,T in first.items():
    print(NT,T)