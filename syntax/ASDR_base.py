from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer, Token


class ASDR_base():
    def __init__(self,lexer:Lexer):
        self.lexer = lexer
        self.cur_tok:Token
        self.pending:set = set()
        self.sorting_order = {"tkn_num": "valor_numerico", "tkn_str": "cadena_de_caracteres"}
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

    def format_expected_symbol(self,s:str):
            if s=="tkn_num":return "\"valor_numerico\""
            elif s=="tkn_str": return "\"cadena_de_caracteres\""
            elif s=="$": return "\"final de archivo\""
            else:
                return f"\"{self.operand_symbols_dict.get(s) if self.operand_symbols_dict.get(s) else s}\""

    
    def format_error_message(self,expected:list[str]):
        lexeme = self.cur_tok.lexeme if self.cur_tok.lexeme != "$" else "final de archivo"
        expected = ", ".join(self.format_expected_symbol(s) for s in expected)
        return f"<{self.cur_tok.line}:{self.cur_tok.col}> Error sintactico: se encontro: \"{lexeme}\"; se esperaba: {expected}."

    def report_expected_symbols(self):
         expected = sorted(self.pending, key=lambda t: self.sorting_order.get(t, t))
         return expected


    def match(self,expected_tok:str):
        if self.cur_tok.type == expected_tok:
            self.pending = set()
            self.cur_tok = self.lexer.tokenize()
        else:
            self.pending|={expected_tok}
            raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))


