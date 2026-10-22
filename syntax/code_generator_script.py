from grammar import Grammar
class NotLL1Error(Exception):
    """
    Custom exception class to raise when the given grammar is not LL1
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message



grammar1: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}
try:
    myGrammar = Grammar(grammar1)
    myGrammar.process_grammar()
    if not myGrammar.check_LL1_condition():
        raise NotLL1Error("Grammar is not LL1. Can't proceed")
    print("grammar processed")
except NotLL1Error as e:
    print(e.message)
    exit()