from grammar import Grammar
class NotLL1Error(Exception):
    """
    Custom exception class to raise when the given grammar is not LL1
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

eps = "ε"

grammar1: dict[str, list[list[str]]] = {
    "A": [["B", "C"], ["ant", "A", "all"]],
    "B": [["big", "C"], ["bus", "A", "boss"], ["ε"]],
    "C": [["cat"], ["cow"]],
}

lines = ["from ..exceptions.custom_exceptions import SyntacticalError","from ASDR_base import ASDR_base", "", "class ASDR(ASDR_base):\n"]

def populate_lines(grammar:Grammar):
    predict = grammar.predict
    grammar_dict = grammar.get_grammar()
    for A, alts in grammar_dict.items():
        # declaraction of the function. 1 level of identation
        lines.append(f"\tdef parse_{A}(self):")
        for i,alt in enumerate(alts):
            cond = "if" if i==0 else "elif"
            # each if branch representing the alternatives of that non-terminal. 2 levels of identation
            lines.append(f"\t\t{cond} self.cur_tok in {sorted(predict[A][i])!r}:")
            for symbol in alt:
                #the specific action of each alternative. Matching other calling other non-terminal function. 3 levels of identation
                if symbol == eps:
                    lines.append(f"\t\t\tpass")
                elif symbol in grammar.non_terminals_set:
                    lines.append(f"\t\t\tself.parse_{symbol}()")
                else:
                    lines.append(f"\t\t\tself.match({symbol!r})")
                    break
        expected = sorted(set().union(*predict[A]))

        lines.append(f"\t\telse:\n\t\t\traise SyntacticalError({expected!r})\n")


def write_program(lines):
    with open("ASDR.py","w") as f:
        for line in lines:
            f.write(line)
            f.write("\n")

try:
    myGrammar = Grammar(grammar1)
    myGrammar.process_grammar()
    if not myGrammar.check_LL1_condition():
        raise NotLL1Error("Grammar is not LL1. Can't proceed")
    populate_lines(myGrammar)
    write_program(lines)
except NotLL1Error as e:
    print(e.message)
    exit()