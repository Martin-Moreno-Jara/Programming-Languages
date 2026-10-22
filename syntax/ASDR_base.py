from ..lexer.lexer import Lexer

class SyntacticalError(Exception):
    """
    Custom exception class to raise when there is a syntactical error
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ASDR_base():
    def __init__(self,lexer:Lexer):
        self.lexer = lexer
        self.cur_tok:str

    def match(self,expected_tok:str):
        if self.cur_tok == expected_tok:
            self.cur_tok = self.lexer.tokenize()
        else:
            raise SyntacticalError("Not expected")


