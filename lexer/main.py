class Lexer:
    def __init__(self):
        self.keywords_set = {
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
        self.operand_symbols_dict = {
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


lexer = Lexer()

print(lexer.keywords_set)

print(lexer.operand_symbols_dict)
