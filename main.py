import sys
from syntax.grammar import Grammar
from lexer.lexer import Lexer
from syntax.code_generator_script import ASDR_generator
from exceptions.custom_exceptions import *
from syntax.ASDR import ASDR



grammar1: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}


grammar2: dict[str, list[list[str]]] = {
    "S": [["A", "B","C"]],
    "A": [["a"],["ε"]],
    "B": [["b"], ["ε"]],
    "C": [["c"]]
}



if __name__ == "__main__":
    myGrammar = Grammar(grammar1)
    myGrammar.process_grammar()
    if not myGrammar.check_LL1_condition():
        print("Cannot procede. Grammar is not LL1")
        exit()
    ASDR_generator(myGrammar).generate()
    data = sys.stdin.read()
    lexer = Lexer(data)
    try:
        parser = ASDR(lexer)
        parser.main()
    except SyntacticalError as e:
        print(f"Syntactical error: {e.message}")
        exit()


