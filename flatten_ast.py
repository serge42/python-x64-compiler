from __future__ import print_function
from helper import Ops, Temporals, SimpleStmt, Labels

import my_ast as ast


def flatten_if_test(t, flatten_stmts, labels, op_type='and', nextLabel=None):
    assert isinstance(t, ast.Constant) \
            or isinstance(t, ast.Compare) \
            or isinstance(t, ast.BoolOp), \
            "Test should be either True/False or bool_expr; received {}".format(type(t))
    if_body, else_body = labels
    if isinstance(t, ast.BoolOp):
        # Chain comparisons, recursive call
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
    elif isinstance(t, ast.Constant):
        assert t.value is True or t.value is False
        if op_type == 'and' and t.value is False:
            flatten_stmts.append(SimpleStmt(Ops.jmp, else_body))
        elif op_type == 'or' and t.value is True:
            flatten_stmts.append(SimpleStmt(Ops.jmp, if_body))
        # else: do nothing
    else:
        raise NotImplementedError()

def flatten_while_test(t, flatten_stmts, labels, op_type, nextLabel=None):
    header_label, body_label, end_label = labels
    for i in range(len(t.values)):
        if isinstance(t, ast.BoolOp):
            if isinstance(t.op, ast.Or):
                if isinstance(t.values[i], ast.BoolOp):
                    nextLabel = Labels.nextLabel()
                    flatten_while_test(t.values[i], flatten_stmts, labels, op_type='or', nextLabel=nextLabel)
                    flatten_stmts.append(SimpleStmt(Ops.jmp, body_label))
                    flatten_stmts.append(SimpleStmt(Ops.label, nextLabel))
                else:
                    flatten_while_test(t.values[i], flatten_stmts, labels, op_type='or')
            else:
                flatten_while_test(t.values[i], flatten_stmts, labels, op_type='and', nextLabel=nextLabel)

        elif isinstance(t, ast.Compare):
            s1 = SimpleStmt(Ops.cmp, t.right, t.left)
            if op_type == 'and':
                lbl = nextLabel if nextLabel else end_label
                s2 = SimpleStmt(Ops.comparison2jmp_inversed(t.op), lbl)
            else:
                s2 = SimpleStmt(Ops.comparison2jmp(t.op), body_label)
            flatten_stmts.extend((s1, s2))
        elif isinstance(t, ast.Constant):
            assert t.value is True or t.value is False
            if op_type == 'and' and t.value is False:
                flatten_stmts.append(SimpleStmt(Ops.jmp, end_label))
            elif op_type == 'or' and t.value is True:
                flatten_stmts.append(SimpleStmt(Ops.jmp, body_label))
    pass


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
        if isinstance(t.test, ast.Constant) and (t.test.value is True or t.test.value is False): # test in {True/False}
            assert t.test.id == 'True' or t.test.id == 'False', 'Boolean constants are True/False'
            if t.test.id is True:
                # Flatten if_body only
                [flatten(x, flatten_stmts) for x in t.body]
            else: # Flatten orelse only
                [flatten(x, flatten_stmts) for x in t.orelse]
        else: # Recursively flatten t.test
            label = Labels.nextLabel()
            if_body = 'if_body_' + label
            else_body = 'if_else_' + label
            end_if = 'if_end_' + label
            flatten_if_test(t.test, flatten_stmts, labels=(if_body, else_body))
            
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
            
    elif isinstance(t, ast.While):
        if isinstance(t.test, ast.Constant) and t.test.value is False:
            pass # Drop the while
        else:
            label = Labels.nextLabel()
            header_label = 'loop_header_' + label 
            body_label = 'loop_body_' + label
            end_label = 'loop_end_' + label
            flatten_stmts.append(SimpleStmt(Ops.label, header_label)) # Add header label before boolean test(s)

            if not isinstance(t.test, ast.Constant): # Test is True: no need to test, infinite loop
                flatten_if_test(t.test, flatten_stmts, labels=(body_label, end_label))

                if isinstance(t.test, ast.BoolOp) and isinstance(t.test.op, ast.Or): # Jmp over body (on False)
                    flatten_stmts.append(SimpleStmt(Ops.jmp, end_label))

                flatten_stmts.append(SimpleStmt(Ops.label, body_label))
            # Flatten body
            [flatten(x, flatten_stmts) for x in t.body]
            # Jmp to header
            flatten_stmts.append(SimpleStmt(Ops.jmp, header_label))
            # Add end label
            flatten_stmts.append(SimpleStmt(Ops.label, end_label))

    elif isinstance(t, ast.List):
        s = SimpleStmt(Ops.call, 'new_list', len(t.elts), temp)

    elif isinstance(t, ast.Subscript):
        pass

    else:
        print("{}".format(t))