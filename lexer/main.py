import sys
from lexer.lexer import Lexer

data = sys.stdin.read()

lexer = Lexer(data)

while True:
    token = lexer.tokenize()
    if token.type=="$":
        break
    print(token)
