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
	jg	LBB0_2						# Goto If (on cond1)
	cmpq	$100, -24(%rbp)			# Cmp2
	jge	LBB0_3						# Goto Else (on inverse cond2)
LBB0_2:								# 
	movq	$1, -32(%rbp)			# If body
	jmp	LBB0_4						# Goto End
LBB0_3:								#
	movq	$2, -32(%rbp)			# Else Body
LBB0_4:								# End
	movq	-32(%rbp), %rsi
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


.subsections_via_symbols
