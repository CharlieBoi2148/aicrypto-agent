from helper import *

# Compute product of moduli
M = N1 * N2 * N3

# Compute CRT using Garner's algorithm for three moduli
# Solve x ≡ a1 mod n1, x ≡ a2 mod n2, x ≡ a3 mod n3
# We'll do stepwise: merge first two, then merge with third.
def crt2(a1, n1, a2, n2):
    # Solve x = a1 + n1 * t ≡ a2 mod n2
    # => n1 * t ≡ a2 - a1 mod n2
    # Compute modular inverse of n1 modulo n2
    g, inv, _ = extended_gcd(n1, n2)
    # g should be 1 since moduli are coprime (distinct primes)
    if g != 1:
        raise ValueError("Moduli not coprime")
    t = (a2 - a1) * inv % n2
    x = a1 + n1 * t
    modulus = n1 * n2
    return x % modulus, modulus

def extended_gcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    return g, x, y

# Merge first two
x12, mod12 = crt2(ct1, N1, ct2, N2)
# Merge with third
x, mod123 = crt2(x12, mod12, ct3, N3)
# x should be m^3

# Compute integer cube root
def integer_cube_root(n):
    # Binary search for cube root
    lo = 0
    hi = 1
    while hi ** 3 < n:
        hi <<= 1  # double until hi^3 >= n
    while lo < hi:
        mid = (lo + hi) // 2
        mid_cubed = mid * mid * mid
        if mid_cubed < n:
            lo = mid + 1
        else:
            hi = mid
    # lo is the smallest integer such that lo^3 >= n
    if lo * lo * lo == n:
        return lo
    else:
        # Should not happen
        raise ValueError("Not a perfect cube")

m = integer_cube_root(x)

# Convert to bytes
# Determine byte length: (m.bit_length() + 7) // 8
byte_length = (m.bit_length() + 7) // 8
flag_bytes = m.to_bytes(byte_length, 'big')
print("Flag:", flag_bytes.decode())

# Write flag to flag.txt
with open('flag.txt', 'w') as f:
    f.write(flag_bytes.decode())