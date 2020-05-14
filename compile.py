from __future__ import print_function
# from my_ast import dump
from my_compiler import MyCompiler
from flatten_ast import flatten

import parser
import sys

import my_ast as ast
from helper import SimpleStmt, Ops, Temporals


def get_arguments():
    args={}
    args['flatten'] = True if '--flatten' in sys.argv else False
    args['arch'] = 'macos' if '--mac' in sys.argv else 'unix'
    args['pseudo'] = True if '--pseudo' in sys.argv else False
    args['liveness'] = True if '--liveness' in sys.argv else False
    return args
    
var_types = {} # Store variable types when boxing

def boxing_fct_name(constant):
    value = constant.value if isinstance(constant, ast.Constant) else constant

    fct_name = ''
    if isinstance(value, int): fct_name += 'box_long'
    elif isinstance(value, bool): fct_name += 'box_bool'
    elif isinstance(value, float): fct_name += 'box_float'
    elif isinstance(value, str): fct_name += 'box_string'
    else: raise RuntimeError('Unrecognized constant type {}'.format(type(value)))
    return fct_name

def binops_return_type(v2, v3):
    # TODO
    return boxing_fct_name(1)

def box_vars(flatten_stmts):
    new_stmts = []
    for i, s in enumerate(flatten_stmts):
        if s._op == Ops.assign and isinstance(s._v2, ast.Constant):
            fct = boxing_fct_name(s._v2)
            var_types[s._v1.id] = fct
            stmt = SimpleStmt(Ops.call, fct, s._v2, s._v1)
            new_stmts.append(stmt)
        elif s._op == Ops.call and (isinstance(s._v2, ast.Name) or isinstance(s._v3, ast.Name)):
            temp2 = s._v2; temp3 = s._v3
            if isinstance(s._v2, ast.Name):
                temp2 = Temporals.generateTemp()
                unbox_fct = 'un' + var_types[s._v2.id]
                stmt = SimpleStmt(Ops.call, unbox_fct, s._v2, temp2)
                new_stmts.append(stmt)
            if isinstance(s._v3, ast.Name):
                temp3 = Temporals.generateTemp()

            stmt = SimpleStmt(Ops.call, s._v1, temp2, temp3)
            new_stmts.append(stmt)
            # Box back function return
            if isinstance(s._v3, ast.Name):
                if s._v1 == 'input':
                    box_fct = 'box_long' 
                else:
                    raise NotImplementedError() # TODO: accept other fct types
                var_types[s._v3.id] = box_fct
                stmt = SimpleStmt(Ops.call, box_fct, temp3, s._v3)
                new_stmts.append(stmt)
        elif s._op == Ops.cmp and (isinstance(s._v1, ast.Name) or isinstance(s._v2, ast.Name)):
            temp1 = s._v1; temp2 = s._v2
            if isinstance(s._v1, ast.Name):
                temp1 = Temporals.generateTemp()
                unbox_fct = 'un' + var_types[s._v1.id]
                stmt = SimpleStmt(Ops.call, unbox_fct, s._v1, temp1)
                new_stmts.append(stmt)
            if isinstance(s._v2, ast.Name):
                temp2 = Temporals.generateTemp()
                unbox_fct = 'un' + var_types[s._v2.id]
                stmt = SimpleStmt(Ops.call, unbox_fct, s._v2, temp2)
                new_stmts.append(stmt)
            stmt = SimpleStmt(Ops.cmp, temp1, temp2)
            new_stmts.append(stmt)
        elif s._op in Ops.bin_ops:
            temp1 = s._v1; temp2 = s._v2; temp3 = s._v3
            if isinstance(s._v2, ast.Name):
                temp2 = Temporals.generateTemp()
                unbox_fct = 'un' + var_types[s._v2.id]
                stmt = SimpleStmt(Ops.call, unbox_fct, s._v2, temp2)
                new_stmts.append(stmt)
            if isinstance(s._v3, ast.Name):
                temp3 = Temporals.generateTemp()
                unbox_fct = 'un' + var_types[s._v3.id]
                stmt = SimpleStmt(Ops.call, unbox_fct, s._v3, temp3)
                new_stmts.append(stmt)

            if isinstance(s._v1, ast.Name):
                temp1 = Temporals.generateTemp()
                # Chose type based on v2 and v3 # TODO: addition of different types
                box_fct = binops_return_type(s._v2, s._v3)
                var_types[s._v1.id] = box_fct
            stmt = SimpleStmt(s._op, temp1, temp2, temp3) # Binop
            new_stmts.append(stmt)
            if isinstance(s._v1, ast.Name): # Box back if necessary
                stmt = SimpleStmt(Ops.call, box_fct, temp1, s._v1)
                new_stmts.append(stmt)
        elif s._op == Ops.neg:
            temp1 = s._v1; temp2 = s._v2
            if isinstance(s._v2, ast.Name): # Unbox arg
                temp2 = Temporals.generateTemp()
                unbox_fct = 'un' + var_types[s._v2.id]
                stmt = SimpleStmt(Ops.call, unbox_fct, s._v2, temp2)
                new_stmts.append(stmt)
            if isinstance(s._v1, ast.Name):
                temp1 = Temporals.generateTemp()
                box_fct = var_types[s._v2.id]
                var_types[s._v1.id] = box_fct
            stmt = SimpleStmt(s._op, temp1, temp2)
            new_stmts.append(stmt)
            if isinstance(s._v1, ast.Name):
                stmt = SimpleStmt(Ops.call, box_fct, temp1, s._v1)
                new_stmts.append(stmt)
        else:
            new_stmts.append(s)
    return new_stmts


def main():
    code = ''
    try:
        f = open(sys.argv[1], 'r')
        code = f.read()
        f.close()
    except IOError as e:
        print(e)
        return
        
    t = parser.parse(code)
    # print (ast.dump(t))

    flatten_stmts = []
    flatten(t, flatten_stmts)
    args = get_arguments()
    # Flatten only
    if args['flatten']:
        print("\nflattened statements:")
        for i, s in enumerate(flatten_stmts):
            print(i, s)
        return

    # TODO: BOX/unbox variables
    flatten_stmts = box_vars(flatten_stmts)
    # DEBUG
    # print("\nflattened statements:")
    # for i, s in enumerate(flatten_stmts):
    #     print(i, s)
    # return
    
    # Generate x86
    MyCompiler(args['arch'], args['pseudo'], args['liveness']).compile_x86(flatten_stmts)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print('Usage: python compile.py <file.py> [flags]')
    else:
        main()
