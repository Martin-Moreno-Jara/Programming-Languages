from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer, Token


class ASDR_base():
    def __init__(self,lexer:Lexer):
        self.lexer = lexer
        self.cur_tok:Token

    def format_error_message(self,expected):
        return f"<{self.cur_tok.line}:{self.cur_tok.col}> Error sintactico: se encontro: \"{self.cur_tok.lexeme}\"; se esperaba: {expected}."


    def match(self,expected_tok:str):
        if self.cur_tok.type == expected_tok:
            self.cur_tok = self.lexer.tokenize()
        else:
            raise SyntacticalError(self.format_error_message(expected_tok))


