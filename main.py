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
    "CHUNK": [["BLOCK"]], 
    # The block can have several statements and optionally a return statement
    "BLOCK": [["STATLIST", "RETSTAT"]],
    # A statement list can be empty, have only one, or several statements
    "STATLIST": [["STAT", "STATLIST"],["ε"]],
    "STAT": [["tkn_colon"], 
             # declaraction of variables
             ["VARLIST", "tkn_assign","EXPLIST"],
             ["LABEL"],
             ["break"],
             ["goto", "id"],
             ["DO_BLOCK_END"],
             ["while", "EXP", "DO_BLOCK_END"],
             ["repeat", "BLOCK", "until","EXP"],
             ["IFSTAT"],
             ["FORSTAT"],
             ["function","FUNCNAME","FUNCBODY"],
             ["LOCAL_DEC"],
             ["GLOBAL_DEC"]],

    "GLOBAL_DEC": [["global","GLOBAL_OPT"]],
    "GLOBAL_OPT": [["FUNC_DEC"],["ATTRIB","GLOBAL_TAIL"]],
    "GLOBAL_TAIL": [["tkn_times"],["id", "ATTRIB","NAME_ATTRIB_LIST","OPT_EXPLIST"]],

    "LOCAL_DEC": [["local", "LOCAL_OPT"]],
    "LOCAL_OPT": [["FUNC_DEC"],["ATTNAME_BRANCH"]],
    "ATTNAME_BRANCH": [["ATTNAMELIST","OPT_EXPLIST"]],
    "OPT_EXPLIST": [["tkn_assign","EXPLIST"],["ε"]],

    "ATTNAMELIST": [["ATTRIB","id", "ATTRIB","NAME_ATTRIB_LIST"]],
    "NAME_ATTRIB_LIST": [["tkn_comma","id","ATTRIB","NAME_ATTRIB_LIST"],["ε"]],
    "ATTRIB": [["tkn_less","id","tkn_greater"],["ε"]],
    "FUNC_DEC": [["function", "id", "FUNCBODY"]],

    "FUNCBODY": [["tkn_opening_par","OPT_PARLIST","tkn_closing_par", "BLOCK","end"]],
    "OPT_PARLIST": [["PARLIST"],["ε"]],
    "PARLIST": [["id","PARLIST_TAIL"],["VARPARAGRAM"]],
    "PARLIST_TAIL": [["tkn_comma","PARLIST_AFTER_COMMA"],["ε"]],
    "PARLIST_AFTER_COMMA":[["id","PARLIST_TAIL"],["VARPARAGRAM"]],


    "VARPARAGRAM": [["tkn_varargs","OPT_NAME"]],
    "OPT_NAME": [["id"],["ε"]],
    "FUNCNAME": [["id","DOTTED_FUNCNAME","COLON_FUNCNAME"]],
    "DOTTED_FUNCNAME": [["tkn_period", "id","DOTTED_FUNCNAME"],["ε"]],
    "COLON_FUNCNAME": [["tkn_colon","id"],["ε"]],
    
    "IFSTAT":[["if","EXP","then","BLOCK","ELSEIFSTAT","ELSESTAT","end"]],

    "ELSEIFSTAT": [["elseif", "EXP","then","BLOCK","ELSEIFSTAT"],["ε"]],

    "ELSESTAT": [["else","BLOCK"],["ε"]],

    "FORSTAT": [["for","id","FORTYPE","DO_BLOCK_END"]],
    "FORTYPE": [["NUMERICAL_FOR"], ["GENERIC_FOR"]],
    "NUMERICAL_FOR": [["tkn_assign","EXP","tkn_comma", "EXP","OPT_EXP"]],
    "OPT_EXP": [["tkn_comma","EXP"],["ε"]],

    "GENERIC_FOR": [["MORE_NAMES", "in", "EXPLIST"]],

    "NAMELIST": [["id","MORE_NAMES"]],

    "MORE_NAMES": [["tkn_comma","id","MORE_NAMES"],["ε"]],
             
    "DO_BLOCK_END" : [["do","BLOCK","end"]],
    "LABEL": [["tkn_goto","id","tkn_goto"]],

    # The return statement can return one or many values
    "RETSTAT": [["return","MAYBE_EXPLIST","OPT_SEMILOCON"], ["ε"]],
    "OPT_SEMILOCON": [["tkn_semicolon"],["ε"]],
    # MORE_EXP created to add several expressions
    "MAYBE_EXPLIST": [["EXPLIST"],["ε"]],
    "EXPLIST": [["EXP", "MORE_EXP"]],
    "MORE_EXP": [["tkn_comma", "EXP", "MORE_EXP"], ["ε"]],
    "EXP": [
        # Booleans and nil values
        ["nil","EXP_PRIME"],["false","EXP_PRIME"],["true","EXP_PRIME"],
        # terminal tokens
        ["tkn_num","EXP_PRIME"],["tkn_str","EXP_PRIME"],["tkn_varargs","EXP_PRIME"],
        ["FUNCTIONDEF","EXP_PRIME"],

        ["UNOP","EXP"]
        ],
    "EXP_PRIME": [["BINOP","EXP",],["ε"]],

    "FUNCTIONDEF": [["function", "FUNCBODY"]],
    #prefixexp replaces var in the elimination of left recursion
    "PREFIXEXP": [["tkn_opening_par", "EXP", "tkn_closing_par", "PREFIXEXP_PRIME"],
                  ["id","PREFIXEXP_PRIME"]],
    #prefixexp replaces function call as well
    "PREFIXEXP_PRIME": [["tkn_opening_bra", "EXP", "tkn_closing_bra","PREFIXEXP_PRIME"],
                        ["tkn_period","id","PREFIXEXP_PRIME"],
                        ["ARGS","PREFIXEXP_PRIME"],
                        ["tkn_colon","id","ARGS", "PREFIXEXP_PRIME"],["ε"]],


    "ARGS": [["tkn_opening_par","MAYBE_EXPLIST", "tkn_closing_par"], ["tkn_str"]],
    
    "VARLIST": [["PREFIXEXP", "MORE_VAR"]],

    "MORE_VAR": [["tkn_comma","PREFIXEXP","MORE_VAR"],["ε"]],

    "BINOP" :  [
        ["tkn_plus"],["tkn_minus"],["tkn_times"],["tkn_div"],["tkn_floor_div"],
        ["tkn_power"],["tkn_mod"],["tkn_bit_and"],["tkn_bitex_or"],["tkn_bit_or"],
        ["tkn_right_shift"],["tkn_left_shift"],["tkn_concat"],["tkn_less"],["tkn_leq"],
        ["tkn_greater"],["tkn_geq"],["tkn_equal"],["tkn_neq"],["and"],["or"]], 

    "UNOP": [["tkn_minus"],["not"],["tkn_bitex_or"],["tkn_length"]]
}

if __name__ == "__main__":
    myGrammar = Grammar(final_grammar)
    myGrammar.process_grammar()
    if not myGrammar.check_LL1_condition():
        print("Cannot procede. Grammar is not LL1")
        pred_set = myGrammar.get_predict_set()
        for NT,pred in pred_set.items():print(f"{NT}: {pred}")
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


