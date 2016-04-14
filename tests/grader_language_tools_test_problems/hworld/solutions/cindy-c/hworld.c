#include <stdio.h>
#include <stdlib.h>

int readInput(const char *fileName) {
    int count = 0;
    FILE *inputFile = fopen(fileName, "r");
    fscanf(inputFile, "%d", &count);
    fclose(inputFile);
    return count;
}

char** solve(int count) {
    char **result = (char **)calloc(count, sizeof(char *));
    for (int i = 0; i < count; i++) {
        result[i] = "Hello world!";
    }
    return result;
}

void writeOutput(const char *fileName, const char **lines, int count) {
    FILE *outputFile = fopen(fileName, "w");
    for (int i = 0; i < count; i++) {
        fprintf(outputFile, "%s\n", lines[i]);
    }
    fclose(outputFile);
}

int main(int argc, const char *argv[]) {
    int count = readInput("hworld.in");
    char **lines = solve(count);
    writeOutput("hworld.out", lines, count);
    return 0;
}
