x = 1 + 1
y = 1 + -x * x + -1 # test p_number_signed
print(y)
1 * -(1 + -x) * (2 + 1 -0 - -2) # Dead code
-input() # UMINUS dead code
-(-1 + -(1+1)) # UMINUS dead code
x = 1 * -(1 + -x) * (2 + 1 -0 - -2)
print(x)
z = -y - -(x * input()) # test p_factor_expr_signed
print(input() + z)