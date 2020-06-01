class AST(object):
    def __init__(self):
        self._fields = []

    def __str__(self):
        return '{}()'.format(self.__class__.__name__)

## Ops
# Arithmetic
class Add(AST):
    pass
class Sub(AST):
    pass
class Mul(AST):
    pass
class Div(AST):
    pass
class Mod(AST):
    pass
class USub(AST):
    pass
# Bool_expr arithmetic
class And(AST):
    pass
class Or(AST):
    pass
class BitAnd(AST):
    pass
class BitOr(AST):
    pass
class BitXor(AST):
    pass
class Not(AST): # Unary
    pass
# Comparisons
class Gt(AST):
    pass
class Lt(AST):
    pass
class GtE(AST):
    pass
class LtE(AST):
    pass
class Eq(AST):
    pass
class NotEq(AST):
    pass

## Identifiers load/store
class Store(AST): # Variable store
    pass
class Load(AST): # Variable/function load
    pass

class Module(AST):
    def __init__(self, stmt=None):
        self.body = [stmt] if stmt else []
        self._fields = ['body']

class Expr(AST):
    def __init__(self, value=None):
        self.value = value
        self._fields = ['value']

class Assign(AST):
    def __init__(self, target=None, value=None):
        self.target = target
        self.value = value
        self._fields = ['target', 'value']

class Call(AST):
    def __init__(self, func=None, args=[]):
        assert isinstance(args, list), "args should be a list"
        self.func = func
        self.args = args
        self._fields = ['func', 'args']

class Name(AST):
    def __init__(self, id_=None, ctx=None):
        self.id = id_
        self.ctx = ctx
        self._fields = ['id','ctx']

    def __str__(self):
        return "Name(id={})".format(self.id, self.ctx)

class BinOp(AST):
    def __init__(self, op=None, left=None, right=None):
        self.op = op
        self.left = left
        self.right = right
        self._fields = ['op','left','right']

class UnaryOp(AST):
    def __init__(self, op=None, operand=None):
        self.op = op
        self.operand = operand
        self._fields = ['op', 'operand']

class Constant(AST):
    def __init__(self, value=None):
        self.value = eval(value) if isinstance(value, str) else value # in case string is passed from parser
        self._fields = ['value']

    def __str__(self):
        return "Constant(value={})".format(self.value)

class BoolOp(AST):
    def __init__(self, op, values):
        self.op = op
        self.values = values
        self._fields = ['op', 'values']

class Compare(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
        self._fields = ['left', 'op', 'right']

class If(AST):
    def __init__(self, test, body, orelse):
        self.test = test
        self.body = body
        self.orelse = orelse
        self._fields = ['test', 'body', 'orelse']

class While(AST):
    def __init__(self, test, body):
        self.test = test
        self.body = body
        self._fields = ['test', 'body']

class List(AST):
    def __init__(self, elts=[]):
        self.elts = elts
        self._fields = ['elts']

class Subscript(AST):
    def __init__(self, value, index):
        self.value = value
        self.index = index
        self._fields = ['value, index']

class Pass(AST):
    pass

# class Box_types:
#     integer = 'int'
#     long = 'long'
#     boolean = 'bool'
#     ffloat = 'float'
#     string = 'string'
#     undefined = 'udef'

# class BOX(AST):
#     def __init__(self, value, btype, boxing=True):
#         self.value = value
#         self.type = btype
#         self.boxing = boxing
#         self._fields = ['value', 'type', 'boxing']

#     def __str__(self):
#         return "{}(value={})".format(self.__class__.__name__, self.value)

#     def boxing_fct(self):
#         if self.boxing:
#             return 'box_' + self.type
#         return 'unbox' + self.type

# class Box_int(BOX):
#     def __init__(self, value):
#         assert isinstance(value, Constant) or isinstance(value, BinOp)
#         super(Box_int, self).__init__(value)
#         self.type = int

# class Unbox_int(BOX):
#     pass

# class Box_float(BOX):
#     pass

# class Unbox_float(BOX):
#     pass

# class Box_bool(BOX):
#     def __init__(self, value):
#         assert isinstance(value, Constant), "expected bool, got {}".format(type(value))
#         super(Box_bool, self).__init__(value)

# class Unbox_bool(BOX):
#     pass

def dump(node):
    def _format(node):
        if isinstance(node, AST):
            fields = [(a, _format(b)) for a, b in iter_fields(node)]
            rv = '%s(%s' % (node.__class__.__name__, ', '.join(
                ('%s=%s' % field for field in fields)
                # if annotate_fields else
                # (b for a, b in fields)
            ))
            # if include_attributes and node._attributes:
            #     rv += fields and ', ' or ' '
            #     rv += ', '.join('%s=%s' % (a, _format(getattr(node, a)))
            #                     for a in node._attributes)
            return rv + ')'
        elif isinstance(node, list):
            return '[%s]' % ', '.join(_format(x) for x in node)
        return repr(node)
    if not isinstance(node, AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)

def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass