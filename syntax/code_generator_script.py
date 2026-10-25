from .grammar import Grammar

class ASDR_generator():
    def __init__(self,grammar:Grammar):
        self.grammar = grammar
        self.lines = ["from exceptions.custom_exceptions import SyntacticalError","from lexer.lexer import Lexer","from .ASDR_base import ASDR_base", "", "class ASDR(ASDR_base):\n"]
        self.eps = "ε"
        self.sorting_order = {"tkn_num": "valor_numerico", "tkn_str": "cadena_de_caracteres"}

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
            
            expected = sorted(set().union(*predict[A]), key=lambda t: self.sorting_order.get(t, t))

            self.lines.append(f"\t\telse:")
            self.lines.append(f"\t\t\traise SyntacticalError(self.format_error_message({expected}))\n")

        # main function
        self.lines.append("\tdef main(self):")
        self.lines.append("\t\tself.cur_tok = self.lexer.tokenize()")
        self.lines.append(f"\t\tself.parse_{self.grammar.get_initial_symbol()}()")
        self.lines.append("\t\tif self.cur_tok.type != \"$\":")
        self.lines.append("\t\t\traise SyntacticalError(self.format_error_message([\"$\"]))")

        

    def write_program(self):
        with open("./syntax/ASDR.py","w") as f:
            for line in self.lines:
                f.write(line)
                f.write("\n")

    def generate(self):
        self.populate_lines()
        self.write_program()
 