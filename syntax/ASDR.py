from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer
from .ASDR_base import ASDR_base

class ASDR(ASDR_base):

	def parse_S(self):
		if self.cur_tok.type in ['$', 'id', 'tnk_num', 'tnk_str']:
			self.parse_A()
			self.parse_B()
			self.parse_C()
		else:
			raise SyntacticalError(self.format_error_message(['$', 'id', 'tnk_num', 'tnk_str']))

	def parse_A(self):
		if self.cur_tok.type in ['tnk_str']:
			self.match('tnk_str')
		elif self.cur_tok.type in ['$', 'id', 'tnk_num']:
			pass
		else:
			raise SyntacticalError(self.format_error_message(['$', 'id', 'tnk_num', 'tnk_str']))

	def parse_B(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
		elif self.cur_tok.type in ['$', 'tnk_num']:
			pass
		else:
			raise SyntacticalError(self.format_error_message(['$', 'id', 'tnk_num']))

	def parse_C(self):
		if self.cur_tok.type in ['tnk_num']:
			self.match('tnk_num')
		elif self.cur_tok.type in ['$']:
			pass
		else:
			raise SyntacticalError(self.format_error_message(['$', 'tnk_num']))

	def main(self):
		self.cur_tok = self.lexer.tokenize()
		self.parse_S()
		if self.cur_tok.type != "$":
			raise SyntacticalError(self.format_error_messge("$"))
