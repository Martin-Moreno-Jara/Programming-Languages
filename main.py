import sys
from syntax.grammar import Grammar
from lexer.lexer import Lexer
from syntax.code_generator_script import ASDR_generator
from exceptions.custom_exceptions import *



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

grammar3: dict[str, list[list[str]]] = {
    "S": [["A", "B","C"]],
    "A": [["tnk_str"],["ε"]],
    "B": [["id"], ["ε"]],
    "C": [["tkn_num"],["ε"]]
}

final_grammar: dict[str, list[list[str]]] = {
    "CHUNK": [["VARDEC"]],
    "VARDEC": [["id","tkn_assign","DATATYPE"]],
    "DATATYPE": [["tkn_str"], ["tkn_num"], ["id"]]
}

if __name__ == "__main__":
    myGrammar = Grammar(final_grammar)
    myGrammar.process_grammar()
    if not myGrammar.check_LL1_condition():
        print("Cannot procede. Grammar is not LL1")
        exit()
    ASDR_generator(myGrammar).generate()
    from syntax.ASDR import ASDR
    data = sys.stdin.read()
    lexer = Lexer(data)
    try:
        parser = ASDR(lexer)
        parser.main()
        print("El analisis sintactico ha finalizado exitosamente.")
    except SyntacticalError as e:
        print(f"error: {e.message}")
        exit()


