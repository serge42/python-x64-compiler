	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 10, 14	sdk_version 10, 14
	.globl	_main                   ## -- Begin function main
	.p2align	4, 0x90
_main:                                  ## @main
	pushq	%rbp
	movq	%rsp, %rbp
	subq	$48, %rsp
	movq	$1, -24(%rbp)
	cmpq	$0, -24(%rbp)			# Cmp1
	jle	LBB0_3						# Goto Else (on inverse cond1)
	cmpq	$100, -24(%rbp)			# Cmp2 (AND)
	jge	LBB0_3						# Goto Else (on inverse cond2)
	movq	$1, -32(%rbp)
	jmp	LBB0_4						# If body
LBB0_3:
	movq	$2, -32(%rbp)			# Else body
LBB0_4:
	movq	-32(%rbp), %rsi			# End if
	leaq	L_.str(%rip), %rdi
	movb	$0, %al
	callq	_printf
	xorl	%ecx, %ecx
	movl	%eax, -36(%rbp)         ## 4-byte Spill
	movl	%ecx, %eax
	addq	$48, %rsp
	popq	%rbp
	retq
                                        ## -- End function
	.section	__TEXT,__cstring,cstring_literals
L_.str:                                 ## @.str
	.asciz	"%lld\n"
