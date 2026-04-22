from sage.all import crt, Integer

# Load values from helper.py
from helper import *

# List of moduli and remainders
moduli = [N1, N2, N3]
remainders = [ct1, ct2, ct3]

# Compute CRT
x = crt(remainders, moduli)

# Ensure x is the smallest non-negative solution
# crt returns a solution modulo product, but we need the actual m^3 which is less than product
# Since m^3 < N1*N2*N3, x is exactly m^3.
# However, crt might return a solution modulo product, but we can take x modulo product.
M = N1 * N2 * N3
x = x % M

# Compute integer cube root
m_cubed = Integer(x)
m = m_cubed.nth_root(3)

# Convert to bytes
from Crypto.Util.number import long_to_bytes
flag = long_to_bytes(int(m))
print("Flag:", flag)

# Write flag to flag.txt
with open('flag.txt', 'w') as f:
    f.write(flag.decode())