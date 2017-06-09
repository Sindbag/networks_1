from itertools import combinations_with_replacement
from string import ascii_letters


def generate_names(alphabet=ascii_letters):
    i = 0
    for name in combinations_with_replacement(alphabet, 8):
        i += 1
    return i


if __name__ == "__main__":
    print(26 ** 8)
