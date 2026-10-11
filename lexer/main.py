import sys
from lexer import Lexer

data = sys.stdin.read()

lexer = Lexer(data)

while True:
    try:
        print(lexer.tokenize())
    except EOFError:
        break