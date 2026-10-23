class Grammar():
    """
    Implementation class for a grammar object.
    It contains receives the grammar and offers
    the necessary calculations for the syntactial analyzer
    """

    def __init__(self,grammar):
        """
        
        """
        self.grammar:dict[str, list[list[str]]] = grammar
        self.non_terminals_set:set[str] = set(grammar)
        self.first: dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}
        self.follow:dict[str, set[str]] = {non_terminal: set() for non_terminal in grammar}
        self.predict:dict[str, list[set[str]]] = {non_terminal: [] for non_terminal in grammar}
        self.EPS:str = "ε"
        self.END:str = "$"

    def get_predict_set(self):
        return self.predict

    def get_grammar(self):
        return self.grammar

    def get_initial_symbol(self):
        first = ""
        for A in self.grammar:
            first= A
            break
        return first
    
    def first_of_sequence(self,derivations: list[str]):
        """
        
        """

        seq_first = set()
        terminal_found = False
        for i in range(len(derivations)):
            symbol = derivations[i]
            if not symbol in self.non_terminals_set or symbol == self.EPS: # if terminal or "ε", add directly and break the cycle
                seq_first.add(symbol)
                terminal_found = True
                break
            else: # If the symbol is a non-terminal itself
                seq_first = seq_first| (self.first[symbol] - {self.EPS})  # join with first(symbol) - ε
                if not self.EPS in self.first[symbol]: #if the derived non-terminal is not nullable, the search can end
                    terminal_found = True
                    break
        if not terminal_found: seq_first.add(self.EPS) # if all derivable non-terminals are nullable, A produces "ε" as well
        return seq_first

    def compute_first_set(self) -> None:
        while True:
            num_before = sum(len(s) for s in self.first.values())
            for A, alpha in reversed(self.grammar.items()):
                for derivation in alpha:
                    seq = self.first_of_sequence(derivation)
                    self.first[A]= self.first[A]|seq
            if num_before == sum(len(s) for s in self.first.values()): 
                break


    def compute_follow_set(self) -> None:
        is_first_item = True
        while True:
            num_before = sum(len(s) for s in self.follow.values())
            for A, alpha in self.grammar.items():
                if is_first_item: # Add the $ end marker to the start symbol by default
                    self.follow[A].add(self.END) 
                    is_first_item = False

                for derivation in alpha: # go through all the derivations of a non terminal A
                    for i in range(len(derivation)): # go through all the symbols of each derivation
                        if derivation[i] in self.non_terminals_set: # ignore terminals and ε
                            B = derivation[i]
                            if i+1 >= len(derivation): # if there are no symbols after B, follow(B) U follow(A) 
                                self.follow[B] = self.follow[B]|self.follow[A]
                                break
                            # get the first of sequence of the sequence following the non-terminal B
                            beta = derivation[i+1:] #
                            seq = self.first_of_sequence(beta)
                            self.follow[B] = self.follow[B]|(seq - {self.EPS})  
                            if self.EPS in seq:
                                self.follow[B] = self.follow[B]|self.follow[A]

            if num_before == sum(len(s) for s in self.follow.values()): 
                break 

    def compute_predict_set(self):
    
        for A, alternatives in self.grammar.items():
            for derivation in alternatives:
                fa = self.first_of_sequence(derivation)
                #print(f"{A} -> {derivation} ----- {fa}")
                if self.EPS in fa:
                    fa = (fa-{self.EPS})|self.follow[A] 
                    self.predict[A].append(fa)
                else:
                    self.predict[A].append(fa-{self.EPS})

    def check_LL1_condition(self):
        for A, pred_sets in self.predict.items():
            check_set = set()
            for pred in pred_sets:
                if not check_set.isdisjoint(pred): return False
                else: check_set = check_set|pred 
        return True

    def process_grammar(self):
        self.compute_first_set()
        self.compute_follow_set()
        self.compute_predict_set()
