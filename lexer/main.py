import sys
import re


class LexicalError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col


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
            "global",
            "goto",
            "if",
            "in",
            "local",
            "nil",
            "not",
            "or",
            "print",
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

    def peek(self, offset=0):
        return (
            self.data[self.pos + offset] if self.pos + offset < len(self.data) else None
        )

    def calc_inline_pos(self, start):
        return start - self.last_pos + 1

    def _mode_keyword_id(self, start):
        while self.pos < len(self.data) and self.patterns_dict["id"].match(
            self.data[self.pos]
        ):
            self.pos += 1

        lexem = self.data[start : self.pos]
        if lexem in self.keywords_set:  # token is a keyword
            return f"<{lexem},{self.line},{self.calc_inline_pos(start)}>"
        else:  # token is an identifier
            return f"<id,{lexem},{self.line},{self.calc_inline_pos(start)}>"

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

        return f"<tkn_num,{num},{self.line},{self.calc_inline_pos(start)}>"

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
        return f"<tkn_str,{lexem},{self.line},{self.calc_inline_pos(start)}>"

    def _mode_op_symbol(self, start):
        symbol = self.data[start]

        while self.pos < len(self.data):
            self.pos += 1
            aux = symbol + self.data[self.pos]
            if not self.operand_symbols_dict.get(aux):
                break
            symbol = aux

        # print(self.operand_symbols_dict.get(" "))
        return f"<{self.operand_symbols_dict.get(symbol)},{symbol},{self.line},{self.calc_inline_pos(start)}>"

    def _handle_blanks(self):
        while True:
            cur = self.peek()
            if cur == " " or cur == "\t" or cur == "\r":
                self.pos += 1
            else:
                break

    def _handle_new_line(self):
        while self.peek() == "\n":
            self.pos += 1
            self.line += 1
            self.last_pos = self.pos

    def _handle_single_line_comments(self):
        while self.peek() != "\n":
            self.pos += 1

    def _handle_multiline_comments(self, starting_pos: int, starting_line, n_equals=0):
        while True:
            cur = self.peek()
            # TODO: Arreglar la mandada a error por comentario mal cerrado

            while cur != "]":
                self.pos += 1
                if cur == "\n":
                    self.line += 1
                    self.last_pos = self.pos
                if not cur:
                    raise LexicalError(
                        f">>> Error lexico Comentario multilinea no cerrado",
                        starting_line,
                        starting_pos,
                    )
                cur = self.peek()
            i = 1
            n_counter = 0
            start_again = False
            while n_equals != n_counter:
                if self.peek(i) == "=":
                    n_counter += 1
                    i += 1
                else:
                    start_again == True
                    break
            if start_again:
                continue
            if self.peek(i) == "]":
                self.pos += i + 1
                break

    def _handle_comments(self):
        starting_pos = self.calc_inline_pos(self.pos)
        starting_line = self.line
        self.pos += 2
        cur = self.peek()
        next = self.peek(1)
        if cur == "[" and next == "[":
            self._handle_multiline_comments(starting_pos, starting_line)
        elif cur == "[" and next == "=":
            i = 1
            n_equals = 0
            while self.peek(i) == "=":
                n_equals += 1
                i += 1
            if self.peek() == "[":
                self.pos += i + 1
                self._handle_multiline_comments(starting_pos, starting_line, n_equals)
        else:
            self._handle_single_line_comments()

    def _cleanse_input(self):
        # identify each type of unnecessary token
        while True:
            cur = self.peek()
            next = self.peek(1)

            if cur == "-" and next == "-":
                self._handle_comments()
            elif cur == " " or cur == "\t" or cur == "\r":
                self._handle_blanks()
            elif cur == "\n":
                self._handle_new_line()
            else:
                break

    def _process_token(self, start, first_char):

        # si primer caracter letra - modo keyword/id
        if self.patterns_dict["id"].match(first_char):
            token = self._mode_keyword_id(start)
            return token

            # si primer caracter número - modo número
        elif self.patterns_dict["tkn_num"].match(first_char):
            token = self._mode_num(start)
            return token

            # si primer caracter " o ' - modo string
        elif first_char == '"' or first_char == "'":
            token = self._mode_string(start)
            return token

            # si primer caracter está en dict de simbolos - modo operador/simbolo
        elif self.operand_symbols_dict.get(first_char):
            token = self._mode_op_symbol(start)
            return token

            # si no, error léxico
        else:
            raise LexicalError(
                f">>> Error lexico Token no identificado",
                self.line,
                self.calc_inline_pos(start),
            )

    def tokenize(self) -> str:
        try:
            self._cleanse_input()

            start = self.pos
            first_char = self.peek()

            if not first_char:
                raise EOFError("End of file reached")

            return self._process_token(start, first_char)
        except LexicalError as e:
            print(
                f">>> Error lexico (linea: {e.line}, posicion: {e.col} : {self.peek()})"
            )
            print(e.message)
            exit()
        except EOFError:
            raise
        except Exception as e:
            print(f"Unexpected error ocurred {e.args}, {e.__cause__}")
            exit()


data = sys.stdin.read()

lexer = Lexer(data)

while True:
    try:
        token = lexer.tokenize()
        if token:
            print(token)
    except EOFError:
        break
