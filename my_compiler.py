from __future__ import print_function
from helper import Ops, Temporals, SimpleStmt
from assembly import *

from random import randint, choice, seed

import my_ast as ast
import sys, string


class MyCompiler():
    PRINT_FCT = 'print_int_nl'
    INPUT_FCT = 'input'

    @staticmethod
    def immediate(val):
        assert isinstance(val, int), "Expected integer, got {}".format(type(val))
        return "${:#x}".format(val)


    def __init__(self, arch='unix', pseudo=False, liveness=False):
        self._vars = {}
        self._stack_vars = {}
        self._next_var_pos = -8
        self._max_stack = 0
        self._arch = arch
        self.pseudo = pseudo
        self.liveness = liveness
        seed(a='123') 

    def is_print_fct(self, call_node):
        if self._arch == 'macos':
            return call_node._fct == '_' + MyCompiler.PRINT_FCT
        elif self._arch == 'unix':
            return call_node._fct == MyCompiler.PRINT_FCT

    def is_input_fct(self, call_node):
        if self._arch == 'macos':
            return call_node._fct == '_' + MyCompiler.INPUT_FCT
        elif self._arch == 'unix':
            return call_node._fct == MyCompiler.INPUT_FCT

    def _get_var_pos(self, name):
        if isinstance(name, ast.Name):
            name = name.id
        if name in self._vars:
            return self._vars[name]
        else:
            print (name)
            msg = "Variable {} not found".format(name)
            raise KeyError(msg)

    def _get_stack_size(self):
        if self._max_stack % 0x10 != 0: # Align end of stack
            self._max_stack -= 8 # all variables take 8B
        return -self._max_stack # Stack size is positive (last_addr is negative)

    def _increase_stack(self):
        if self._next_var_pos < self._max_stack: 
            self._max_stack = self._next_var_pos
        self._next_var_pos -= 8

    def _reduce_stack(self):
        self._next_var_pos += 8

    def _get_next_stack_pos(self):
        pos = self._next_var_pos
        self._increase_stack()
        return pos

    def _save_reg_stack(self, var):
        assert isinstance(var, REG)
        self._stack_vars[var] = STACK_VAR(self._next_var_pos)
        self._increase_stack()
        return self._stack_vars[var]

    def _get_saved_reg(self, var):
        assert isinstance(var, REG)
        self._reduce_stack()
        return self._stack_vars.pop(var)

    def _define_vars(self, stmts):
        for s in stmts:
            assert isinstance(s, SimpleStmt), "Error: stmts should be a list of SimpleStmt"
            if isinstance(s._v1, ast.Name):
                self._vars[V_REG(s._v1.id)] = None
            if isinstance(s._v2, ast.Name):
                self._vars[V_REG(s._v2.id)] = None
            if isinstance(s._v3, ast.Name):
                self._vars[V_REG(s._v3.id)] = None

    def _assigned_vars_set(self):
        ''' Returns a set containing all V_REG variables that have been assigned a register'''
        return set([i for i,x in self._vars.items() if x])

    def _assigned_vars_reg_set(self, var_list=[]):
        ''' Returns a set containing the registers that have been assigned to some V_REG variable'''
        return set([x for i,x in self._vars.items() if i in var_list and x])

    def _unassigned_vars_set(self):
        ''' Returns a set containing all V_REG variables that have not yet been assigned a register'''
        return set(self._vars.keys()) - self._assigned_vars_set()

    def _print_sections(self):
        if self._arch == 'macos':
            print("\t.section	__TEXT,__text,regular,pure_instructions")
            print("\t.build_version macos, 10, 14	sdk_version 10, 14")
            print("\t.globl	_main                   ## -- Begin function main")
            print("\t.p2align	4, 0x90")
            # Also print main
            print("_main:")
        elif self._arch == 'unix':
            print('\t.file\t"foo.py"')
            print('\t.text')
            print('\t.globl\tmain')
            print('\t.type\tmain, @function')
            # Also print main
            print("main:")

    def _generate_pseudoreg(self):
        reg_name = next(iter(self._vars)) # If only python had do..while
        while reg_name in self._vars:
            reg_name = 't'
            reg_name += ''.join(choice(string.ascii_lowercase + string.digits) for i in range(2))
        v_reg = V_REG(reg_name, spilled=True)
        self._vars[v_reg] = None # Include in self._vars to avoid duplicates
        return v_reg

    def _pseudo_x86(self, stmts):
        pseudo_stmts = []
        for s in stmts:
            if s._op == Ops.call:
                fct = ''
                if self._arch == 'macos': fct = '_' # MacOS fcts name start with '_'
                if s._v1 == 'print': # A call's 1st arg is either 'print' or 'input'
                    fct += 'print_int_nl'
                    if s._v2:
                        v2 = V_REG(s._v2.id) if isinstance(s._v2, ast.Name) else IMM(s._v2.value)
                        pseudo_stmts.append(MOV(v2, Registers.rdi))
                    pseudo_stmts.append(CALL(fct))
                elif s._v1 == 'input':
                    fct += 'input'
                    pseudo_stmts.append(CALL(fct))
                    if s._v3:
                        assert isinstance(s._v3, ast.Name), "Error"
                        pseudo_stmts.append(MOV(Registers.rax, V_REG(s._v3.id)))
                # elif s._v1 == 'box_int' or s._v1 == 'unbox_int' or s._v1 == 'box_bool' or s._v1 == 'unbox_bool':
                elif s._v1.startswith('box') or s._v1.startswith('unbox'):
                    fct += s._v1.lower() # C fcts are lowercase
                    v2 = V_REG(s._v2.id) if isinstance(s._v2, ast.Name) else IMM(s._v2.value)
                    pseudo_stmts.append(MOV(v2, Registers.rdi))
                    pseudo_stmts.append(CALL(fct))
                    pseudo_stmts.append(MOV(Registers.rax, V_REG(s._v3.id)))

                else: 
                    raise NotImplementedError('Call to unsuported function: {}'.format(s._v1))
            elif s._op == Ops.assign:
                assert isinstance(s._v1, ast.Name), "cannot assign to a non-name value"
                # Check if assigning a Const or a Name
                if isinstance(s._v2, ast.Constant):
                    pseudo_stmts.append(MOV(IMM(s._v2.value), V_REG(s._v1.id))) # Imm to pseudo-reg
                elif isinstance(s._v2, ast.Name): 
                    pseudo_stmts.append(MOV(V_REG(s._v2.id), V_REG(s._v1.id))) # pseudo-reg to pseudo-reg
            elif s._op == Ops.add or s._op == Ops.sub or s._op == Ops.mul:
                assert isinstance(s._v1, ast.Name), "Error"
                assert isinstance(s._v2, ast.Name) or isinstance(s._v2, ast.Constant), "Error"
                assert isinstance(s._v3, ast.Name) or isinstance(s._v3, ast.Constant), "Error"

                v1 = V_REG(s._v1.id)
                v2 = V_REG(s._v2.id) if isinstance(s._v2, ast.Name) else IMM(s._v2.value)
                v3 = V_REG(s._v3.id) if isinstance(s._v3, ast.Name) else IMM(s._v3.value)

                if s._op == Ops.add:
                    op = ADD(v3, v1) 
                elif s._op == Ops.sub: 
                    op = SUB(v3, v1)
                else:
                    op = IMUL(v3, v1)

                # E.g. addq r10, r11 -> r11 += r10
                pseudo_stmts.append(MOV(v2, v1))
                pseudo_stmts.append(op)
                
            elif s._op == Ops.neg:
                assert isinstance(s._v1, ast.Name) , "Error"
                assert isinstance(s._v2, ast.Name) , "Error"

                v1 = V_REG(s._v1.id) 
                v2 = V_REG(s._v2.id)
                
                pseudo_stmts.append(MOV(v2, v1))
                pseudo_stmts.append(NEG(v1))

            elif s._op == Ops.cmp:
                assert isinstance(s._v1, ast.Name) or isinstance(s._v1, ast.Constant), 'Error'
                assert isinstance(s._v2, ast.Name) or isinstance(s._v2, ast.Constant), 'Error'

                # TODO: check if _v1 or _v2 are equal to True/False (ast.Name)
                v1 = V_REG(s._v1.id) if isinstance(s._v1, ast.Name) else IMM(s._v1.value)
                v2 = V_REG(s._v2.id) if isinstance(s._v2, ast.Name) else IMM(s._v2.value)
                pseudo_stmts.append(CMP(v1, v2))
            elif s._op in Ops.jmp_ops:
                pseudo_stmts.append(JMP(s._v1, inst=Ops.get_name(s._op)))
            elif s._op == Ops.label:
                pseudo_stmts.append(LABEL(s._v1))
            else:
                print("# Warning: received unsupported operation: 'Ops.{}'".format(Ops.get_name(s._op)), file=sys.stderr)
        # End for 
        return pseudo_stmts

    def _liveness_analysis(self, pseudo_stmts, drop_stmts=False):
        ''' Removes stmts if they only define dead vars (dead code)
        pseudo_stmts: list of statements in pseudo-x86 using virtual registers and ASSEMBLY nodes
        Returns: live: list of sets containing st. live[i] = live_in for stmt i, live[i+1] = live_out for stmt i'''
        # Liveness analysis
        live = [set()] # final live_out is empty
        new_stmts = []
        branch_out = None
        i = len(pseudo_stmts) - 1
        for s in reversed(pseudo_stmts):
            live_out = live[-1]
            DEF = set(); USE = set()
            if isinstance(s, MOV):
                # Remove useless stmt (passing parameter isn't useless)
                if drop_stmts and not s._D in Registers.params and not isinstance(s._D, STACK_VAR) and not s._D in live_out:
                    continue
                if isinstance(s._S, REG) or isinstance(s._S, V_REG):
                    USE.add(s._S) 
                if isinstance(s._D, REG) or isinstance(s._D, V_REG):
                    DEF.add(s._D)
                new_stmts.append(s)

            elif isinstance(s, ADD) or isinstance(s, SUB) or isinstance(s, IMUL):
                # Remove useless stmt (passing parameter or saveing on stack isn't useless)
                if drop_stmts and not s._D in Registers.params and not isinstance(s._D, STACK_VAR) and not s._D in live_out:
                    continue
                # ADD S, D -> D += S; both S and D are used and live if they're (virtual)registers
                if isinstance(s._S, REG) or isinstance(s._S, V_REG):
                    USE.add(s._S)
                # <op>._D is always REG or V_REG
                USE.add(s._D) # Could add DEF.add(s._D)
                new_stmts.append(s)

            elif isinstance(s, NEG):
                if isinstance(s._D, REG) or isinstance(s._D, V_REG):
                    if drop_stmts and not s._D in live_out and not s._D in Registers.params:
                        continue
                    USE.add(s._D) # Could add DEF.add(s._D)
                new_stmts.append(s)
            elif isinstance(s, CALL):
                if self.is_print_fct(s):
                    USE.add(Registers.rdi)
                DEF.add(Registers.rax) # CALL writes to %rax -> add to DEF
                new_stmts.append(s)
            elif isinstance(s, CMP):
                if isinstance(s._S1, V_REG):
                    USE.add(s._v1)
                if isinstance(s._S2, V_REG):
                    USE.add(s._S2)
                new_stmts.append(s)
            elif isinstance(s, LABEL):
                # TODO: check if it is a `while` or `if` label
                # save live_out for the previous label (if body)
                if branch_out is None: 
                    branch_out = live_out
                else:
                    live_out = branch_out
                    branch_out = None
                new_stmts.append(s)
            else: # No change to DEF and USE
                new_stmts.append(s)

            # Equation update of live_in[i]
            live.append( (live_out - DEF).union(USE) )
        # End for
        live.reverse(); new_stmts.reverse() # live and new_stmts were build in reverse 
        return live, new_stmts

    def _build_interference(self, liveness):
        assert isinstance(liveness, list)
        graph = {} # {'v/reg': set([v/reg])}: adj. list of interdependent (virtual)registers
        for s in liveness:
            for reg in s:
                if not reg in graph: graph[reg] = set()
                neigh = s - set([reg]) # Set minus, take other (virtual)registers
                graph[reg] = graph[reg].union(neigh)
        
        return graph

    def _update_vreg(self, pseudo_stmts, live):
        stmts = []
        for i, s in enumerate(pseudo_stmts):
            if isinstance(s, MOV):
                new_S = s._S; new_D = s._D
                if isinstance(s._S, V_REG):
                    new_S = self._vars[s._S]
                if isinstance(s._D, V_REG):
                    new_D = self._vars[s._D]
                if new_S == new_D: continue # Useless mov, pass
                stmts.append(MOV(new_S, new_D))

            elif isinstance(s, ADD) or isinstance(s, SUB) or isinstance(s, IMUL):
                new_S = self._vars[s._S] if isinstance(s._S, V_REG) else s._S
                new_D = self._vars[s._D] if isinstance(s._D, V_REG) else s._D
                if isinstance(s, ADD):
                    stmt = ADD(new_S, new_D) 
                elif isinstance(s, SUB): 
                    stmt = SUB(new_S, new_D)
                else:
                    stmt = IMUL(new_S, new_D)
                stmts.append(stmt)

            elif isinstance(s, NEG):
                new_D = self._vars[s._D] if isinstance(s._D, V_REG) else s._D
                stmts.append(NEG(new_D))

            elif isinstance(s, CALL):
                live_reg = [x for x in live[i] if isinstance(x, REG)]
                live_reg += [self._vars[x] for x in live[i] if isinstance(x, V_REG)]
                save_reg = set(live_reg).intersection(Registers.caller_save)
                # print(save_reg)
                for reg in save_reg:
                    stack_pos = self._save_reg_stack(reg)
                    stmts.append(MOV(reg, stack_pos))
                stmts.append(s)
                for reg in save_reg:
                    stack_pos = self._get_saved_reg(reg)
                    stmts.append(MOV(stack_pos, reg))
            
            elif isinstance(s, CMP):
                new_S1 = s._S1; new_S2 = s._S2
                if isinstance(s._S1, V_REG):
                    new_S1 = self._vars[s._S1]
                if isinstance(s._S2, V_REG):
                    new_S2 = self._vars[s._S2]
                stmts.append(CMP(new_S1, new_S2))
            else: stmts.append(s)

        return stmts

    def _spill_var(self, pseudo_stmts, var):
        stack_pos = STACK_VAR(self._get_next_stack_pos())
        new_stmts = []
        for s in pseudo_stmts:
            if isinstance(s, MOV):
                new_S = s._S; new_D = s._D
                if isinstance(s._S, V_REG) and s._S._name == var._name:
                    new_S = stack_pos
                if isinstance(s._D, V_REG) and s._D._name == var._name:
                    new_D = stack_pos

                if isinstance(new_S, STACK_VAR) and isinstance(new_D, STACK_VAR):
                    # illegal stmt: MOV(STACK_VAR(X), STACK_VAR(Y)) -> MOV(STACK_VAR(X), temp); MOV(temp, STACK_VAR(Y))
                    temp = self._generate_pseudoreg()
                    new_stmts.append(MOV(new_S, temp))
                    new_S = temp
                new_stmts.append(MOV(new_S, new_D))

            elif isinstance(s, ADD) or isinstance(s, SUB) or isinstance(s, IMUL):
                new_S = s._S; new_D = s._D
                end_append = None
                if isinstance(s._S, V_REG) and s._S._name == var._name:
                    ## Spilling X: ADD(X, Y) -> MOV(stack_pos(x), temp); ADD(temp, Y)
                    temp = self._generate_pseudoreg()
                    new_stmts.append(MOV(stack_pos, temp))
                    new_S = temp
                if isinstance(s._D, V_REG) and s._D._name == var._name:
                    ## Spilling Y: ADD(X, Y) -> MOV(stack_pos(Y), temp); ADD(X, temp); MOV(temp, stack_pos(y))
                    temp = self._generate_pseudoreg()
                    new_stmts.append(MOV(stack_pos, temp))
                    new_D = temp 
                    # ADD/SUB/IMUL stmt will be inserted before end_append
                    end_append = MOV(temp, stack_pos)
                
                if isinstance(s, ADD):
                    stmt = ADD(new_S, new_D) 
                elif isinstance(s, SUB): 
                    stmt = SUB(new_S, new_D)
                else:
                    stmt = IMUL(new_S, new_D)

                new_stmts.append(stmt)
                if end_append: new_stmts.append(end_append)

            elif isinstance(s, NEG):
                if isinstance(s._D, V_REG) and s._D._name == var._name:
                    ## Spilling X: NEG(X) -> MOV(stack_pos(X), temp); NEG(temp); MOV(temp, stack_pos(X))
                    temp = self._generate_pseudoreg()
                    new_stmts.append(MOV(stack_pos, temp))
                    new_stmts.append(NEG(temp))
                    new_stmts.append(MOV(temp, stack_pos))
                else:
                    new_stmts.append(s)
            else:
                new_stmts.append(s)
        # End for
        return new_stmts

    def _allocate_registers(self, inter_graph, pseudo_stmts):
        assert isinstance(inter_graph, dict)
        # Step 1 assign REG to their corresponding register
        for var in inter_graph:
            if isinstance(var, REG):
                self._vars[var] = var
        # Start assigning registers, %rsp and %rbp should not be used
        for var in inter_graph:
            if self._vars[var]: continue # Already assigned
            neighbors_reg = self._assigned_vars_reg_set(var_list=inter_graph[var]) # Set of registers assigned to some V_REG variables interfering with 'var'
            available = set(Registers.allocable) - neighbors_reg
            # Select first register that is not used by any of var's neighbors in inter_graph
            if len(available) > 0:
                self._vars[var] = next(iter(available))
            else:
                # raise NotImplementedError('Spilling not working yet')
                # spill a variable, that is NOT already a generated V_REG caused by a spill
                not_spilled_neighbors = [x for x in inter_graph[var].union([var]) if not x._spilled]
                if len(not_spilled_neighbors) < 1: raise RuntimeError("No (virtual)registers left to spill")
                return True,not_spilled_neighbors[0]
        return False,None

    def _print_x86(self, pseudo_stmts):
        self._print_sections()
        # Add Prologue
        stack_size = self._get_stack_size()
        pseudo_stmts.insert(0, PUSH(Registers.rbp))
        pseudo_stmts.insert(1, MOV(Registers.rsp, Registers.rbp))
        if stack_size > 0:
            stack_size = IMM(stack_size)
            pseudo_stmts.insert(2, SUB(stack_size, Registers.rsp))

        # Add Epilogue
        if stack_size > 0:
            pseudo_stmts.append(ADD(stack_size, Registers.rsp))
        pseudo_stmts.append(POP(Registers.rbp))
        pseudo_stmts.append(SINGLE_OP('retq'))

        # Print stmts
        for s in pseudo_stmts:
            print(str(s))


    def compile_x86(self, stmts):
        assert isinstance(stmts, list)
        # Count vars and define their position on stack
        self._define_vars(stmts)

        pseudo_stmts = self._pseudo_x86(stmts)

        # Stop after generating pseudo x86 if --pseudo arg was given
        if self.pseudo:
            for stmt in pseudo_stmts:
                print(stmt)
            return

        live,pseudo_stmts = self._liveness_analysis(pseudo_stmts, drop_stmts=True)
        if self.liveness:
            for i in range(len(pseudo_stmts)):
                print('# live: {}'.format(' '.join([str(x) for x in live[i]])))
                print(pseudo_stmts[i])
            
            print('# live: {}'.format(' '.join([str(x) for x in live[-1]]))) # Final live_out
            return

        # DEBUG: print pseudo_stmts
        # [print(s) for s in pseudo_stmts]
        # Build interference graph
        graph = self._build_interference(live)
        # print("\nInterference graph:")
        # [print('{}: {}'.format(node, val)) for node, val in graph.items()]
        spilled,var = self._allocate_registers(graph, pseudo_stmts) # Assigns reg in self._vars
        while spilled:
            pseudo_stmts = self._spill_var(pseudo_stmts, var)
            live,pseudo_stmts = self._liveness_analysis(pseudo_stmts, drop_stmts=True)
            graph = self._build_interference(live)
            spilled,var = self._allocate_registers(graph, pseudo_stmts)
        # print("\nRegisters allocation:")
        # [print('{}: {}'.format(node, val)) for node, val in self._vars.items()]

        stmts = self._update_vreg(pseudo_stmts, live)
        self._print_x86(stmts)
        # DEBUG
        # live,new_stmts = self._liveness_analysis(stmts)
        # for i in range(len(new_stmts)):
        #     print('# live: {}'.format(' '.join([str(x) for x in live[i]])))
        #     print(new_stmts[i])
        # print('# live: {}'.format(' '.join([str(x) for x in live[-1]]))) # Final live_out