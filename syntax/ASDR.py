from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer
from .ASDR_base import ASDR_base

class ASDR(ASDR_base):

	def parse_S(self):
		if self.cur_tok in ['a', 'b', 'c']:
			self.parse_A()
			self.parse_B()
			self.parse_C()
		else:
			raise SyntacticalError(['a', 'b', 'c'])

	def parse_A(self):
		if self.cur_tok in ['a']:
			self.match('a')
		elif self.cur_tok in ['b', 'c']:
			pass
		else:
			raise SyntacticalError(['a', 'b', 'c'])

	def parse_B(self):
		if self.cur_tok in ['b']:
			self.match('b')
		elif self.cur_tok in ['c']:
			pass
		else:
			raise SyntacticalError(['b', 'c'])

	def parse_C(self):
		if self.cur_tok in ['c']:
			self.match('c')
		else:
			raise SyntacticalError(['c'])

	def main(self):
		self.cur_tok = self.lexer.tokenize()
		print(self.cur_tok)
		self.parse_S()
