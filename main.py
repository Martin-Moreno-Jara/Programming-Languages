import sys
from syntax.grammar import Grammar
from lexer.lexer import Lexer
from syntax.code_generator_script import ASDR_generator
from exceptions.custom_exceptions import *


final_grammar: dict[str, list[list[str]]] = {
    # ------------------------------------------------------------------
    # Program structure
    # ------------------------------------------------------------------
    # CHUNK is the initial symbol
    "CHUNK": [["BLOCK"]],
    # The block can have several statements and optionally a return statement
    "BLOCK": [["STATLIST", "RETSTAT"]],
    # A statement list can be empty, have only one, or several statements
    "STATLIST": [["STAT", "STATLIST"], ["ε"]],

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------
    "STAT": [
        ["tkn_semicolon"], # empty statement
        # varlist and functionall factor prefixexp
        ["NAME","VAR_STAT"],
        #["tkn_opening_par","EXP", "tkn_closing_par","AFTER_VAR"],
        ["LABEL"],
        ["break"],
        ["goto", "NAME"],
        ["while", "EXP", "DO_BLOCK_END"],
        ["repeat", "BLOCK", "until", "EXP"],
        ["IFSTAT"],
        ["FORSTAT"],
        ["function", "FUNCNAME", "FUNCBODY"],
        ["LOCAL_DEC"],
        ["GLOBAL_DEC"],
    ],

    "LABEL": [["tkn_goto", "NAME", "tkn_goto"]],
    "DO_BLOCK_END": [["do", "BLOCK", "end"]],

    "VAR_STAT": [
            ["tkn_opening_bra", "EXP", "tkn_closing_bra", "VAR_STAT"],
            ["tkn_period", "NAME", "VAR_STAT"],
            ["FUNCTIONCALL","FUNCALL_STAT"],
            ["MORE_VAR","tkn_assign","EXPLIST"]
            ],

    "FUNCALL_STAT" : [
                    ["tkn_opening_bra", "EXP", "tkn_closing_bra", "VAR_STAT"],
                    ["tkn_period", "NAME", "VAR_STAT"],
                    ["FUNCTIONCALL","FUNCALL_STAT"],
                    ["ε"]
    ],

    # if statements
    "IFSTAT": [["if", "EXP", "then", "BLOCK", "ELSEIFSTAT", "ELSESTAT", "end"]],
    "ELSEIFSTAT": [["elseif", "EXP", "then", "BLOCK", "ELSEIFSTAT"], ["ε"]],
    "ELSESTAT": [["else", "BLOCK"], ["ε"]],

    # for statements
    "FORSTAT": [["for", "NAME", "FORTYPE", "DO_BLOCK_END"]],
    "FORTYPE": [["NUMERICAL_FOR"], ["GENERIC_FOR"]],
    "NUMERICAL_FOR": [["tkn_assign", "EXP", "tkn_comma", "EXP", "OPT_EXP"]],
    "OPT_EXP": [["tkn_comma", "EXP"], ["ε"]],
    "GENERIC_FOR": [["MORE_NAMES", "in", "EXPLIST"]],

    # Return statement: can return zero, one or many values
    "RETSTAT": [["return", "MAYBE_EXPLIST", "OPT_SEMILOCON"], ["ε"]],
    "OPT_SEMILOCON": [["tkn_semicolon"], ["ε"]],

    # ------------------------------------------------------------------
    # Declarations (local / global)
    # ------------------------------------------------------------------
    "LOCAL_DEC": [["local", "LOCAL_OPTS"]],
    "LOCAL_OPTS": [["FUNC_DEC"], ["ATTNAME_BRANCH"]],
    "ATTNAME_BRANCH": [["ATTNAMELIST", "OPT_EXPLIST"]],

    # the optional ATTRIB is factored out so "global <attrib> *" and
    # "global <attrib> name ..." don't share a prediction
    "GLOBAL_DEC": [["global", "GLOBAL_OPTS"]],
    "GLOBAL_OPTS": [["FUNC_DEC"], ["ATTNAMELIST", "OPT_EXPLIST"]],

    "FUNC_DEC": [["function", "NAME", "FUNCBODY"]],
    "OPT_EXPLIST": [["tkn_assign", "EXPLIST"], ["ε"]],

    "ATTNAMELIST": [["NAME", "ATTRIB", "NAME_ATTRIB_LIST"]],
    "NAME_ATTRIB_LIST": [["tkn_comma", "NAME", "ATTRIB", "NAME_ATTRIB_LIST"], ["ε"]],
    "ATTRIB": [["tkn_less", "NAME", "tkn_greater"], ["ε"]],

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------
    "FUNCNAME": [["NAME", "DOTTED_FUNCNAME", "COLON_FUNCNAME"]],
    "DOTTED_FUNCNAME": [["tkn_period", "NAME", "DOTTED_FUNCNAME"], ["ε"]],
    "COLON_FUNCNAME": [["tkn_colon", "NAME"], ["ε"]],

    "FUNCTIONDEF": [["function", "FUNCBODY"]],
    "FUNCBODY": [["tkn_opening_par", "OPT_PARLIST", "tkn_closing_par", "BLOCK", "end"]],

    # parameter list: the comma is consumed before deciding between
    # another name and the varargs
    "OPT_PARLIST": [["PARLIST"], ["ε"]],
    "PARLIST": [["NAME", "PARLIST_TAIL"], ["VARPARAGRAM"]],
    "PARLIST_TAIL": [["tkn_comma", "PARLIST_AFTER_COMMA"], ["ε"]],
    "PARLIST_AFTER_COMMA": [["NAME", "PARLIST_TAIL"], ["VARPARAGRAM"]],
    "VARPARAGRAM": [["tkn_varargs", "OPT_NAME"]],
    "OPT_NAME": [["NAME"], ["ε"]],

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------
    "MORE_NAMES": [["tkn_comma", "NAME", "MORE_NAMES"], ["ε"]],

    #"VARLIST": [["tkn_assign"]],
    "MORE_VAR": [["tkn_comma", "PREFIXEXP", "MORE_VAR"], ["ε"]],

    # MORE_EXP created to add several expressions
    "MAYBE_EXPLIST": [["EXPLIST"], ["ε"]],
    "EXPLIST": [["EXPLIST_ITEM", "MORE_EXP"]],
    "MORE_EXP": [["tkn_comma", "EXPLIST_ITEM", "MORE_EXP"],["ε"]],
    "EXPLIST_ITEM": [["EXP"],["FUNCTIONDEF"]],

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------
    "EXP": [["OPERAND","EXP_PRIME"]],

    "OPERAND_NOT_ID":  [
    ["nil"], ["false"], ["true"],
    ["tkn_num"], ["tkn_str"],
    ["TABLECONSTRUCTOR",],
    ["UNOP", "OPERAND"],
    ["tkn_opening_par", "EXP", "tkn_closing_par"],
],
    "EXP_PRIME": [["ARITH_TAIL", "CMP_TAIL", "LOGIC_TAIL"]],

    "OPERAND": [["NAME", "PREFIXEXP_PRIME"], ["OPERAND_NOT_ID"]],

    # prefixexp replaces var and function call in the elimination of left recursion
    "PREFIXEXP": [
       # ["tkn_opening_par", "EXP", "tkn_closing_par", "PREFIXEXP_PRIME"],
        ["NAME", "PREFIXEXP_PRIME"],
    ],
    "PREFIXEXP_PRIME": [
        ["tkn_opening_bra", "EXP", "tkn_closing_bra", "PREFIXEXP_PRIME"],
        ["tkn_period", "NAME", "PREFIXEXP_PRIME"],
        ["FUNCTIONCALL","PREFIXEXP_PRIME"],
        ["ε"],
    ],

    "FUNCTIONCALL": [["ARGS"],
            ["tkn_colon", "NAME", "ARGS"],],
    
    "ARGS": [["tkn_opening_par", "MAYBE_EXPLIST", "tkn_closing_par"]],



    # ------------------------------------------------------------------
    # Tables
    # ------------------------------------------------------------------
    "TABLECONSTRUCTOR":[["tkn_opening_key","FIELDLIST","tkn_closing_key"]],
    "FIELDLIST":[["FIELD","FIELD_TAIL"],["ε"]],
    "FIELD_TAIL": [["FIELDSEP","FIELDLIST"],["ε"]],
    "FIELD": [["tkn_opening_bra","EXP","tkn_closing_bra","tkn_assign", "FIELD_VALUE"],
              ["NAME", "FIELD_ID"], ["OPERAND_NOT_ID", "EXP_PRIME"],["FUNCTIONDEF"]],
    "FIELD_ID": [["tkn_assign", "FIELD_VALUE"],["PREFIXEXP_PRIME", "EXP_PRIME"]],
    "FIELD_VALUE": [["EXP"],["FUNCTIONDEF"]],
    "FIELDSEP":[["tkn_comma"],["tkn_semicolon"]],

    # ------------------------------------------------------------------
    # Operators
    # ------------------------------------------------------------------

    "LOGIC_TAIL": [["LOGICAL_OP", "CMP_EXP","LOGIC_TAIL"],["ε"]],
    "CMP_EXP": [["ARTH_EXP", "CMP_TAIL"]],
    "CMP_TAIL": [["RELATIONAL_OP", "ARTH_EXP"],["ε"]],
    "ARTH_EXP": [["OPERAND", "ARITH_TAIL"]],
    "ARITH_TAIL": [["FLAT_OP", "OPERAND", "ARITH_TAIL"], ["ε"]],


    "ARITH_OP": [["tkn_plus"], ["tkn_minus"], ["tkn_times"], ["tkn_div"], ["tkn_floor_div"],
            ["tkn_power"], ["tkn_mod"],],

    "RELATIONAL_OP": [["tkn_less"], ["tkn_leq"], ["tkn_greater"], ["tkn_geq"],
            ["tkn_equal"], ["tkn_neq"],],

    "LOGICAL_OP": [["and"], ["or"]],

    "BITWISE_OP" : [["tkn_bit_and"], ["tkn_bitex_or"], ["tkn_bit_or"],
            ["tkn_right_shift"], ["tkn_left_shift"],],

    "OTHER_OP": [["tkn_concat"]],

    "FLAT_OP": [["ARITH_OP"],["BITWISE_OP"],["OTHER_OP"]],

    "UNOP": [["tkn_minus"], ["not"], ["tkn_length"]],
    "NAME": [["id"],["print"],["pcall"],["error"],["warn"],["xpcall"]],
}

pred_exceptions={
  
}

if __name__ == "__main__":
    myGrammar = Grammar(final_grammar)
    myGrammar.set_pred_exceptions(pred_exceptions)
    myGrammar.process_grammar()

    if not myGrammar.check_LL1_condition():
        print("Cannot procede. Grammar is not LL1")
        exit()
    ASDR_generator(myGrammar).generate()
    from syntax.ASDR import ASDR
    data = sys.stdin.read()
    if not data.endswith("\n"):
        data += "\n"

    lexer = Lexer(data)
    try:
        parser = ASDR(lexer)
        parser.main()
        print("El analisis sintactico ha finalizado exitosamente.")
    except SyntacticalError as e:
        print(e.message)
        exit()


