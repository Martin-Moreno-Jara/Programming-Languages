class Grammar():
    """
    Implementation class for a grammar object.
    It contains receives the grammar and offers
    the necessary calculations for the syntactial analyzer
    """

    def __init__(self,grammar):
        self.grammar:dict[str, list[list[str]]] = grammar
        self.non_terminals_set:set[str] = set(grammar)
        self.first: dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}
        self.follow:dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}
        self.predict:dict[str, list[set[str]]] = {non_terminal: [] for non_terminal in grammar}
        self.EPS:str = "ε"
        self.END:str = "$"

    def first_of_sequence(self,derivations: list[str]):

        seq_first = set()
        terminal_found = False
        for i in range(len(derivations)):
            symbol = derivations[i]
            if not symbol in self.non_terminals_set or symbol == self.EPS: # if terminal or "ε", add directly and break the cycle
                seq_first.add(symbol)
                terminal_found = True
                break
            else: # If the symbol is a non-terminal itself
                seq_first = seq_first| (self.first[symbol] - {"ε"})  # join with first(symbol) - ε
                if not self.EPS in self.first[symbol]: #if the derived non-terminal is not nullable, the search can end
                    terminal_found = True
                    break
        if not terminal_found: seq_first.add(self.EPS) # if all derivable non-terminals are nullable, A produces "ε" as well
        return seq_first
