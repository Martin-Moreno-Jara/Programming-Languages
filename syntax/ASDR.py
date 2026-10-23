from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer
from .ASDR_base import ASDR_base

class ASDR(ASDR_base):

	def parse_CHUNK(self):
		if self.cur_tok.type in ['id']:
			self.parse_VARDEC()
		else:
			raise SyntacticalError(self.format_error_message('"id"'))

	def parse_VARDEC(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
			self.match('tkn_assign')
			self.parse_DATATYPE()
		else:
			raise SyntacticalError(self.format_error_message('"id"'))

	def parse_DATATYPE(self):
		if self.cur_tok.type in ['tkn_str']:
			self.match('tkn_str')
		elif self.cur_tok.type in ['tkn_num']:
			self.match('tkn_num')
		elif self.cur_tok.type in ['id']:
			self.match('id')
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_num", "tkn_str"'))

	def main(self):
		self.cur_tok = self.lexer.tokenize()
		self.parse_CHUNK()
		if self.cur_tok.type != "$":
			raise SyntacticalError(self.format_error_message("$"))
