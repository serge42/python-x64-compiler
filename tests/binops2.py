x = 2
y =  -x + -1 # test p_number_signed
print(y)
# 1 * (1 + x) # Dead code
# -input() # UMINUS dead code
# -(-1 + -(1+1)) # UMINUS dead code
-1
x = 1 + (1 + -x)
print(x)
# z = -y - -(x * input()) # test p_factor_expr_signed
# print(input() + z)