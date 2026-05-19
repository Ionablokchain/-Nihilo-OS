#!/usr/bin/env python3
"""
paradox_generator.py - Generate random paradox challenge strings.

Usage:
    paradox_generator.py [--type prime|causal|self] [--seed N] [--length L]

Outputs a paradox string that can be used for authentication testing.
"""

import sys
import random
import argparse

PRIMES = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71]

def generate_prime_paradox(seed: int, length: int) -> str:
    rng = random.Random(seed)
    seq = [rng.choice(PRIMES) for _ in range(length)]
    code = seq[0] ^ seq[1] ^ seq[2] if length >= 3 else seq[0]
    return f"prime:{code}:{seed}:{length}"

def generate_causal_loop(seed: int, loop: int) -> str:
    code = seed ^ loop
    return f"causal:{code}:{seed}:{loop}"

def generate_self_referential(seed: int) -> str:
    code = seed ^ (seed >> 16)
    return f"self:{code}:{seed}"

def main():
    parser = argparse.ArgumentParser(description='Generate paradox challenge')
    parser.add_argument('--type', '-t', default='prime', choices=['prime', 'causal', 'self'], help='Paradox type')
    parser.add_argument('--seed', '-s', type=int, default=None, help='Random seed')
    parser.add_argument('--length', '-l', type=int, default=3, help='Length for prime paradox')
    parser.add_argument('--loop', '-L', type=int, default=0, help='Loop value for causal paradox')
    args = parser.parse_args()

    if args.seed is None:
        args.seed = random.randint(0, 2**16-1)

    if args.type == 'prime':
        result = generate_prime_paradox(args.seed, args.length)
    elif args.type == 'causal':
        result = generate_causal_loop(args.seed, args.loop)
    else:
        result = generate_self_referential(args.seed)

    print(result)

if __name__ == '__main__':
    main()