def main()
    input_filename = ARGV.length == 0 ? "hworld.in" : ARGV[0]
    output_filename = ARGV.length == 0 ? "hworld.out" : ARGV[1]

    count = read_input(input_filename)
    lines = solve(count)
    write_output(output_filename, lines)
end


def read_input(filename)
    return File.read(filename).to_i
end


def solve(count)
    return ["Hello world!"] * (count + 1)
end


def write_output(filename, lines)
    File.write(filename, lines.join("\n"))
end


main()
