from pwn import *
import random
import sys

def parse_params(line):
    # line looks like: MySeededHash(12345, 65537)
    line = line.strip()
    if line.startswith('MySeededHash('):
        line = line[len('MySeededHash('):-1]  # remove trailing ')'
        parts = line.split(', ')
        N = int(parts[0])
        e = int(parts[1])
        return N, e
    else:
        raise ValueError("Unexpected line")

def int_to_bytes(x):
    return x.to_bytes(256, 'big')

def bytes_to_int(b):
    return int.from_bytes(b, 'big')

def generate_block(N):
    # generate random 2048-bit integer in [2, N-2]
    # ensure uniform
    while True:
        # random integer in [0, 2^2048-1]
        # but we need less than N
        # generate random bytes of length 256
        b = random.randbytes(256)
        x = bytes_to_int(b)
        if 2 <= x <= N-2:
            return b, x

def main():
    conn = remote('127.0.0.1', 1337)
    # receive first line: MySeededHash(...)
    line = conn.recvline().decode().strip()
    print(f"Received: {line}")
    N, e = parse_params(line)
    print(f"N = {N}")
    print(f"e = {e}")
    # receive prompt "Give me your string that hashes to 0..."
    conn.recvline()  # this line
    # We need to compute solution offline
    # Generate many blocks
    num_blocks = 2050  # slightly more than 2048
    blocks = []
    ints = []
    rsa_ints = []
    seen = set()
    for i in range(num_blocks):
        if i % 100 == 0:
            print(f"Generated {i} blocks")
        while True:
            b, x = generate_block(N)
            # compute RSA
            y = pow(x, e, N)
            # check collisions
            if b not in seen and y not in seen:
                seen.add(b)
                seen.add(y)
                blocks.append(b)
                ints.append(x)
                rsa_ints.append(y)
                break
    print(f"Generated {len(blocks)} blocks")
    # Build matrix over GF(2): each row is 2048 bits of rsa output
    # We'll use Python's bitarray or just list of ints for bits
    # We'll perform Gaussian elimination to find linear dependency
    # Use SageMath? But we can do with Python using bit operations.
    # Since 2048 bits, we can represent each row as integer (rsa_int).
    # XOR of rows corresponds to bitwise XOR of integers.
    # We need to find subset of rows whose XOR is zero.
    # This is same as finding linear dependency over GF(2) of vectors.
    # Use standard algorithm: maintain basis and track combinations.
    # We'll implement using integer representation.
    # Each row is 2048-bit integer, we treat as vector of bits.
    # We'll compute row-reduced echelon form.
    # Use list of (row_int, index, combo_mask) where combo_mask indicates which original rows contribute.
    rows = []  # list of (vector, combo_mask)
    for idx, r in enumerate(rsa_ints):
        v = r
        combo = 1 << idx  # bitmask of which original rows included (limited to 64 bits if idx>64)
        # But idx up to 2050, need bigger mask. Use Python integer as bitmask.
        combo = 1 << idx  # this works for large idx because Python ints are arbitrary precision.
        # Reduce with existing basis
        for basis_v, basis_combo in rows:
            # if leading bit of v is set, xor with basis
            # find highest set bit? Actually we need to eliminate bits from high to low.
            # Simpler: use Gaussian elimination over bits in any order, but we need consistent ordering.
            # We'll treat bits as positions 0..2047 (least significant bit?).
            # We'll maintain basis where each basis vector has a unique pivot bit.
            # Determine pivot bit of v: highest bit where v has 1.
            if v == 0:
                break
            # find highest set bit
            pivot = v.bit_length() - 1
            # check if we have a basis vector with same pivot
            # we need to store pivot for each basis vector.
            # Let's restructure: keep list of (pivot, basis_v, basis_combo)
            pass
    # Implementing full Gaussian elimination over GF(2) with 2050x2048 is heavy but doable.
    # However, we can use SageMath's matrix over GF(2) which is more robust.
    # Since we have SageMath installed, we can write a Sage script.
    # But we need to interact with server using Python.
    # Alternative: Use Python's numpy? Not available.
    # Let's write a separate Sage script to compute dependency, then use results.
    # We'll output the indices of blocks to use.
    # Write data to file: list of rsa_ints as hex.
    with open('/tmp/rsa_ints.txt', 'w') as f:
        for y in rsa_ints:
            f.write(hex(y)[2:] + '\n')
    with open('/tmp/blocks.bin', 'wb') as f:
        for b in blocks:
            f.write(b)
    # Now call Sage script
    # We'll embed Sage code in Python using subprocess.
    sage_script = '''
import sys
# read ints
ints = []
with open('/tmp/rsa_ints.txt', 'r') as f:
    for line in f:
        ints.append(int(line.strip(), 16))
nbits = 2048
nvec = len(ints)
# Build matrix over GF(2)
M = matrix(GF(2), nvec, nbits)
for i, val in enumerate(ints):
    bits = val.bits()
    for j, b in enumerate(bits):
        M[i, j] = b
# Find kernel
K = M.kernel()
# Get a non-zero vector in kernel
if K.dimension() == 0:
    print("No dependency found")
    sys.exit(1)
# Take first basis vector of kernel
v = K.basis()[0]
# v is a vector of length nvec over GF(2)
# Get indices where v[i] == 1
indices = [i for i in range(nvec) if v[i] == 1]
print(" ".join(map(str, indices)))
'''
    # Write sage script to file
    with open('/tmp/compute_dep.sage', 'w') as f:
        f.write(sage_script)
    # Run sage
    import subprocess
    result = subprocess.run(['sage', '/tmp/compute_dep.sage'], capture_output=True, text=True)
    if result.returncode != 0:
        print("Sage computation failed:", result.stderr)
        sys.exit(1)
    indices = list(map(int, result.stdout.strip().split()))
    print(f"Selected {len(indices)} blocks")
    # Build preimage by concatenating blocks in any order? Order doesn't matter because XOR is commutative.
    preimage = b''.join(blocks[i] for i in indices)
    # Verify locally that XOR of RSA outputs is zero
    xor_sum = 0
    for i in indices:
        xor_sum ^= rsa_ints[i]
    # xor_sum is integer, convert to bytes
    xor_bytes = int_to_bytes(xor_sum)
    if all(b == 0 for b in xor_bytes):
        print("XOR zero verified")
    else:
        print("XOR not zero! Something wrong.")
        sys.exit(1)
    # Send hex
    conn.sendline(preimage.hex())
    # Receive response
    response = conn.recvall().decode()
    print(response)
    # Extract flag if present
    if 'irisctf{' in response:
        flag = response[response.find('irisctf{'):].split()[0].strip()
        with open('flag.txt', 'w') as f:
            f.write(flag)
    conn.close()

if __name__ == '__main__':
    main()