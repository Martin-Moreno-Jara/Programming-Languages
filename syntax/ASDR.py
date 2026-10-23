from ASDR_base import ASDR_base

class ASDR(ASDR_base):

	def parse_A(self):
		if self.cur_tok in ['big', 'bus', 'cat', 'cow']:
			self.parse_B()
			self.parse_C()
		elif self.cur_tok in ['ant']:
			self.match('ant')
		else:
			raise SyntacticalError(['ant', 'big', 'bus', 'cat', 'cow'])

	def parse_B(self):
		if self.cur_tok in ['big']:
			self.match('big')
		elif self.cur_tok in ['bus']:
			self.match('bus')
		elif self.cur_tok in ['cat', 'cow']:
			pass
		else:
			raise SyntacticalError(['big', 'bus', 'cat', 'cow'])

	def parse_C(self):
		if self.cur_tok in ['cat']:
			self.match('cat')
		elif self.cur_tok in ['cow']:
			self.match('cow')
		else:
			raise SyntacticalError(['cat', 'cow'])

