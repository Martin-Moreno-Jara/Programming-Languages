import re
import string


class LexicalError(Exception):
    """
    Custom exception class to raise when a symbol is not recognized
    as a part of the language
    """

    def __init__(self, message, line, col):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col


class Lexer:
    """
    Lexical analyzer implementation class
    """

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
            "error",
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
            "pcall",
            "repeat",
            "return",
            "then",
            "true",
            "until",
            "warn",
            "while",
        }
        self.digits_set = set(string.digits)
        self.alfabetic_set = set(string.ascii_letters + "_")
        self.hexdigits_set = set(string.hexdigits)
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
            "id": re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*"),
            "int_dec": re.compile(
                r"\d+\.\d*[eE][+-]{0,1}\d+|\d+\.\d*|\d+[eE][+-]{0,1}\d+|\d+"
            ),
            "hex": re.compile(
                r"0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)(?:[pP][+-]?\d+)?"
            ),
            "nums": re.compile(r"\d+|\."),
        }

    def peek(self, offset=0):
        """
        returns the element at self.pos+offset. If that position is out of range,
        it returns None, so a index out of bounds exception is not triggered.
        """
        return (
            self.data[self.pos + offset] if self.pos + offset < len(self.data) else None
        )

    def calc_inline_pos(self, start):
        """
        Calculates the position of a token relative to its line.
        In other words, the col.
        """
        return start - self.last_pos + 1

    def _mode_keyword_id(self, start):
        """
        Given that the token could be a keyword or an identifier,
        it captures the longest possible substring and decides
        which one it is by checking the keywords set
        """
        longest_match = self.patterns_dict["id"].match(
            self.data, start
        )  # use regex to quickly catch the longest match

        lexem = longest_match.group()
        self.pos = longest_match.end()
        if lexem in self.keywords_set:  # token is a keyword
            return f"<{lexem},{self.line},{self.calc_inline_pos(start)}>"
        else:  # token is an identifier
            return f"<id,{lexem},{self.line},{self.calc_inline_pos(start)}>"

    def _mode_num(self, start):
        """
        Given the first char is a digit, it checks the
        longest substring that coincides with a integer
        or a decimal
        """
        # TODO: If next submission doesn't pass, consider adding scientific notation, hexadecimals and binaries
        cur = self.peek()
        next = self.peek(1)
        after_next = self.peek(2)
        if cur == "0" and (next == "x" or next == "X") and (after_next in self.hexdigits_set):  # hexadecimal
            longest_match = self.patterns_dict["hex"].match(self.data, start)
        else: # int, decimal, exponentials
            longest_match = self.patterns_dict["int_dec"].match(self.data, start)
        lexem = longest_match.group()
        self.pos = longest_match.end()

        return f"<tkn_num,{lexem},{self.line},{self.calc_inline_pos(start)}>"

    def _mode_string(self, start):
        """
        Given that the first char is a quote " or '
        it processes the string until it closes, or
        raises an exception if it is not correctly closed

        """
        starting_quote = self.peek()
        self.pos += 1
        while True:
            cur = self.peek()
            next = self.peek(1)

            if (
                not cur
            ):  # if end of file is reached without closing the string, lexical error
                raise LexicalError(
                    f">>> Error lexico String no cerrado",
                    self.line,
                    self.calc_inline_pos(start),
                )
            elif cur == "\n":  # if there is a newline in a simple string, lexical error
                raise LexicalError(
                    f">>> Error lexico String malformado. Nueva línea no permitida",
                    self.line,
                    self.calc_inline_pos(start),
                )
            elif cur == "\\" and (
                next == starting_quote or next == "\\"
            ):  # Allowing embedded quotes with scaping sequence
                self.pos += 2

            elif cur == starting_quote:  # Closing of string reached
                self.pos += 1
                break
            else:  # General case
                self.pos += 1

        return f"<tkn_str,{self.data[start+1:self.pos-1]},{self.line},{self.calc_inline_pos(start)}>"

    def _mode_op_symbol(self, start):
        """
        Given that the first character is in the symbols and operands dict
        it returns the longest possible and valid match in the dict
        """
        symbol = ""
        for i in range(2, -1, -1):
            if self.peek(i):
                symbol = self.operand_symbols_dict.get(self.data[start : start + i + 1])
                if symbol:
                    self.pos += i + 1
                    break

        return f"<{symbol},{self.line},{self.calc_inline_pos(start)}>"

    def _handle_multiline_comments(
        self, starting_pos: int, starting_line: int, n_equals=0
    ):
        """
        Given a multiline comment, it ignores everything
        until the block is correctly closed.
        Raises error otherwise
        """
        is_closed_correctly = False
        matching_delim = 0
        while True:
            cur = self.peek()
            next = self.peek(1)

            if (
                not cur
            ):  # Reached the end of the input without correctly closing the comment
                raise LexicalError(
                    f">>> Error lexico Comentario multilinea no cerrado",
                    starting_line,
                    starting_pos,
                )

            if cur == "]":  # possibility of closing the comment
                while (
                    next == "="
                ):  # checking that the number of = deliminator coincides with the opening part
                    matching_delim += 1
                    self.pos += 1
                    next = self.peek(1)
                if next == "]" and n_equals == matching_delim:
                    is_closed_correctly = True
                    self.pos += 2  # added 2 because it puts the pos pointer in the next position after finishing the comment
                else:
                    matching_delim = 0  # reset the matching counter if the closing part is not well formed
                    self.pos += 1

            elif cur == "\n":  # newline character - must update line data
                self.pos += 1
                self.line += 1
                self.last_pos = self.pos
            else:  # general case
                self.pos += 1

            if is_closed_correctly:
                break

    def _handle_comments(self) -> None:
        """
        Given that the following sequence is a comment,
        decide whether it is a single line or multiline comment
        and treat it accordingly.
        """

        starting_pos = self.calc_inline_pos(self.pos)
        starting_line = self.line

        self.pos += 2  # leave pointer in the next character after --

        cur = self.peek()
        next = self.peek(1)

        is_multiline = False
        n_equals = 0
        if cur == "[":  # check possible multiline comment start
            while next == "=":  # count the = delimitator if there are
                n_equals += 1
                self.pos += 1
                next = self.peek(1)
            if (
                next == "["
            ):  # makes sure that the multicomment block is formed correctly --[[ or -[(=)*[
                self.pos += 1
                is_multiline = True

        if is_multiline:
            self._handle_multiline_comments(starting_pos, starting_line, n_equals)
        else:
            while self.peek() and self.peek() != "\n":  # single line comments
                self.pos += 1

    def _cleanse_input(self) -> None:
        """
        Ignore characters that should not be processed
        as tokens (blank spaces, new lines and comments)
        until it finds a valid token character.
        """
        # TODO: Maybe find a more efficient way to skip blank spaces
        while True:
            cur = self.peek()
            next = self.peek(1)

            if cur == "-" and next == "-":  # comment
                self._handle_comments()
            elif (  # blank spaces
                cur == " " or cur == "\t" or cur == "\r" or cur == "\v" or cur == "\f"
            ):
                self.pos += 1
            elif cur == "\n":  # new lines
                self.pos += 1
                self.line += 1
                self.last_pos = self.pos
            else:  # other character - must process it
                break

    def _process_token(self) -> str:
        """ "
        Given the first character of a token
        it decides what it should be processed as.
        """
        start = self.pos
        first_char = self.peek()
        # si primer caracter letra - modo keyword/id
        if first_char in self.alfabetic_set:
            return self._mode_keyword_id(start)

            # si primer caracter número - modo número
        elif first_char in self.digits_set:
            return self._mode_num(start)

            # TODO: Considerar comentarios multilínea con [[""]]
            # si primer caracter " o ' - modo string
        elif first_char == '"' or first_char == "'":
            return self._mode_string(start)

            # si primer caracter está en dict de simbolos - modo operador/simbolo
        elif self.operand_symbols_dict.get(first_char):
            return self._mode_op_symbol(start)

            # si no, error léxico
        else:
            raise LexicalError(
                f">>> Error lexico Token no identificado",
                self.line,
                self.calc_inline_pos(start),
            )

    def tokenize(self) -> str:
        """
        Wrapper function. Calls function to clean the input of
        unnecessary characters, and then calls the function
        to process and return the next token, while handling
        exception in the try except block
        """
        try:
            self._cleanse_input()

            if not self.peek():
                raise EOFError("End of file reached")

            return self._process_token()
        except LexicalError as e:
            print(f">>> Error lexico (linea: {e.line}, posicion: {e.col})")
            exit()
        except EOFError:
            raise
        except Exception as e:
            print(f"Unexpected error ocurred {e.args}, {e.__cause__}")
            exit()
