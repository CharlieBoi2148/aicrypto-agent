from pwn import *
import random

def parse_params(line):
    line = line.strip()
    if line.startswith('MySeededHash('):
        line = line[len('MySeededHash('):-1]
        N_str, e_str = line.split(', ')
        return int(N_str), int(e_str)
    else:
        raise ValueError("Unexpected line")

def int_to_bytes(x):
    return x.to_bytes(256, 'big')

def bytes_to_int(b):
    return int.from_bytes(b, 'big')

def generate_block(N):
    # generate random 2048-bit integer in [2, N-2]
    while True:
        b = random.randbytes(256)
        x = bytes_to_int(b)
        if 2 <= x <= N-2:
            return b, x

def find_dependency(vectors, masks):
    # vectors: list of ints (each 2048-bit)
    # masks: list of int bitmasks indicating original index
    # returns mask of subset that XOR to zero, or None
    pivot_to_vec = {}  # pivot bit -> (vector, mask)
    for v, mask in zip(vectors, masks):
        # reduce v using existing basis
        while v != 0:
            pivot = v.bit_length() - 1
            if pivot in pivot_to_vec:
                basis_v, basis_mask = pivot_to_vec[pivot]
                v ^= basis_v
                mask ^= basis_mask
            else:
                pivot_to_vec[pivot] = (v, mask)
                break
        if v == 0:
            # found dependency
            return mask
    return None

def main():
    conn = remote('127.0.0.1', 1337)
    line = conn.recvline().decode().strip()
    print(f"Received: {line}")
    N, e = parse_params(line)
    print(f"N = {N}")
    print(f"e = {e}")
    conn.recvline()  # "Give me your string that hashes to 0..."

    # Generate blocks until we find a linear dependency
    blocks = []
    vectors = []  # RSA outputs as integers
    masks = []    # bitmask with single bit set
    seen = set()
    idx = 0
    while True:
        if idx % 100 == 0:
            print(f"Generated {idx} blocks")
        b, x = generate_block(N)
        y = pow(x, e, N)
        # check collisions
        if b in seen or y in seen:
            continue
        seen.add(b)
        seen.add(y)
        blocks.append(b)
        vectors.append(y)
        masks.append(1 << idx)
        # Try to find dependency
        dep_mask = find_dependency(vectors, masks.copy())
        if dep_mask is not None:
            print(f"Dependency found after {idx+1} blocks")
            # Extract indices where bit is set
            indices = []
            for i in range(idx+1):
                if dep_mask & (1 << i):
                    indices.append(i)
            print(f"Using {len(indices)} blocks")
            # Verify XOR zero
            xor_sum = 0
            for i in indices:
                xor_sum ^= vectors[i]
            if xor_sum == 0:
                print("XOR zero verified")
            else:
                print("XOR not zero, something wrong")
                continue
            # Build preimage
            preimage = b''.join(blocks[i] for i in indices)
            # Send
            conn.sendline(preimage.hex())
            # Get response
            response = conn.recvall().decode()
            print(response)
            if 'irisctf{' in response:
                flag = response[response.find('irisctf{'):].split()[0].strip()
                with open('flag.txt', 'w') as f:
                    f.write(flag)
                print(f"Flag saved: {flag}")
            else:
                print("Failed to get flag")
            break
        idx += 1
    conn.close()

if __name__ == '__main__':
    main()