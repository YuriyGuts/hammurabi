import sys


def main():
    input_filename = "hworld.in" if len(sys.argv) == 1 else sys.argv[1]
    output_filename = "hworld.out" if len(sys.argv) == 1 else sys.argv[2]

    count = read_input(input_filename)
    lines = solve(count)
    write_output(output_filename, lines)


def read_input(filename):
    with open(filename) as input_file:
        count = int(input_file.readline())
        return count


def solve(count):
    return ["Hello world!" for _ in range(0, count)]


def write_output(filename, lines):
    with open(filename, "w") as output_file:
        output_file.write("\n".join(lines))


if __name__ == "__main__":
    main()
