from exceptions.custom_exceptions import SyntacticalError
from lexer.lexer import Lexer
from .ASDR_base import ASDR_base

class ASDR(ASDR_base):

	def parse_CHUNK(self):
		self.parse_BLOCK()

	def parse_BLOCK(self):
		self.parse_STATLIST()
		self.parse_RETSTAT()

	def parse_STATLIST(self):
		if self.cur_tok.type in ['break', 'error', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'pcall', 'print', 'repeat', 'tkn_goto', 'tkn_semicolon', 'warn', 'while', 'xpcall']:
			self.parse_STAT()
			self.parse_STATLIST()
		else:
			self.pending|=set(['break', 'error', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'pcall', 'print', 'repeat', 'tkn_goto', 'tkn_semicolon', 'warn', 'while', 'xpcall'])

	def parse_STAT(self):
		if self.cur_tok.type in ['tkn_semicolon']:
			self.match('tkn_semicolon')
		elif self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_VAR_STAT()
		elif self.cur_tok.type in ['tkn_goto']:
			self.parse_LABEL()
		elif self.cur_tok.type in ['break']:
			self.match('break')
		elif self.cur_tok.type in ['goto']:
			self.match('goto')
			self.parse_NAME()
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
			self.pending|=set(['break', 'error', 'for', 'function', 'global', 'goto', 'id', 'if', 'local', 'pcall', 'print', 'repeat', 'tkn_goto', 'tkn_semicolon', 'warn', 'while', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_LABEL(self):
		if self.cur_tok.type in ['tkn_goto']:
			self.match('tkn_goto')
			self.parse_NAME()
			self.match('tkn_goto')
		else:
			self.pending|=set(['tkn_goto'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_DO_BLOCK_END(self):
		if self.cur_tok.type in ['do']:
			self.match('do')
			self.parse_BLOCK()
			self.match('end')
		else:
			self.pending|=set(['do'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_VAR_STAT(self):
		if self.cur_tok.type in ['tkn_opening_bra']:
			self.match('tkn_opening_bra')
			self.parse_EXP()
			self.match('tkn_closing_bra')
			self.parse_VAR_STAT()
		elif self.cur_tok.type in ['tkn_period']:
			self.match('tkn_period')
			self.parse_NAME()
			self.parse_VAR_STAT()
		elif self.cur_tok.type in ['tkn_colon', 'tkn_opening_par']:
			self.parse_FUNCTIONCALL()
			self.parse_FUNCALL_STAT()
		elif self.cur_tok.type in ['tkn_assign', 'tkn_comma']:
			self.parse_MORE_VAR()
			self.match('tkn_assign')
			self.parse_EXPLIST()
		else:
			self.pending|=set(['tkn_assign', 'tkn_colon', 'tkn_comma', 'tkn_opening_bra', 'tkn_opening_par', 'tkn_period'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FUNCALL_STAT(self):
		if self.cur_tok.type in ['tkn_opening_bra']:
			self.match('tkn_opening_bra')
			self.parse_EXP()
			self.match('tkn_closing_bra')
			self.parse_VAR_STAT()
		elif self.cur_tok.type in ['tkn_period']:
			self.match('tkn_period')
			self.parse_NAME()
			self.parse_VAR_STAT()
		elif self.cur_tok.type in ['tkn_colon', 'tkn_opening_par']:
			self.parse_FUNCTIONCALL()
			self.parse_FUNCALL_STAT()
		else:
			self.pending|=set(['tkn_colon', 'tkn_opening_bra', 'tkn_opening_par', 'tkn_period'])

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
			self.pending|=set(['if'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_ELSEIFSTAT(self):
		if self.cur_tok.type in ['elseif']:
			self.match('elseif')
			self.parse_EXP()
			self.match('then')
			self.parse_BLOCK()
			self.parse_ELSEIFSTAT()
		else:
			self.pending|=set(['elseif'])

	def parse_ELSESTAT(self):
		if self.cur_tok.type in ['else']:
			self.match('else')
			self.parse_BLOCK()
		else:
			self.pending|=set(['else'])

	def parse_FORSTAT(self):
		if self.cur_tok.type in ['for']:
			self.match('for')
			self.parse_NAME()
			self.parse_FORTYPE()
			self.parse_DO_BLOCK_END()
		else:
			self.pending|=set(['for'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FORTYPE(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.parse_NUMERICAL_FOR()
		elif self.cur_tok.type in ['in', 'tkn_comma']:
			self.parse_GENERIC_FOR()
		else:
			self.pending|=set(['in', 'tkn_assign', 'tkn_comma'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_NUMERICAL_FOR(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.match('tkn_assign')
			self.parse_EXP()
			self.match('tkn_comma')
			self.parse_EXP()
			self.parse_OPT_EXP()
		else:
			self.pending|=set(['tkn_assign'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_OPT_EXP(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_EXP()
		else:
			self.pending|=set(['tkn_comma'])

	def parse_GENERIC_FOR(self):
		if self.cur_tok.type in ['in', 'tkn_comma']:
			self.parse_MORE_NAMES()
			self.match('in')
			self.parse_EXPLIST()
		else:
			self.pending|=set(['in', 'tkn_comma'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_RETSTAT(self):
		if self.cur_tok.type in ['return']:
			self.match('return')
			self.parse_MAYBE_EXPLIST()
			self.parse_OPT_SEMILOCON()
		else:
			self.pending|=set(['return'])

	def parse_OPT_SEMILOCON(self):
		if self.cur_tok.type in ['tkn_semicolon']:
			self.match('tkn_semicolon')
		else:
			self.pending|=set(['tkn_semicolon'])

	def parse_LOCAL_DEC(self):
		if self.cur_tok.type in ['local']:
			self.match('local')
			self.parse_LOCAL_OPTS()
		else:
			self.pending|=set(['local'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_LOCAL_OPTS(self):
		if self.cur_tok.type in ['function']:
			self.parse_FUNC_DEC()
		elif self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_ATTNAME_BRANCH()
		else:
			self.pending|=set(['error', 'function', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_ATTNAME_BRANCH(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_ATTNAMELIST()
			self.parse_OPT_EXPLIST()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_GLOBAL_DEC(self):
		if self.cur_tok.type in ['global']:
			self.match('global')
			self.parse_GLOBAL_OPTS()
		else:
			self.pending|=set(['global'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_GLOBAL_OPTS(self):
		if self.cur_tok.type in ['function']:
			self.parse_FUNC_DEC()
		elif self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_ATTNAMELIST()
			self.parse_OPT_EXPLIST()
		else:
			self.pending|=set(['error', 'function', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FUNC_DEC(self):
		if self.cur_tok.type in ['function']:
			self.match('function')
			self.parse_NAME()
			self.parse_FUNCBODY()
		else:
			self.pending|=set(['function'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_OPT_EXPLIST(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.match('tkn_assign')
			self.parse_EXPLIST()
		else:
			self.pending|=set(['tkn_assign'])

	def parse_ATTNAMELIST(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_ATTRIB()
			self.parse_NAME_ATTRIB_LIST()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_NAME_ATTRIB_LIST(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_NAME()
			self.parse_ATTRIB()
			self.parse_NAME_ATTRIB_LIST()
		else:
			self.pending|=set(['tkn_comma'])

	def parse_ATTRIB(self):
		if self.cur_tok.type in ['tkn_less']:
			self.match('tkn_less')
			self.parse_NAME()
			self.match('tkn_greater')
		else:
			self.pending|=set(['tkn_less'])

	def parse_FUNCNAME(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_DOTTED_FUNCNAME()
			self.parse_COLON_FUNCNAME()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_DOTTED_FUNCNAME(self):
		if self.cur_tok.type in ['tkn_period']:
			self.match('tkn_period')
			self.parse_NAME()
			self.parse_DOTTED_FUNCNAME()
		else:
			self.pending|=set(['tkn_period'])

	def parse_COLON_FUNCNAME(self):
		if self.cur_tok.type in ['tkn_colon']:
			self.match('tkn_colon')
			self.parse_NAME()
		else:
			self.pending|=set(['tkn_colon'])

	def parse_FUNCTIONDEF(self):
		if self.cur_tok.type in ['function']:
			self.match('function')
			self.parse_FUNCBODY()
		else:
			self.pending|=set(['function'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FUNCBODY(self):
		if self.cur_tok.type in ['tkn_opening_par']:
			self.match('tkn_opening_par')
			self.parse_OPT_PARLIST()
			self.match('tkn_closing_par')
			self.parse_BLOCK()
			self.match('end')
		else:
			self.pending|=set(['tkn_opening_par'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_OPT_PARLIST(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'tkn_varargs', 'warn', 'xpcall']:
			self.parse_PARLIST()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'tkn_varargs', 'warn', 'xpcall'])

	def parse_PARLIST(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_PARLIST_TAIL()
		elif self.cur_tok.type in ['tkn_varargs']:
			self.parse_VARPARAGRAM()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'tkn_varargs', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_PARLIST_TAIL(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_PARLIST_AFTER_COMMA()
		else:
			self.pending|=set(['tkn_comma'])

	def parse_PARLIST_AFTER_COMMA(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_PARLIST_TAIL()
		elif self.cur_tok.type in ['tkn_varargs']:
			self.parse_VARPARAGRAM()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'tkn_varargs', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_VARPARAGRAM(self):
		if self.cur_tok.type in ['tkn_varargs']:
			self.match('tkn_varargs')
			self.parse_OPT_NAME()
		else:
			self.pending|=set(['tkn_varargs'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_OPT_NAME(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'warn', 'xpcall'])

	def parse_MORE_NAMES(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_NAME()
			self.parse_MORE_NAMES()
		else:
			self.pending|=set(['tkn_comma'])

	def parse_MORE_VAR(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_PREFIXEXP()
			self.parse_MORE_VAR()
		else:
			self.pending|=set(['tkn_comma'])

	def parse_MAYBE_EXPLIST(self):
		if self.cur_tok.type in ['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_EXPLIST()
		else:
			self.pending|=set(['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])

	def parse_EXPLIST(self):
		if self.cur_tok.type in ['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_EXPLIST_ITEM()
			self.parse_MORE_EXP()
		else:
			self.pending|=set(['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_MORE_EXP(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
			self.parse_EXPLIST_ITEM()
			self.parse_MORE_EXP()
		else:
			self.pending|=set(['tkn_comma'])

	def parse_EXPLIST_ITEM(self):
		if self.cur_tok.type in ['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_EXP()
		elif self.cur_tok.type in ['function']:
			self.parse_FUNCTIONDEF()
		else:
			self.pending|=set(['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_EXP(self):
		if self.cur_tok.type in ['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_OPERAND()
			self.parse_EXP_PRIME()
		else:
			self.pending|=set(['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_OPERAND_NOT_ID(self):
		if self.cur_tok.type in ['nil']:
			self.match('nil')
		elif self.cur_tok.type in ['false']:
			self.match('false')
		elif self.cur_tok.type in ['true']:
			self.match('true')
		elif self.cur_tok.type in ['tkn_num']:
			self.match('tkn_num')
		elif self.cur_tok.type in ['tkn_str']:
			self.match('tkn_str')
		elif self.cur_tok.type in ['tkn_opening_key']:
			self.parse_TABLECONSTRUCTOR()
		elif self.cur_tok.type in ['not', 'tkn_length', 'tkn_minus']:
			self.parse_UNOP()
			self.parse_OPERAND()
		elif self.cur_tok.type in ['tkn_opening_par']:
			self.match('tkn_opening_par')
			self.parse_EXP()
			self.match('tkn_closing_par')
		else:
			self.pending|=set(['false', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_EXP_PRIME(self):
		self.parse_ARITH_TAIL()
		self.parse_CMP_TAIL()
		self.parse_LOGIC_TAIL()

	def parse_OPERAND(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['false', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true']:
			self.parse_OPERAND_NOT_ID()
		else:
			self.pending|=set(['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_PREFIXEXP(self):
		if self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_PREFIXEXP_PRIME()
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_PREFIXEXP_PRIME(self):
		if self.cur_tok.type in ['tkn_opening_bra']:
			self.match('tkn_opening_bra')
			self.parse_EXP()
			self.match('tkn_closing_bra')
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['tkn_period']:
			self.match('tkn_period')
			self.parse_NAME()
			self.parse_PREFIXEXP_PRIME()
		elif self.cur_tok.type in ['tkn_colon', 'tkn_opening_par']:
			self.parse_FUNCTIONCALL()
			self.parse_PREFIXEXP_PRIME()
		else:
			self.pending|=set(['tkn_colon', 'tkn_opening_bra', 'tkn_opening_par', 'tkn_period'])

	def parse_FUNCTIONCALL(self):
		if self.cur_tok.type in ['tkn_opening_par']:
			self.parse_ARGS()
		elif self.cur_tok.type in ['tkn_colon']:
			self.match('tkn_colon')
			self.parse_NAME()
			self.parse_ARGS()
		else:
			self.pending|=set(['tkn_colon', 'tkn_opening_par'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_ARGS(self):
		if self.cur_tok.type in ['tkn_opening_par']:
			self.match('tkn_opening_par')
			self.parse_MAYBE_EXPLIST()
			self.match('tkn_closing_par')
		else:
			self.pending|=set(['tkn_opening_par'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_TABLECONSTRUCTOR(self):
		if self.cur_tok.type in ['tkn_opening_key']:
			self.match('tkn_opening_key')
			self.parse_FIELDLIST()
			self.match('tkn_closing_key')
		else:
			self.pending|=set(['tkn_opening_key'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FIELDLIST(self):
		if self.cur_tok.type in ['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_bra', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_FIELD()
			self.parse_FIELD_TAIL()
		else:
			self.pending|=set(['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_bra', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])

	def parse_FIELD_TAIL(self):
		if self.cur_tok.type in ['tkn_comma', 'tkn_semicolon']:
			self.parse_FIELDSEP()
			self.parse_FIELDLIST()
		else:
			self.pending|=set(['tkn_comma', 'tkn_semicolon'])

	def parse_FIELD(self):
		if self.cur_tok.type in ['tkn_opening_bra']:
			self.match('tkn_opening_bra')
			self.parse_EXP()
			self.match('tkn_closing_bra')
			self.match('tkn_assign')
			self.parse_FIELD_VALUE()
		elif self.cur_tok.type in ['error', 'id', 'pcall', 'print', 'warn', 'xpcall']:
			self.parse_NAME()
			self.parse_FIELD_ID()
		elif self.cur_tok.type in ['false', 'nil', 'not', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true']:
			self.parse_OPERAND_NOT_ID()
			self.parse_EXP_PRIME()
		elif self.cur_tok.type in ['function']:
			self.parse_FUNCTIONDEF()
		else:
			self.pending|=set(['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_bra', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FIELD_ID(self):
		if self.cur_tok.type in ['tkn_assign']:
			self.match('tkn_assign')
			self.parse_FIELD_VALUE()
		elif self.cur_tok.type in ['and', 'or', 'tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_closing_key', 'tkn_colon', 'tkn_comma', 'tkn_concat', 'tkn_div', 'tkn_equal', 'tkn_floor_div', 'tkn_geq', 'tkn_greater', 'tkn_left_shift', 'tkn_leq', 'tkn_less', 'tkn_minus', 'tkn_mod', 'tkn_neq', 'tkn_opening_bra', 'tkn_opening_par', 'tkn_period', 'tkn_plus', 'tkn_power', 'tkn_right_shift', 'tkn_semicolon', 'tkn_times']:
			self.parse_PREFIXEXP_PRIME()
			self.parse_EXP_PRIME()
		else:
			self.pending|=set(['and', 'or', 'tkn_assign', 'tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_colon', 'tkn_concat', 'tkn_div', 'tkn_equal', 'tkn_floor_div', 'tkn_geq', 'tkn_greater', 'tkn_left_shift', 'tkn_leq', 'tkn_less', 'tkn_minus', 'tkn_mod', 'tkn_neq', 'tkn_opening_bra', 'tkn_opening_par', 'tkn_period', 'tkn_plus', 'tkn_power', 'tkn_right_shift', 'tkn_times'])

	def parse_FIELD_VALUE(self):
		if self.cur_tok.type in ['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_EXP()
		elif self.cur_tok.type in ['function']:
			self.parse_FUNCTIONDEF()
		else:
			self.pending|=set(['error', 'false', 'function', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FIELDSEP(self):
		if self.cur_tok.type in ['tkn_comma']:
			self.match('tkn_comma')
		elif self.cur_tok.type in ['tkn_semicolon']:
			self.match('tkn_semicolon')
		else:
			self.pending|=set(['tkn_comma', 'tkn_semicolon'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_LOGIC_TAIL(self):
		if self.cur_tok.type in ['and', 'or']:
			self.parse_LOGICAL_OP()
			self.parse_CMP_EXP()
			self.parse_LOGIC_TAIL()
		else:
			self.pending|=set(['and', 'or'])

	def parse_CMP_EXP(self):
		if self.cur_tok.type in ['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_ARTH_EXP()
			self.parse_CMP_TAIL()
		else:
			self.pending|=set(['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_CMP_TAIL(self):
		if self.cur_tok.type in ['tkn_equal', 'tkn_geq', 'tkn_greater', 'tkn_leq', 'tkn_less', 'tkn_neq']:
			self.parse_RELATIONAL_OP()
			self.parse_ARTH_EXP()
		else:
			self.pending|=set(['tkn_equal', 'tkn_geq', 'tkn_greater', 'tkn_leq', 'tkn_less', 'tkn_neq'])

	def parse_ARTH_EXP(self):
		if self.cur_tok.type in ['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall']:
			self.parse_OPERAND()
			self.parse_ARITH_TAIL()
		else:
			self.pending|=set(['error', 'false', 'id', 'nil', 'not', 'pcall', 'print', 'tkn_length', 'tkn_minus', 'tkn_num', 'tkn_opening_key', 'tkn_opening_par', 'tkn_str', 'true', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_ARITH_TAIL(self):
		if self.cur_tok.type in ['tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_concat', 'tkn_div', 'tkn_floor_div', 'tkn_left_shift', 'tkn_minus', 'tkn_mod', 'tkn_plus', 'tkn_power', 'tkn_right_shift', 'tkn_times']:
			self.parse_FLAT_OP()
			self.parse_OPERAND()
			self.parse_ARITH_TAIL()
		else:
			self.pending|=set(['tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_concat', 'tkn_div', 'tkn_floor_div', 'tkn_left_shift', 'tkn_minus', 'tkn_mod', 'tkn_plus', 'tkn_power', 'tkn_right_shift', 'tkn_times'])

	def parse_ARITH_OP(self):
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
		else:
			self.pending|=set(['tkn_div', 'tkn_floor_div', 'tkn_minus', 'tkn_mod', 'tkn_plus', 'tkn_power', 'tkn_times'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_RELATIONAL_OP(self):
		if self.cur_tok.type in ['tkn_less']:
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
		else:
			self.pending|=set(['tkn_equal', 'tkn_geq', 'tkn_greater', 'tkn_leq', 'tkn_less', 'tkn_neq'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_LOGICAL_OP(self):
		if self.cur_tok.type in ['and']:
			self.match('and')
		elif self.cur_tok.type in ['or']:
			self.match('or')
		else:
			self.pending|=set(['and', 'or'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_BITWISE_OP(self):
		if self.cur_tok.type in ['tkn_bit_and']:
			self.match('tkn_bit_and')
		elif self.cur_tok.type in ['tkn_bitex_or']:
			self.match('tkn_bitex_or')
		elif self.cur_tok.type in ['tkn_bit_or']:
			self.match('tkn_bit_or')
		elif self.cur_tok.type in ['tkn_right_shift']:
			self.match('tkn_right_shift')
		elif self.cur_tok.type in ['tkn_left_shift']:
			self.match('tkn_left_shift')
		else:
			self.pending|=set(['tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_left_shift', 'tkn_right_shift'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_OTHER_OP(self):
		if self.cur_tok.type in ['tkn_concat']:
			self.match('tkn_concat')
		else:
			self.pending|=set(['tkn_concat'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_FLAT_OP(self):
		if self.cur_tok.type in ['tkn_div', 'tkn_floor_div', 'tkn_minus', 'tkn_mod', 'tkn_plus', 'tkn_power', 'tkn_times']:
			self.parse_ARITH_OP()
		elif self.cur_tok.type in ['tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_left_shift', 'tkn_right_shift']:
			self.parse_BITWISE_OP()
		elif self.cur_tok.type in ['tkn_concat']:
			self.parse_OTHER_OP()
		else:
			self.pending|=set(['tkn_bit_and', 'tkn_bit_or', 'tkn_bitex_or', 'tkn_concat', 'tkn_div', 'tkn_floor_div', 'tkn_left_shift', 'tkn_minus', 'tkn_mod', 'tkn_plus', 'tkn_power', 'tkn_right_shift', 'tkn_times'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_UNOP(self):
		if self.cur_tok.type in ['tkn_minus']:
			self.match('tkn_minus')
		elif self.cur_tok.type in ['not']:
			self.match('not')
		elif self.cur_tok.type in ['tkn_length']:
			self.match('tkn_length')
		else:
			self.pending|=set(['not', 'tkn_length', 'tkn_minus'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def parse_NAME(self):
		if self.cur_tok.type in ['id']:
			self.match('id')
		elif self.cur_tok.type in ['print']:
			self.match('print')
		elif self.cur_tok.type in ['pcall']:
			self.match('pcall')
		elif self.cur_tok.type in ['error']:
			self.match('error')
		elif self.cur_tok.type in ['warn']:
			self.match('warn')
		elif self.cur_tok.type in ['xpcall']:
			self.match('xpcall')
		else:
			self.pending|=set(['error', 'id', 'pcall', 'print', 'warn', 'xpcall'])
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))

	def main(self):
		self.cur_tok = self.lexer.tokenize()
		self.parse_CHUNK()
		if self.cur_tok.type != "$":
			self.pending|={"$"}
			raise SyntacticalError(self.format_error_message(self.report_expected_symbols()))
