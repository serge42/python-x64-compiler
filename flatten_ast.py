from __future__ import print_function
from helper import Ops, Temporals, SimpleStmt, Labels

import my_ast as ast


def flatten_if_test(t, flatten_stmts, labels, op_type='and', nextLabel=None):
    assert isinstance(t, ast.Name) \
            or isinstance(t, ast.Compare) \
            or isinstance(t, ast.BoolOp), \
            "Test should be either True/False or bool_expr; received {}".format(type(t))
    if_body, else_body, end_if = labels
    if isinstance(t, ast.BoolOp):
        # Chain comparisons, recursive call
        # otype = 'and' if isinstance(t.op, ast.And) else 'or'
        # [flatten_if_test(x, flatten_stmts, labels, op_type=otype) for x in t.values]
        for i in range(len(t.values)):
            if isinstance(t.op, ast.Or):
                if isinstance(t.values[i], ast.BoolOp):
                    nextLabel = Labels.nextLabel()
                    flatten_if_test(t.values[i], flatten_stmts, labels, op_type='or', nextLabel=nextLabel)
                    flatten_stmts.append(SimpleStmt(Ops.jmp, if_body)) # Jump over or clause if previous clause is True
                    flatten_stmts.append(SimpleStmt(Ops.label, nextLabel))
                else:
                    flatten_if_test(t.values[i], flatten_stmts, labels, op_type='or')
            else:
                flatten_if_test(t.values[i], flatten_stmts, labels,  op_type='and', nextLabel=nextLabel)
        # if nextLabel and isinstance(t.op, ast.Or):
        #     flatten_stmts.append(SimpleStmt(Ops.label, nextLabel))
    elif isinstance(t, ast.Compare):
        s1 = SimpleStmt(Ops.cmp, t.right, t.left)
        if op_type == 'and':
            lbl = nextLabel if nextLabel else else_body
            s2 = SimpleStmt(Ops.comparison2jmp_inversed(t.op), lbl)
        else: 
            s2 = SimpleStmt(Ops.comparison2jmp(t.op), if_body)
        flatten_stmts.extend((s1, s2))
    elif isinstance(t, ast.Name):
        assert t.id == 'True' or t.id == 'False'
        if op_type == 'and' and t.id == 'False':
            flatten_stmts.append(SimpleStmt(Ops.jmp, else_body))
        elif op_type == 'or' and t.id == 'True':
            flatten_stmts.append(SimpleStmt(Ops.jmp, if_body))
        # else: do nothing
    else:
        raise NotImplementedError()


def flattenBinOP(t, flatten_stmts, op, temp=None):
    v1 = lhs = t.left
    v2 = rhs = t.right
    if not isinstance(lhs, ast.Constant) and not isinstance(lhs, ast.Name):
        # Flatten recursively
        v_temp = Temporals.generateTemp()
        flatten(lhs, flatten_stmts, temp=v_temp)
        v1 = v_temp
    if not isinstance(rhs, ast.Constant) and not isinstance(rhs, ast.Name):
        v_temp = Temporals.generateTemp()
        flatten(rhs, flatten_stmts, temp=v_temp)
        v2 = v_temp

    if temp:
        if not isinstance(temp, ast.Name): temp = ast.Name(temp) 
        s = SimpleStmt(op, temp, v1, v2)
        flatten_stmts.append(s)
    # else: # discard node
    #     print "Useless add: discarded"

def flatten(t, flatten_stmts, temp=None):
    assert isinstance(flatten_stmts, list)

    if isinstance(t, ast.Module):
        for s in t.body:
            flatten(s, flatten_stmts)
    elif isinstance(t, ast.Expr):
        flatten(t.value, flatten_stmts)
    elif isinstance(t, ast.Call):
        # Only 'input' (w/out args) and 'print' must be covered
        funcName = t.func.id
        assert funcName == 'input' or funcName == 'print'
        
        # Do function calls even if no return value
        arg = None
        if len(t.args) == 0: # Nothing to od
            pass
        elif len(t.args) == 1:
            arg = t.args[0]
            if not(isinstance(arg, ast.Constant) or isinstance(arg, ast.Name)):
                arg_temp = Temporals.generateTemp()
                flatten(arg, flatten_stmts, temp=arg_temp)
                arg = arg_temp
        else:
            raise NotImplementedError("fcts can take at most one argument (len={})".format(len(t.args)))

        s = SimpleStmt(Ops.call, funcName, arg, temp)
        flatten_stmts.append(s)

    elif isinstance(t, ast.Assign):
        rhs = t.value
        name_node = t.target

        if isinstance(rhs, ast.Constant) or isinstance(rhs, ast.Name):
            s = SimpleStmt(Ops.assign, name_node, rhs)
            flatten_stmts.append(s)
        else: # No need to create temporal since we are assigning anyways
            flatten(rhs, flatten_stmts, temp=name_node)
    elif isinstance(t, ast.BinOp):
        op = Ops.ast_to_ops(t.op)
        flattenBinOP(t, flatten_stmts, op, temp)
    elif isinstance(t, ast.UnaryOp):
        # assert isinstance(t.op, ast.USub), "only USub() and Not() are supported"
        if isinstance(t.operand, ast.Constant):
            t.operand.value = -t.operand.value
            s = SimpleStmt(Ops.assign, temp, t.operand)
            # flatten_stmts.append(s)
        elif isinstance(t.operand, ast.Name):
            s = SimpleStmt(Ops.neg, temp, t.operand)
            # flatten_stmts.append(s)
        else :
            operand_temp = Temporals.generateTemp()
            flatten(t.operand, flatten_stmts, temp=operand_temp)
            s = SimpleStmt(Ops.neg, temp, operand_temp)
        if temp:
            flatten_stmts.append(s)

    elif isinstance(t, ast.If):
        if isinstance(t.test, ast.Name): # test in {True/False}
            assert t.test.id == 'True' or t.test.id == 'False', 'Boolean constants are True/False'
            if t.test.id == 'True':
                # Flatten if_body only
                [flatten(x, flatten_stmts) for x in t.body]
            else: # Flatten orelse only
                [flatten(x, flatten_stmts) for x in t.orelse]
        else: # Recursively flatten t.test
            if_body = Labels.nextLabel()
            else_body = Labels.nextLabel()
            end_if = Labels.nextLabel()
            flatten_if_test(t.test, flatten_stmts, labels=(if_body, else_body, end_if))
            
            if isinstance(t.test, ast.BoolOp) and isinstance(t.test.op, ast.Or): # Jump over if body to else
                flatten_stmts.append(SimpleStmt(Ops.jmp, else_body))

            flatten_stmts.append(SimpleStmt(Ops.label, if_body)) # Add label to if body
        # Flatten if body
            [flatten(x, flatten_stmts) for x in t.body]
            flatten_stmts.append(SimpleStmt(Ops.jmp, end_if)) # jump to end_if
            flatten_stmts.append(SimpleStmt(Ops.label, else_body)) # Add label to else body
        # Flatten else body
            [flatten(x, flatten_stmts) for x in t.orelse]
            flatten_stmts.append(SimpleStmt(Ops.label, end_if)) # Add label to end if
            
            
    else:
        print("{}".format(t))