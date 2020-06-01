from __future__ import print_function

import ply.yacc as yacc
import lexer
from lexer import tokens
import my_ast as ast


# Parsing rules

precedence = (
    ('left', 'or'),
    ('left', 'and'),
    ('left', 'BOR'),
    ('left', 'XOR'),
    ('left', 'BAND'),
    ('left', 'EQ', 'NEQ'),
    ('left', 'GT', 'GE', 'LT', 'LE', 'DEQ'),
    ('left', 'RSHIFT', 'LSHIFT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'MOD'),
    # ('left','PLUS','MINUS'),
    # ('left','TIMES','DIVIDE'),
    ('right','UMINUS'),
    )

def p_module(p):
    '''module : module statement
              | statement'''
    if len(p) == 2:
        p[0] = ast.Module(p[1])
    elif len(p) == 3:
        p[1].body.append(p[2])
        p[0] = p[1]
        
def p_suite_statement(p):
    '''suite : suite statement
             | statement'''
    # print('in suite')
    if len(p) == 2:
        p[0] = [ p[1] ]
    elif len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]

def p_statement_group(p):
    '''statement : expression
                  | newline statement
                  | statement newline'''
    if len(p) == 2 and isinstance(p[1], ast.AST):
        p[0] = ast.Expr(p[1])
    # Ignore blank lines before/after statement (shift-reduce conflict should not matter)
    elif len(p) == 3:
        if isinstance(p[1], ast.AST):
            p[0] = p[1]
        elif isinstance(p[2], ast.AST):
            p[0] = p[2]

def p_statement_pass(p):
    'statement : pass'
    p[0] = ast.Pass()

def p_statement_assign(p):
    'statement : identifier EQ expression'
    var = ast.Name(id_=p[1], ctx=ast.Store())
    p[0] = ast.Assign(target=var, value=p[3])

def p_statement_if(p):
    '''statement : if bool_expr colon newline indent suite dedent else colon newline indent suite dedent
                 | if bool_expr colon statement newline else colon statement newline'''
    # print('IF START, len(p)={}'.format(len(p)))
    if len(p) == 14:
        p[0] = ast.If(p[2], p[6], p[12])
    else:
        p[0] = ast.If(p[2], [ p[4] ], [ p[8] ])

def p_statement_while(p):
    '''statement : while bool_expr colon newline indent suite dedent'''
    # p[0] = ast.While(p[2], 0) # DEBUG
    p[0] = ast.While(p[2], p[6])

def p_expression_binop(p):
    '''expression : expression PLUS term
                  | expression MINUS term
                  | term'''
    if len(p) == 4:
        op = ast.Add() if p[2] == '+' else ast.Sub()
        lhs = p[1]; rhs = p[3]
        p[0] = ast.BinOp(left=p[1], op=op, right=p[3])

    elif len(p) == 2: # expression : term
        p[0] = p[1]
    else: 
        raise RuntimeError('Unknown pattern')

def p_expression_unary(p):
    'expression : MINUS expression %prec UMINUS'
    p[0] = ast.UnaryOp(op=ast.USub(), operand=p[2])

def p_expression_bool_expr(p):
    '''expression : bool_expr'''
    p[0] = p[1]

def p_bool_expr_end(p):
    '''bool_term : True
                 | False'''
    p[0] = ast.Constant(p[1])

def p_bool_expr_compare(p):
    '''bool_term : expression DEQ expression
                  | expression NEQ expression
                  | expression GT expression
                  | expression GE expression
                  | expression LT expression
                  | expression LE expression
                  | oparen bool_expr cparen
                  | not bool_term %prec UMINUS'''
    if p[1] == '(':
        p[0] = p[2]
        return
    if p[1] == 'not':
        p[0] = ast.UnaryOp(op=ast.Not(), operand=p[2])
        return
    if p[2] == '==': op = ast.Eq()
    elif p[2] == '!=': op = ast.NotEq()
    elif p[2] == '>': op = ast.Gt()
    elif p[2] == '>=': op = ast.GtE()
    elif p[2] == '<': op = ast.Lt()
    elif p[2] == '<=': op = ast.LtE()
    else: raise RuntimeError('unknown operation')

    p[0] = ast.Compare(left=p[1], op=op, right=p[3])

def p_bool_expr_arithmetic(p):
    '''bool_expr : bool_expr or bool_term
                  | bool_expr and bool_term
                  | bool_term'''
    if len(p) == 2: # bool_expr : term
        p[0] = p[1]
    else: # and/or
        op = ast.And() if p[2] == 'and' else ast.Or()
        p[0] = ast.BoolOp(op=op, values=[p[1], p[3]])

# def p_bool_expr_bitwise_artihm(p):
#     '''bool_expr : bool_expr BOR bool_expr
#                  | bool_expr XOR bool_expr
#                  | bool_expr BAND bool_expr'''
#     raise NotImplementedError('')
#     if p[2] == '&': op = ast.BitAnd()
#     elif p[2] == '|': op = ast.BitOr()
#     elif p[2] == '^': op = ast.BitXor()

def p_term_binop(p):
    '''term : term TIMES factor
            | term DIVIDE factor
            | term MOD factor
            | factor'''
    if len(p) == 4:
        if p[2] == '*': op = ast.Mul()
        elif p[2] == '/': op = ast.Div()
        elif p[2] == '%': op = ast.Mod()
        else: raise RuntimeError('Unricognized operation')
        p[0] = ast.BinOp(op, p[1], p[3])
    elif len(p) == 2:
        p[0] = p[1]

def p_factor_expr(p):
    'factor : oparen expression cparen'
    p[0] = p[2]

def p_factor_signed(p):
    'factor : MINUS factor %prec UMINUS'
    p[0] = ast.UnaryOp(op=ast.USub(), operand=p[2])

def p_factor_number_name_call(p):
    '''factor : number
              | name
              | call'''
    p[0] = p[1]

def p_factor_list(p):
    '''factor : obracket cbracket
              | obracket series cbracket
              | name obracket integer cbracket'''
    if len(p) == 3:
        p[0] = ast.List()
    elif len(p) == 4:
        pass # TODO accept multiple expr separated by commas
        p[0] = ast.List(p[2])
    elif len(p) == 5:
        p[0] = ast.Subscript(p[1], p[3])

def p_series_expr(p):
    '''series : series comma expression
              | expression'''
    # if len(p) == 2:
    #     p[0] = [ p[1] ]
    # elif len(p) == 4:
    #     p[0].append(p[3])
    if len(p) == 2:
        p[0] = [ p[1] ]
    elif len(p) == 4:
        p[0].append(p[3])

# In case we have to add float numbers
def p_number(p):
    'number : integer'
    p[0] = ast.Constant(int(p[1]))

def p_name_identifier(p):
    '''name : identifier'''
    p[0] = ast.Name(id_=p[1], ctx=ast.Load())

def p_call(p):
    '''call : identifier oparen cparen
            | identifier oparen expression cparen'''
    if len(p) == 4: # Call, no args
        name = ast.Name(id_=p[1],ctx=ast.Load())
        p[0] = ast.Call(func=name)
    elif len(p) == 5: # Call, 1 argument
        name = ast.Name(id_=p[1], ctx=ast.Load())
        p[0] = ast.Call(func=name,args=[p[3]])
    

def p_error(p):
    raise(SyntaxError())

def parse(file):
    myLex = lexer.init_lexer()
    myLex.input(file)

    myParser = yacc.yacc()
    
    result = myParser.parse(lexer=myLex)
    return result
    

if __name__ == '__main__':
    t = ast.Module()
    print(t)