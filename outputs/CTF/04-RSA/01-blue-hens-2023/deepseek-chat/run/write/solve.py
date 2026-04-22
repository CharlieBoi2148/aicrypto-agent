#!/usr/bin/env python3
from helper import *

# Extended Euclidean algorithm
def egcd(a, b):
    if b == 0:
        return (1, 0, a)
    else:
        x, y, g = egcd(b, a % b)
        return (y, x - (a // b) * y, g)

# Compute a, b such that a*e1 + b*e2 = 1
a, b, g = egcd(e1, e2)
print(f"a = {a}, b = {b}, gcd = {g}")

# Ensure gcd is 1
assert g == 1

# Compute message m = c1^a * c2^b mod n
# If a is negative, compute c1^a as pow(c1_inv, -a, n)
# Similarly for b
if a < 0:
    c1_inv = pow(c1, -1, n)
    part1 = pow(c1_inv, -a, n)
else:
    part1 = pow(c1, a, n)

if b < 0:
    c2_inv = pow(c2, -1, n)
    part2 = pow(c2_inv, -b, n)
else:
    part2 = pow(c2, b, n)

m = (part1 * part2) % n
print(f"Recovered message (as integer): {m}")

# Convert to bytes
from Crypto.Util.number import long_to_bytes
flag = long_to_bytes(m)
print(f"Flag: {flag}")

# Write flag to flag.txt
with open('flag.txt', 'wb') as f:
    f.write(flag)