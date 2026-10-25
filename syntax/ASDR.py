from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer
from .ASDR_base import ASDR_base

class ASDR(ASDR_base):

	def parse_CHUNK(self):
		if self.cur_tok.type in ['$', 'break', 'do', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'while']:
			self.parse_BLOCK()
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "while"'))

	def parse_BLOCK(self):
		if self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'until', 'while']:
			self.parse_STATLIST()
			self.parse_RETSTAT()
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "until", "while"'))

	def parse_STATLIST(self):
		if self.cur_tok.type in ['break', 'do', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'while']:
			self.parse_STAT()
			self.parse_STATLIST()
		elif self.cur_tok.type in ['$', 'else', 'elseif', 'end', 'return', 'until']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "until", "while"'))

	def parse_STAT(self):
		if self.cur_tok.type in ['tkn_semicolon']:
			self.match('tkn_semicolon')
		elif self.cur_tok.type in ['id', 'tkn_opening_par']:
			self.parse_PREFIXEXP()
			self.parse_PREFIXEXP_NEXT()
		elif self.cur_tok.type in ['tkn_goto']:
			self.parse_LABEL()
		elif self.cur_tok.type in ['break']:
			self.match('break')
		elif self.cur_tok.type in ['goto']:
			self.match('goto')
			self.match('id')
		elif self.cur_tok.type in ['do']:
			self.parse_DO_BLOCK_END()
		elif self.cur_tok.type in ['while']:
			self.match('while')
			self.parse_EXP()
			self.parse_DO_BLOCK_END()
		elif self.cur_tok.type in ['repeat']:
			self.match('repeat')
			self.parse_BLOCK()
			self.match('until')
			self.parse_EXP()
		elif self.cur_tok.type in ['if']:
			self.parse_IFSTAT()
		elif self.cur_tok.type in ['for']:
			self.parse_FORSTAT()
		elif self.cur_tok.type in ['function']:
			self.match('function')
			self.parse_FUNCNAME()
			self.parse_FUNCBODY()
		elif self.cur_tok.type in ['local']:
			self.parse_LOCAL_DEC()
		elif self.cur_tok.type in ['global']:
			self.parse_GLOBAL_DEC()
		else:
			raise SyntacticalError(self.format_error_message('"break", "do", "for", "function", "global", "goto", "id", "if", "local", "repeat", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "while"'))

	def parse_LABEL(self):
		if self.cur_tok.type in ['tkn_goto']:
			self.match('tkn_goto')
			self.match('id')
			self.match('tkn_goto')
		else:
			raise SyntacticalError(self.format_error_message('"tkn_goto"'))

	def parse_DO_BLOCK_END(self):
		if self.cur_tok.type in ['do']:
			self.match('do')
			self.parse_BLOCK()
			self.match('end')
		else:
			raise SyntacticalError(self.format_error_message('"do"'))

	def parse_PREFIXEXP_NEXT(self):
		if self.cur_tok.type in ['tkn_assign', 'tkn_comma']:
			self.parse_MORE_VAR()
			self.match('tkn_assign')
			self.parse_EXPLIST()
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_assign", "tkn_comma", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "until", "while"'))

	def parse_IFSTAT(self):
		if self.cur_tok.type in ['if']:
			self.match('if')
			self.parse_EXP()
			self.match('then')
			self.parse_BLOCK()
			self.parse_ELSEIFSTAT()
			self.parse_ELSESTAT()
			self.match('end')
		else:
			raise SyntacticalError(self.format_error_message('"if"'))

	def parse_ELSEIFSTAT(self):
		if self.cur_tok.type in ['elseif']:
			self.match('elseif')
			self.parse_EXP()
			self.match('then')
			self.parse_BLOCK()
			self.parse_ELSEIFSTAT()
		elif self.cur_tok.type in ['else', 'end']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"else", "elseif", "end"'))

	def parse_ELSESTAT(self):
		if self.cur_tok.type in ['else']:
			self.match('else')
			self.parse_BLOCK()
		elif self.cur_tok.type in ['end']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"else", "end"'))

	def parse_FORSTAT(self):
		if self.cur_tok.type in ['for']:
			self.match('for')
			self.match('id')
			self.parse_FORTYPE()
			self.parse_DO_BLOCK_END()
		else:
			raise SyntacticalError(self.format_error_message('"for"'))

	def parse_FORTYPE(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.parse_NUMERICAL_FOR()
		elif self.cur_tok.type in ['in', 'tkn_comma']:
			self.parse_GENERIC_FOR()
		else:
			raise SyntacticalError(self.format_error_message('"in", "tkn_assign", "tkn_comma"'))

	def parse_NUMERICAL_FOR(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.match('tkn_assign')
			self.parse_EXP()
			self.match('tkn_comma')
			self.parse_EXP()
			self.parse_OPT_EXP()
		else:
			raise SyntacticalError(self.format_error_message('"tkn_assign"'))

	def parse_OPT_EXP(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_EXP()
		elif self.cur_tok.type in ['do']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"do", "tkn_comma"'))

	def parse_GENERIC_FOR(self):
		if self.cur_tok.type in ['in', 'tkn_comma']:
			self.parse_MORE_NAMES()
			self.match('in')
			self.parse_EXPLIST()
		else:
			raise SyntacticalError(self.format_error_message('"in", "tkn_comma"'))

	def parse_RETSTAT(self):
		if self.cur_tok.type in ['return']:
			self.match('return')
			self.parse_MAYBE_EXPLIST()
			self.parse_OPT_SEMILOCON()
		elif self.cur_tok.type in ['$', 'else', 'elseif', 'end', 'until']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "else", "elseif", "end", "return", "until"'))

	def parse_OPT_SEMILOCON(self):
		if self.cur_tok.type in ['tkn_semicolon']:
			self.match('tkn_semicolon')
		elif self.cur_tok.type in ['$', 'else', 'elseif', 'end', 'until']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "else", "elseif", "end", "tkn_semicolon", "until"'))

	def parse_TABLECONSTRUCTOR(self):
		if self.cur_tok.type in ['tkn_opening_key']:
			self.match('tkn_opening_key')
			self.parse_FIELDLIST()
			self.match('tkn_closing_key')
		else:
			raise SyntacticalError(self.format_error_message('"tkn_opening_key"'))

	def parse_FIELDLIST(self):
		if self.cur_tok.type in ['false', 'function', 'id', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_bra', 'tkn_opening_key', 'tkn_str', 'tkn_varargs', 'true']:
			self.parse_FIELD()
			self.parse_FIELD_TAIL()
		elif self.cur_tok.type in ['tkn_closing_key']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"false", "function", "id", "nil", "not", "tkn_closing_key", "tkn_length", "tkn_minus", "tkn_num", "tkn_opening_bra", "tkn_opening_key", "tkn_str", "tkn_varargs", "true"'))

	def parse_FIELD_TAIL(self):
		if self.cur_tok.type in ['tkn_comma', 'tkn_semicolon']:
			self.parse_FIELDSEP()
			self.parse_FIELDLIST()
		elif self.cur_tok.type in ['tkn_closing_key']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"tkn_closing_key", "tkn_comma", "tkn_semicolon"'))

	def parse_FIELDSEP(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
		elif self.cur_tok.type in ['tkn_semicolon']:
			self.match('tkn_semicolon')
		else:
			raise SyntacticalError(self.format_error_message('"tkn_comma", "tkn_semicolon"'))

	def parse_FIELD(self):
		if self.cur_tok.type in ['tkn_opening_bra']:
			self.match('tkn_opening_bra')
			self.parse_EXP()
			self.match('tkn_closing_bra')
			self.match('tkn_assign')
			self.parse_EXP()
		elif self.cur_tok.type in ['id']:
			self.match('id')
			self.match('tkn_assign')
			self.parse_EXP()
		elif self.cur_tok.type in ['false', 'function', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_str', 'tkn_varargs', 'true']:
			self.parse_EXP()
		else:
			raise SyntacticalError(self.format_error_message('"false", "function", "id", "nil", "not", "tkn_length", "tkn_minus", "tkn_num", "tkn_opening_bra", "tkn_opening_key", "tkn_str", "tkn_varargs", "true"'))

	def parse_LOCAL_DEC(self):
		if self.cur_tok.type in ['local']:
			self.match('local')
			self.parse_LOCAL_OPT()
		else:
			raise SyntacticalError(self.format_error_message('"local"'))

	def parse_LOCAL_OPT(self):
		if self.cur_tok.type in ['function']:
			self.parse_FUNC_DEC()
		elif self.cur_tok.type in ['id', 'tkn_less']:
			self.parse_ATTNAME_BRANCH()
		else:
			raise SyntacticalError(self.format_error_message('"function", "id", "tkn_less"'))

	def parse_ATTNAME_BRANCH(self):
		if self.cur_tok.type in ['id', 'tkn_less']:
			self.parse_ATTNAMELIST()
			self.parse_OPT_EXPLIST()
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_less"'))

	def parse_GLOBAL_DEC(self):
		if self.cur_tok.type in ['global']:
			self.match('global')
			self.parse_GLOBAL_OPT()
		else:
			raise SyntacticalError(self.format_error_message('"global"'))

	def parse_GLOBAL_OPT(self):
		if self.cur_tok.type in ['function']:
			self.parse_FUNC_DEC()
		elif self.cur_tok.type in ['id', 'tkn_less', 'tkn_times']:
			self.parse_ATTRIB()
			self.parse_GLOBAL_TAIL()
		else:
			raise SyntacticalError(self.format_error_message('"function", "id", "tkn_less", "tkn_times"'))

	def parse_GLOBAL_TAIL(self):
		if self.cur_tok.type in ['tkn_times']:
			self.match('tkn_times')
		elif self.cur_tok.type in ['id']:
			self.match('id')
			self.parse_ATTRIB()
			self.parse_NAME_ATTRIB_LIST()
			self.parse_OPT_EXPLIST()
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_times"'))

	def parse_FUNC_DEC(self):
		if self.cur_tok.type in ['function']:
			self.match('function')
			self.match('id')
			self.parse_FUNCBODY()
		else:
			raise SyntacticalError(self.format_error_message('"function"'))

	def parse_OPT_EXPLIST(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.match('tkn_assign')
			self.parse_EXPLIST()
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_assign", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "until", "while"'))

	def parse_ATTNAMELIST(self):
		if self.cur_tok.type in ['id', 'tkn_less']:
			self.parse_ATTRIB()
			self.match('id')
			self.parse_ATTRIB()
			self.parse_NAME_ATTRIB_LIST()
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_less"'))

	def parse_NAME_ATTRIB_LIST(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.match('id')
			self.parse_ATTRIB()
			self.parse_NAME_ATTRIB_LIST()
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_assign', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_assign", "tkn_comma", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "until", "while"'))

	def parse_ATTRIB(self):
		if self.cur_tok.type in ['tkn_less']:
			self.match('tkn_less')
			self.match('id')
			self.match('tkn_greater')
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_assign', 'tkn_comma', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'tkn_times', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_assign", "tkn_comma", "tkn_goto", "tkn_less", "tkn_opening_par", "tkn_semicolon", "tkn_times", "until", "while"'))

	def parse_FUNCNAME(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
			self.parse_DOTTED_FUNCNAME()
			self.parse_COLON_FUNCNAME()
		else:
			raise SyntacticalError(self.format_error_message('"id"'))

	def parse_DOTTED_FUNCNAME(self):
		if self.cur_tok.type in ['tkn_period']:
			self.match('tkn_period')
			self.match('id')
			self.parse_DOTTED_FUNCNAME()
		elif self.cur_tok.type in ['tkn_colon', 'tkn_opening_par']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"tkn_colon", "tkn_opening_par", "tkn_period"'))

	def parse_COLON_FUNCNAME(self):
		if self.cur_tok.type in ['tkn_colon']:
			self.match('tkn_colon')
			self.match('id')
		elif self.cur_tok.type in ['tkn_opening_par']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"tkn_colon", "tkn_opening_par"'))

	def parse_FUNCTIONDEF(self):
		if self.cur_tok.type in ['function']:
			self.match('function')
			self.parse_FUNCBODY()
		else:
			raise SyntacticalError(self.format_error_message('"function"'))

	def parse_FUNCBODY(self):
		if self.cur_tok.type in ['tkn_opening_par']:
			self.match('tkn_opening_par')
			self.parse_OPT_PARLIST()
			self.match('tkn_closing_par')
			self.parse_BLOCK()
			self.match('end')
		else:
			raise SyntacticalError(self.format_error_message('"tkn_opening_par"'))

	def parse_OPT_PARLIST(self):
		if self.cur_tok.type in ['id', 'tkn_varargs']:
			self.parse_PARLIST()
		elif self.cur_tok.type in ['tkn_closing_par']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_closing_par", "tkn_varargs"'))

	def parse_PARLIST(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
			self.parse_PARLIST_TAIL()
		elif self.cur_tok.type in ['tkn_varargs']:
			self.parse_VARPARAGRAM()
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_varargs"'))

	def parse_PARLIST_TAIL(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_PARLIST_AFTER_COMMA()
		elif self.cur_tok.type in ['tkn_closing_par']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"tkn_closing_par", "tkn_comma"'))

	def parse_PARLIST_AFTER_COMMA(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
			self.parse_PARLIST_TAIL()
		elif self.cur_tok.type in ['tkn_varargs']:
			self.parse_VARPARAGRAM()
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_varargs"'))

	def parse_VARPARAGRAM(self):
		if self.cur_tok.type in ['tkn_varargs']:
			self.match('tkn_varargs')
			self.parse_OPT_NAME()
		else:
			raise SyntacticalError(self.format_error_message('"tkn_varargs"'))

	def parse_OPT_NAME(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
		elif self.cur_tok.type in ['tkn_closing_par']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_closing_par"'))

	def parse_MORE_NAMES(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.match('id')
			self.parse_MORE_NAMES()
		elif self.cur_tok.type in ['in']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"in", "tkn_comma"'))

	def parse_MORE_VAR(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_PREFIXEXP()
			self.parse_MORE_VAR()
		elif self.cur_tok.type in ['tkn_assign']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"tkn_assign", "tkn_comma"'))

	def parse_MAYBE_EXPLIST(self):
		if self.cur_tok.type in ['false', 'function', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_str', 'tkn_varargs', 'true']:
			self.parse_EXPLIST()
		elif self.cur_tok.type in ['$', 'else', 'elseif', 'end', 'tkn_closing_par', 'tkn_semicolon', 'until']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "else", "elseif", "end", "false", "function", "nil", "not", "tkn_closing_par", "tkn_length", "tkn_minus", "tkn_num", "tkn_opening_key", "tkn_semicolon", "tkn_str", "tkn_varargs", "true", "until"'))

	def parse_EXPLIST(self):
		if self.cur_tok.type in ['false', 'function', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_str', 'tkn_varargs', 'true']:
			self.parse_EXP()
			self.parse_MORE_EXP()
		else:
			raise SyntacticalError(self.format_error_message('"false", "function", "nil", "not", "tkn_length", "tkn_minus", "tkn_num", "tkn_opening_key", "tkn_str", "tkn_varargs", "true"'))

	def parse_MORE_EXP(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_EXP()
			self.parse_MORE_EXP()
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_closing_par', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_closing_par", "tkn_comma", "tkn_goto", "tkn_opening_par", "tkn_semicolon", "until", "while"'))

	def parse_EXP(self):
		if self.cur_tok.type in ['nil']:
			self.match('nil')
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['false']:
			self.match('false')
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['true']:
			self.match('true')
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['tkn_num']:
			self.match('tkn_num')
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['tkn_str']:
			self.match('tkn_str')
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['tkn_varargs']:
			self.match('tkn_varargs')
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['tkn_opening_key']:
			self.parse_TABLECONSTRUCTOR()
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['function']:
			self.parse_FUNCTIONDEF()
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['not', 'tkn_length', 'tkn_minus']:
			self.parse_UNOP()
			self.parse_EXP()
		else:
			raise SyntacticalError(self.format_error_message('"false", "function", "nil", "not", "tkn_length", "tkn_minus", "tkn_num", "tkn_opening_key", "tkn_str", "tkn_varargs", "true"'))

	def parse_EXP_PRIME(self):
		if self.cur_tok.type in ['and', 'or', 'tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_concat', 'tkn_div', 'tkn_equal', 'tkn_floor_div', 'tkn_geq', 'tkn_greater', 'tkn_left_shift', 'tkn_leq', 'tkn_less', 'tkn_minus', 'tkn_mod', 'tkn_neq', 'tkn_plus', 'tkn_power', 'tkn_right_shift', 'tkn_times']:
			self.parse_BINOP()
			self.parse_EXP()
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'then', 'tkn_closing_bra', 'tkn_closing_key', 'tkn_closing_par', 'tkn_comma', 'tkn_goto', 'tkn_opening_par', 'tkn_semicolon', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "and", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "or", "repeat", "return", "then", "tkn_bit_and", "tkn_bit_or", "tkn_bitex_or", "tkn_closing_bra", "tkn_closing_key", "tkn_closing_par", "tkn_comma", "tkn_concat", "tkn_div", "tkn_equal", "tkn_floor_div", "tkn_geq", "tkn_goto", "tkn_greater", "tkn_left_shift", "tkn_leq", "tkn_less", "tkn_minus", "tkn_mod", "tkn_neq", "tkn_opening_par", "tkn_plus", "tkn_power", "tkn_right_shift", "tkn_semicolon", "tkn_times", "until", "while"'))

	def parse_PREFIXEXP(self):
		if self.cur_tok.type in ['tkn_opening_par']:
			self.match('tkn_opening_par')
			self.parse_EXP()
			self.match('tkn_closing_par')
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['id']:
			self.match('id')
			self.parse_PREFIXEXP_PRIME()
		else:
			raise SyntacticalError(self.format_error_message('"id", "tkn_opening_par"'))

	def parse_PREFIXEXP_PRIME(self):
		if self.cur_tok.type in ['tkn_opening_bra']:
			self.match('tkn_opening_bra')
			self.parse_EXP()
			self.match('tkn_closing_bra')
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['tkn_period']:
			self.match('tkn_period')
			self.match('id')
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['tkn_colon', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str']:
			self.parse_FUNCTIONCALL()
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['$', 'break', 'do', 'else', 'elseif', 'end', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'repeat', 'return', 'tkn_assign', 'tkn_comma', 'tkn_goto', 'tkn_semicolon', 'until', 'while']:
			pass
		else:
			raise SyntacticalError(self.format_error_message('"$", "break", "do", "else", "elseif", "end", "for", "function", "global", "goto", "id", "if", "local", "repeat", "return", "tkn_assign", "tkn_colon", "tkn_comma", "tkn_goto", "tkn_opening_bra", "tkn_opening_key", "tkn_opening_par", "tkn_period", "tkn_semicolon", "tkn_str", "until", "while"'))

	def parse_FUNCTIONCALL(self):
		if self.cur_tok.type in ['tkn_opening_key', 'tkn_opening_par', 'tkn_str']:
			self.parse_ARGS()
		elif self.cur_tok.type in ['tkn_colon']:
			self.match('tkn_colon')
			self.match('id')
			self.parse_ARGS()
		else:
			raise SyntacticalError(self.format_error_message('"tkn_colon", "tkn_opening_key", "tkn_opening_par", "tkn_str"'))

	def parse_ARGS(self):
		if self.cur_tok.type in ['tkn_opening_par']:
			self.match('tkn_opening_par')
			self.parse_MAYBE_EXPLIST()
			self.match('tkn_closing_par')
		elif self.cur_tok.type in ['tkn_opening_key']:
			self.parse_TABLECONSTRUCTOR()
		elif self.cur_tok.type in ['tkn_str']:
			self.match('tkn_str')
		else:
			raise SyntacticalError(self.format_error_message('"tkn_opening_key", "tkn_opening_par", "tkn_str"'))

	def parse_BINOP(self):
		if self.cur_tok.type in ['tkn_plus']:
			self.match('tkn_plus')
		elif self.cur_tok.type in ['tkn_minus']:
			self.match('tkn_minus')
		elif self.cur_tok.type in ['tkn_times']:
			self.match('tkn_times')
		elif self.cur_tok.type in ['tkn_div']:
			self.match('tkn_div')
		elif self.cur_tok.type in ['tkn_floor_div']:
			self.match('tkn_floor_div')
		elif self.cur_tok.type in ['tkn_power']:
			self.match('tkn_power')
		elif self.cur_tok.type in ['tkn_mod']:
			self.match('tkn_mod')
		elif self.cur_tok.type in ['tkn_bit_and']:
			self.match('tkn_bit_and')
		elif self.cur_tok.type in ['tkn_bitex_or']:
			self.match('tkn_bitex_or')
		elif self.cur_tok.type in ['tkn_bit_or']:
			self.match('tkn_bit_or')
		elif self.cur_tok.type in ['tkn_right_shift']:
			self.match('tkn_right_shift')
		elif self.cur_tok.type in ['tkn_left_shift']:
			self.match('tkn_left_shift')
		elif self.cur_tok.type in ['tkn_concat']:
			self.match('tkn_concat')
		elif self.cur_tok.type in ['tkn_less']:
			self.match('tkn_less')
		elif self.cur_tok.type in ['tkn_leq']:
			self.match('tkn_leq')
		elif self.cur_tok.type in ['tkn_greater']:
			self.match('tkn_greater')
		elif self.cur_tok.type in ['tkn_geq']:
			self.match('tkn_geq')
		elif self.cur_tok.type in ['tkn_equal']:
			self.match('tkn_equal')
		elif self.cur_tok.type in ['tkn_neq']:
			self.match('tkn_neq')
		elif self.cur_tok.type in ['and']:
			self.match('and')
		elif self.cur_tok.type in ['or']:
			self.match('or')
		else:
			raise SyntacticalError(self.format_error_message('"and", "or", "tkn_bit_and", "tkn_bit_or", "tkn_bitex_or", "tkn_concat", "tkn_div", "tkn_equal", "tkn_floor_div", "tkn_geq", "tkn_greater", "tkn_left_shift", "tkn_leq", "tkn_less", "tkn_minus", "tkn_mod", "tkn_neq", "tkn_plus", "tkn_power", "tkn_right_shift", "tkn_times"'))

	def parse_UNOP(self):
		if self.cur_tok.type in ['tkn_minus']:
			self.match('tkn_minus')
		elif self.cur_tok.type in ['not']:
			self.match('not')
		elif self.cur_tok.type in ['tkn_length']:
			self.match('tkn_length')
		else:
			raise SyntacticalError(self.format_error_message('"not", "tkn_length", "tkn_minus"'))

	def main(self):
		self.cur_tok = self.lexer.tokenize()
		self.parse_CHUNK()
		if self.cur_tok.type != "$":
			raise SyntacticalError(self.format_error_message("$"))
