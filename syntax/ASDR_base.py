from ..exceptions.custom_exceptions import SyntacticalError
from ..lexer.lexer import Lexer


class ASDR_base():
    def __init__(self,lexer:Lexer):
        self.lexer = lexer
        self.cur_tok:str

    def match(self,expected_tok:str):
        if self.cur_tok == expected_tok:
            self.cur_tok = self.lexer.tokenize()
        else:
            raise SyntacticalError("Not expected")


