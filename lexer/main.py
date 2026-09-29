import sys
import re


class Lexer:
    def __init__(self, data):
        self.data: str = data
        self.line = 1
        self.pos = 0
        self.last_pos = 0
        self.keywords_set: set = {
            "and",
            "break",
            "do",
            "else",
            "elseif",
            "end",
            "false",
            "for",
            "function",
            "goto",
            "if",
            "in",
            "local",
            "nil",
            "not",
            "or",
            "repeat",
            "return",
            "then",
            "true",
            "until",
            "while",
        }
        self.operand_symbols_dict: dict = {
            "&": "tkn_bit_and",
            "|": "tkn_bit_or",
            "~": "tkn_bitex_or",
            ">>": "tkn_right_shift",
            "<<": "tkn_left_shift",
            ";": "tkn_semicolon",
            ":": "tkn_colon",
            ",": "tkn_comma",
            ".": "tkn_period",
            "::": "tkn_goto",
            "..": "tkn_concat",
            "...": "tkn_varargs",
            "{": "tkn_opening_key",
            "}": "tkn_closing_key",
            "[": "tkn_opening_bra",
            "]": "tkn_closing_bra",
            "(": "tkn_opening_par",
            ")": "tkn_closing_par",
            "#": "tkn_length",
            "+": "tkn_plus",
            "-": "tkn_minus",
            "*": "tkn_times",
            "/": "tkn_div",
            "//": "tkn_floor_div",
            "^": "tkn_power",
            "%": "tkn_mod",
            "==": "tkn_equal",
            "~=": "tkn_neq",
            "<=": "tkn_leq",
            ">=": "tkn_geq",
            ">": "tkn_greater",
            "<": "tkn_less",
            "=": "tkn_assign",
        }

        self.patterns_dict: dict = {
            "id": re.compile(r"^[a-zA-Z_]+\d*[a-zA-Z-]*$"),
            "alf": re.compile(r"^[a-zA-Z_]+$"),
            "tkn_num": re.compile(r"^\d+(\.\d+)*\Z"),
            "tkn_string": re.compile(r"\"([^\"\\]|\\.)*\"|'([^'\\]|\\.)*'"),
            "comm": re.compile(r"^--.*$"),
            "multi_comm": re.compile(r"^\[\[ .* \]\]"),
        }

    def _mode_keyword_id(self, start):
        while self.pos < len(self.data) and self.patterns_dict["id"].match(
            self.data[self.pos]
        ):
            self.pos += 1

        lexem = self.data[start : self.pos]
        if lexem in self.keywords_set:  # token is a keyword
            return f"<{lexem},{self.line},{start - self.last_pos + 1}>"
        else:  # token is an identifier
            return f"<id,{lexem},{self.line},{start - self.last_pos + 1}>"

    def _mode_num(self, start):
        num = self.data[start]

        while self.pos < len(self.data):
            self.pos += 1
            aux = num + self.data[self.pos]
            if self.data[self.pos] == ".":
                aux += "."
                continue
            if not self.patterns_dict["tkn_num"].match(aux):
                break
            num = aux

        return f"<tkn_num,{num},{self.line},{start - self.last_pos + 1}>"

    def _mode_string(self, start):
        starting_quote = self.data[start]
        while self.pos < len(self.data):
            self.pos += 1
            if self.data[self.pos] == starting_quote:
                self.pos += 1
                break
            if self.data[self.pos] == "\\":  # secuencia de escape
                pass

        lexem = self.data[start + 1 : self.pos - 1]
        return f"<tkn_str,{lexem},{self.line},{start - self.last_pos + 1}>"

    def _mode_op_symbol(self, start):
        symbol = self.data[start]

        while self.pos < len(self.data):
            self.pos += 1
            aux = symbol + self.data[self.pos]
            if not self.operand_symbols_dict.get(aux):
                break
            symbol = aux

        # print(self.operand_symbols_dict.get(" "))
        return f"<{self.operand_symbols_dict.get(symbol)},{symbol},{self.line},{start - self.last_pos + 1}>"

    def _mode_single_comment(self):
        pass

    def tokenize(self) -> str:
        try:
            token = ""
            # identificar y saltar espacios
            while self.pos < len(self.data) and self.data[self.pos] == "\n":
                self.line += 1
                self.pos += 1
                self.last_pos = self.pos
            while self.pos < len(self.data) and self.data[self.pos] == " ":
                self.pos += 1

            # identificar y saltar comentarios

            #
            start = self.pos
            first_char = self.data[start]
            # si primer caracter letra - modo keyword/id
            if self.patterns_dict["id"].match(first_char):
                token = self._mode_keyword_id(start)

                # si primer caracter número - modo número
            elif self.patterns_dict["tkn_num"].match(first_char):
                token = self._mode_num(start)

                # si primer caracter " o ' - modo string
            elif first_char == '"' or first_char == "'":
                token = self._mode_string(start)

                # si primer caracter está en dict de simbolos - modo operador/simbolo
            elif self.operand_symbols_dict.get(first_char):
                token = self._mode_op_symbol(start)

                # si no, error léxico
            else:
                print(f">>> Error lexico (linea: {self.line}, posicion: {self.pos+1})")
                exit()

            return token
        except EOFError:
            return
        except IndexError:
            exit()


data = sys.stdin.read()

lexer = Lexer(data)

while True:
    token = lexer.tokenize()
    print(token)
