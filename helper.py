
import my_ast as ast
# Python2 doesn't support enums...
class Ops():
    _ops = ['add', 'sub', 'mul', 'div', 'mod', 'call', 'assign', 'neg', 'cmp', 'jmp', 'je', 'jne', 'jg', 'jge', 'jl', 'jle', 'label']#'if_', 'while_']
    add = 0 # binop result lhs rhs
    sub = 1
    mul = 2 
    div = 3
    mod = 4
    call = 5        # call func arg result
    assign = 6      # assign var val
    neg = 7         # u_op result operand
    cmp = 8         # cmp S2 S1 (sets condition codes according to S1 - S2) 
    jmp = 9         # jmp <label_name> 
    je = 10         #
    jne = 11        #
    jg = 12         #
    jge = 13        #
    jl = 14         #
    jle = 15        #
    label = 16        # label <name>
    # if_ = 8         # if [test] [body] [orelse]
    # while_ = 9      # while [test] [body]
    bin_ops = [add, sub, mul, div, mod]
    jmp_ops = [jmp, je, jne, jg, jge, jl, jle]

    @staticmethod
    def get_name(id):
        return Ops._ops[id]

    @staticmethod
    def ast_to_ops(op):
        assert isinstance(op, ast.AST)
        if isinstance(op, ast.Add): return Ops.add
        elif isinstance(op, ast.Sub): return Ops.sub
        elif isinstance(op, ast.Mul): return Ops.mul
        elif isinstance(op, ast.Div): return Ops.div
        elif isinstance(op, ast.Mod): return Ops.mod
        else: raise RuntimeError('Unrecognized operation')

    @staticmethod
    def comparison2jmp(op):
        if isinstance(op, ast.Gt): return Ops.jg
        elif isinstance(op, ast.Lt): return Ops.jl
        elif isinstance(op, ast.GtE): return Ops.jge
        elif isinstance(op, ast.LtE): return Ops.jle
        elif isinstance(op, ast.Eq): return Ops.je
        elif isinstance(op, ast.NotEq): return Ops.jne
        else: raise RuntimeError('Unrecognized operation')

    @staticmethod
    def comparison2jmp_inversed(op):
        if isinstance(op, ast.Gt): return Ops.jle
        elif isinstance(op, ast.Lt): return Ops.jge
        elif isinstance(op, ast.GtE): return Ops.jl
        elif isinstance(op, ast.LtE): return Ops.jg
        elif isinstance(op, ast.Eq): return Ops.jne
        elif isinstance(op, ast.NotEq): return Ops.je
        else: raise RuntimeError('Unrecognized operation')

class SimpleStmt():
    def __init__(self, op, v1, v2=None, v3=None):
        self._op = op
        self._v1 = v1
        self._v2 = v2
        self._v3 = v3

    def __repr__(self):
        return Ops.get_name(self._op) + " " + str(self._v1) + " " + str(self._v2) + " " + str(self._v3)

class Temporals():
    base = 'xzwk'
    id = 0
    @staticmethod
    def generateTemp():
        Temporals.id += 1
        return ast.Name(Temporals.base + '$' + str(Temporals.id))

class Labels():
    base = 'lbl'
    id = 0
    @staticmethod
    def nextLabel():
        label = Labels.base + str(Labels.id)
        Labels.id += 1
        return label