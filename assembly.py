class ASSEMBLY(object):
    def __init__(self):
        self._fields = []
        self._inst = 'nop'

    def __repr__(self):
        values = [str(getattr(self, field)) for field in self._fields]
        return '\t{} {}'.format(self._inst, ', '.join(values))

    def __hash__(self):
        res = 0
        for i,field in enumerate(self._fields):
            res += hash(getattr(self, field)) * hash(field) # Field and field value are important; ie. MOV(r1, r2) != MOV(r2, r1)
        return res

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and hash(self) == hash(other))

    def __ne__(self, other):
        return not self.__eq__(other)

class MOV(ASSEMBLY):
    def __init__(self, S, D):
        assert isinstance(D, REG) or isinstance(D, V_REG) or isinstance(D, STACK_VAR)
        assert not(isinstance(S, STACK_VAR) and isinstance(D, STACK_VAR)), "Can't mov from stack to stack"
        super(MOV, self).__init__()
        self._S = S
        self._D = D
        self._fields = ['_S','_D']
        self._inst = 'movq'


class CALL(ASSEMBLY):
    def __init__(self, fct):
        super(CALL, self).__init__()
        self._fct = fct
        self._fields = ['_fct']
        self._inst = 'call'


class PUSH(ASSEMBLY):
    def __init__(self, reg):
        assert isinstance(reg, REG)
        super(PUSH, self).__init__()
        self._reg = reg
        self._fields = ['_reg']
        self._inst = 'pushq'


class POP(ASSEMBLY):
    def __init__(self, reg):
        assert isinstance(reg, REG)
        super(POP, self).__init__()
        self._reg = reg
        self._fields = ['_reg']
        self._inst = 'popq'


class ADD(ASSEMBLY):
    def __init__(self, S, D):
        assert isinstance(S, REG) or isinstance(S, V_REG) or isinstance(S, IMM)
        assert isinstance(D, REG) or isinstance(D, V_REG), 'Expected D instanceof REG or V_REG, got {}'.format(type(D))
        super(ADD, self).__init__()
        self._S = S
        self._D = D
        self._fields = ['_S', '_D']
        self._inst = 'addq'


class SUB(ASSEMBLY):
    def __init__(self, S, D):
        assert isinstance(S, REG) or isinstance(S, V_REG) or isinstance(S, IMM)
        assert isinstance(D, REG) or isinstance(D, V_REG)
        super(SUB, self).__init__()
        self._S = S
        self._D = D
        self._fields = ['_S', '_D']
        self._inst = 'subq'


class IMUL(ASSEMBLY):
    def __init__(self, S, D):
        assert isinstance(S, REG) or isinstance(S, V_REG) or isinstance(S, IMM)
        super(IMUL, self).__init__()
        self._S = S
        self._D = D
        self._fields = ['_S', '_D']
        self._inst = 'imul'


class IDIVQ(ASSEMBLY):
    # Signed divide %rdx:%rax by S. Quotient in %rax, remainder in %rdx (Used for modulo as well)
    def __init__(self, S):
        super(IDIVQ, self).__init__()
        self._S = S
        self._fields = ['_S']
        self._inst = 'idivq'


class NEG(ASSEMBLY):
    def __init__(self, D):
        assert isinstance(D, REG) or isinstance(D, V_REG)
        super(NEG, self).__init__()
        self._D = D
        self._fields = ['_D']
        self._inst = 'neg'


class REG(ASSEMBLY):
    def __init__(self, name):
        assert isinstance(name, str)
        super(REG, self).__init__()
        self._name = name
        self._fields = ['_name']
        self._spilled = True # Reg can never be spilled (thus, there are defined as 'already spilled')

    def __repr__(self):
        return 'REG({})'.format(self._name)

    def __str__(self):
        return self._name
        

class V_REG(ASSEMBLY):
    def __init__(self, name, spilled=False):
        assert isinstance(name, str)
        super(V_REG, self).__init__()
        self._name = name
        self._fields = ['_name']
        self._spilled = spilled # spilled=True if V_REG has been generated to replace a spilled variable

    def __repr__(self):
        return 'V_REG({})'.format(self._name)
        

class STACK_VAR(ASSEMBLY):
    def __init__(self, pos):
        super(STACK_VAR, self).__init__()
        self._pos = pos
        self._fields = ['_pos']

    def __repr__(self):
        return '{:#x}(%rbp)'.format(self._pos)


class IMM(ASSEMBLY):
    def __init__(self, value):
        super(IMM, self).__init__()
        self._value = value
        self._fields = ['_value']

    def __repr__(self):
        return '${:#x}'.format(self._value)

class CMP(ASSEMBLY):
    def __init__(self, S1, S2):
        super(CMP, self).__init__()
        self._S1 = S1
        self._S2 = S2
        self._fields = ['_S1', '_S2']
        self._inst = 'cmp'

class JMP(ASSEMBLY):
    def __init__(self, label, inst='jmp'):
        super(JMP, self).__init__()
        self._label = label
        self._fields = ['_label']
        self._inst = inst

class LABEL(ASSEMBLY):
    def __init__(self, name):
        super(LABEL, self).__init__()
        self._name = name
        self._fields = ['_name']

    def __repr__(self):
        return '{}:'.format(self._name)

class SINGLE_OP(ASSEMBLY):
    '''Class representing any x86 operation without argument st. retq, nop, etc. '''

    def __init__(self, op_name):
        assert isinstance(op_name, str)
        super(SINGLE_OP, self).__init__()
        self._inst = op_name

class Registers():
    rax = REG('%rax')
    rbx = REG('%rbx')
    rcx = REG('%rcx')
    rdx = REG('%rdx')
    rsi = REG('%rsi')
    rdi = REG('%rdi')
    rsp = REG('%rsp')
    rbp = REG('%rbp')
    r8 = REG('%r8')
    r9 = REG('%r9')
    r10 = REG('%r10')
    r11 = REG('%r11')
    r12 = REG('%r12')
    r13 = REG('%r13')
    r14 = REG('%r14')
    r15 = REG('%r15')
    allocable = [rax, rbx, rcx, rdx, rsi, r8, r9, r10, r11, r12, r13, r14, r15] # All_reg - {rdi, rsp, rbp}
    # allocable = [rax, rbx, rcx] # Reduced registers to test spilling
    params = [rdi, rsi, rdx, rcx, r8, r9]
    caller_save = [rax, rcx, rdx, rdi, rsi, r8, r9, r10, r11] # caller_save - {rsp}
    callee_save = [rbx, r12, r13, r14, r15] # callee_saved - {rbp}