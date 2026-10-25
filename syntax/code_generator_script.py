from .grammar import Grammar

class ASDR_generator():
    def __init__(self,grammar:Grammar):
        self.grammar = grammar
        self.lines = ["from exceptions.custom_exceptions import SyntacticalError","from lexer.lexer import Lexer","from .ASDR_base import ASDR_base", "", "class ASDR(ASDR_base):\n"]
        self.eps = "ε"
        self.operand_symbols_dict: dict = {
                            "tkn_bit_and": "&",
                            "tkn_bit_or": "|",
                            "tkn_bitex_or": "~",
                            "tkn_right_shift": ">>",
                            "tkn_left_shift": "<<",
                            "tkn_semicolon": ";",
                            "tkn_colon": ":",
                            "tkn_comma": ",",
                            "tkn_period": ".",
                            "tkn_goto": "::",
                            "tkn_concat": "..",
                            "tkn_varargs": "...",
                            "tkn_opening_key": "{",
                            "tkn_closing_key": "}",
                            "tkn_opening_bra": "[",
                            "tkn_closing_bra": "]",
                            "tkn_opening_par": "(",
                            "tkn_closing_par": ")",
                            "tkn_length": "#",
                            "tkn_plus": "+",
                            "tkn_minus": "-",
                            "tkn_times": "*",
                            "tkn_div": "/",
                            "tkn_floor_div": "//",
                            "tkn_power": "^",
                            "tkn_mod": "%",
                            "tkn_equal": "==",
                            "tkn_neq": "~=",
                            "tkn_leq": "<=",
                            "tkn_geq": ">=",
                            "tkn_greater": ">",
                            "tkn_less": "<",
                            "tkn_assign": "=",
                        }

    def format_expected_symbol(self,s):
        if s=="tkn_num":return "valor_numerico"
        elif s=="tkn_str": return "cadena_de_caracteres"
        elif s=="$": return "final de archivo"
        else:
            return self.operand_symbols_dict.get(s) if self.operand_symbols_dict.get(s) else s

    def populate_lines(self):
        predict = self.grammar.predict
        grammar_dict = self.grammar.get_grammar()
        for A, alts in grammar_dict.items():

            # declaraction of the function. 1 level of identation
            self.lines.append(f"\tdef parse_{A}(self):")
            for i,alt in enumerate(alts):
                cond = "if" if i==0 else "elif"
                # each if branch representing the alternatives of that non-terminal. 2 levels of identation
                self.lines.append(f"\t\t{cond} self.cur_tok.type in {sorted(predict[A][i])!r}:")
                for symbol in alt:
                    #the specific action of each alternative. Matching other calling other non-terminal function. 3 levels of identation
                    if symbol == self.eps:
                        self.lines.append(f"\t\t\tpass")
                    elif symbol in self.grammar.non_terminals_set:
                        self.lines.append(f"\t\t\tself.parse_{symbol}()")
                    else:
                        self.lines.append(f"\t\t\tself.match({symbol!r})")
            expected = sorted(set().union(*predict[A]))
            expected_str = ""
            for i,ex in enumerate(expected):
                ex= self.format_expected_symbol(ex)
                expected_str+= f"\"{ex}\""
                if i < len(expected) -1:
                    expected_str+=", "

            self.lines.append(f"\t\telse:")
            self.lines.append(f"\t\t\traise SyntacticalError(self.format_error_message({expected_str!r}))\n")

        # main function
        self.lines.append("\tdef main(self):")
        self.lines.append("\t\tself.cur_tok = self.lexer.tokenize()")
        self.lines.append(f"\t\tself.parse_{self.grammar.get_initial_symbol()}()")
        self.lines.append("\t\tif self.cur_tok.type != \"$\":")
        self.lines.append("\t\t\traise SyntacticalError(self.format_error_message(\"$\"))")

        

    def write_program(self):
        with open("./syntax/ASDR.py","w") as f:
            for line in self.lines:
                f.write(line)
                f.write("\n")

    def generate(self):
        self.populate_lines()
        self.write_program()
 