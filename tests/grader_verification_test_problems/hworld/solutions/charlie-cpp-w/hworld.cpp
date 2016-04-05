#include <iostream>
#include <fstream>
#include <vector>

int readInput(std::string fileName) {
    std::ifstream inputFile(fileName, std::ifstream::in);
    
    int count;
    inputFile >> count;
    inputFile.close();

    return count;
}

std::vector<std::string> solve(int count) {
    std::vector<std::string> lines(count, "Hello World");
    return lines;
}

void writeOutput(std::string fileName, std::vector<std::string> lines) {
    std::ofstream outputFile(fileName, std::ifstream::out);
    for (std::string line: lines) {
        outputFile << line << std::endl;
    }
    outputFile.close();
}

int main(int argc, const char * argv[]) {
    auto count = readInput("hworld.in");
    auto lines = solve(count);
    writeOutput("hworld.out", lines);
    return 0;
}
