from .grammar import Grammar

class ASDR_generator():
    def __init__(self,grammar:Grammar):
        self.grammar = grammar
        self.lines = ["from exceptions.custom_exceptions import SyntacticalError","from lexer.lexer import Lexer","from .ASDR_base import ASDR_base", "", "class ASDR(ASDR_base):\n"]
        self.eps = "ε"

    def populate_lines(self):

        predict = self.grammar.predict
        grammar_dict = self.grammar.get_grammar()
        for A, alts in grammar_dict.items():
            is_nullable=False
            pass_else = False
            pending_acc = set()
            # declaraction of the function. 1 level of identation
            self.lines.append(f"\tdef parse_{A}(self):")
            for i,alt in enumerate(alts):
                # a single nullable alternative needs no if: its symbols are all non-terminals
                if len(alts) == 1 and self.eps in self.grammar.first_of_sequence(alts[0]):
                    calls = [f"\t\tself.parse_{symbol}()" for symbol in alt if symbol != self.eps]
                    self.lines.extend(calls if calls else ["\t\tpass"])
                    self.lines.append("")
                    pass_else= True
                    continue

                if alt == [self.eps]:
                    is_nullable=True
                    continue
                if self.eps in self.grammar.first_of_sequence(alt):
                    is_nullable=True

                # each if branch representing the alternatives of that non-terminal. 2 levels of identation
                branch_pred = predict[A][i]
                # only the tokens that start the alternative, without FOLLOW and the excepted ones
                pending_acc |= (self.grammar.first_of_sequence(alt) - {self.eps}) & branch_pred
                cond = "if" if i==0 else "elif"
                self.lines.append(f"\t\t{cond} self.cur_tok.type in {sorted(branch_pred)!r}:")
                for symbol in alt:
                    #the specific action of each alternative. Matching other calling other non-terminal function. 3 levels of identation
                    if symbol in self.grammar.non_terminals_set:
                        self.lines.append(f"\t\t\tself.parse_{symbol}()")
                    else:
                        self.lines.append(f"\t\t\tself.match({symbol!r})")

            add_pending = f"self.pending|=set({sorted(pending_acc)!r})"
            if is_nullable:
                self.lines.append(f"\t\telse:\n\t\t\t{add_pending}\n")
            elif pass_else:
                pass
            else:
                self.lines.append(f"\t\telse:\n\t\t\t{add_pending}\n\t\t\traise SyntacticalError(self.format_error_message(self.report_expected_symbols()))\n")

        # main function
        self.lines.append("\tdef main(self):")
        self.lines.append("\t\tself.cur_tok = self.lexer.tokenize()")
        self.lines.append(f"\t\tself.parse_{self.grammar.get_initial_symbol()}()")
        self.lines.append("\t\tif self.cur_tok.type != \"$\":")
        self.lines.append("\t\t\tself.pending|={\"$\"}")
        self.lines.append("\t\t\traise SyntacticalError(self.format_error_message(self.report_expected_symbols()))")

        

    def write_program(self):
        with open("./syntax/ASDR.py","w") as f:
            for line in self.lines:
                f.write(line)
                f.write("\n")

    def generate(self):
        self.populate_lines()
        self.write_program()
 