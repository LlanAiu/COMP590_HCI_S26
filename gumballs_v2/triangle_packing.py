from argparse import ArgumentParser

import math

def triangular_side_length(N):
    """
    Returns T(N): the minimal side length of an equilateral triangle
    that can contain N unit circles (assuming triangular lattice optimality).
    """
    # Solve m(m+1)/2 >= N
    m = math.ceil((math.sqrt(8*N + 1) - 1) / 2)
    
    return 2 * m

if __name__ == "__main__":
    parser = ArgumentParser()
    
    parser.add_argument("circles", type=int, help="Number of circles to pack")
    args_cli = parser.parse_args()
    
    length = triangular_side_length(args_cli.circles)
    print(f"T({args_cli.circles}) = {length}")