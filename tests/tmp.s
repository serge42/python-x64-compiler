	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 10, 14	sdk_version 10, 14
	.globl	_main                   ## -- Begin function main
	.p2align	4, 0x90
_main:
	pushq %rbp
	movq %rsp, %rbp
	subq $0x10, %rsp
	movq $0x1, %rdi
	movq %r9, -0x8(%rbp)
	movq %rdi, -0x10(%rbp)
	call _print_int_nl
	movq -0x8(%rbp), %r9
	movq -0x10(%rbp), %rdi
	movq $-0x1, %rdi
	movq %r9, -0x8(%rbp)
	call _box_int
	movq -0x8(%rbp), %r9
	movq %rax, %rdx
	movq %rdx, %rdi
	movq %r9, -0x8(%rbp)
	call _unbox_int
	movq -0x8(%rbp), %r9
	movq %rax, %rdx
	movq %rdx, %rdi
	movq %r9, -0x8(%rbp)
	movq %rdi, -0x10(%rbp)
	call _print_int_nl
	movq -0x8(%rbp), %r9
	movq -0x10(%rbp), %rdi
	movq $0x1, %rdi
	movq %r9, -0x8(%rbp)
	call _box_int
	movq -0x8(%rbp), %r9
	movq %rax, %rdx
	movq %rdx, %rdi
	movq %r9, -0x8(%rbp)
	call _unbox_int
	movq -0x8(%rbp), %r9
	movq %r9, %rdi
	call _box_int
	movq %rbx, %rdi
	call _box_int
	movq %rax, %rdx
	movq %rdx, %rdi
	call _unbox_int
	movq %rax, %rdx
	movq %rdx, %rdi
	movq %rdi, -0x8(%rbp)
	call _print_int_nl
	movq -0x8(%rbp), %rdi
	addq $0x10, %rsp
	popq %rbp
	retq 
