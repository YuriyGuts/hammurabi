import java.io.*;
import java.util.*;

public class Hworld {

    public static void main(String[] args) throws IOException {
        String inputFileName = args.length >= 2 ? args[0] : "hworld.in";
        String outputFileName = args.length >= 2 ? args[1] : "hworld.out";

        HworldInputData inputData = readInput(inputFileName);
        HworldOutputData outputData = solve(inputData);
        writeOutput(outputFileName, outputData);
    }

    private static HworldInputData readInput(String inputFileName) throws IOException {
        File inputFile = new File(inputFileName);
        try (FileReader inputFileReader = new FileReader(inputFile)) {
            try (BufferedReader bufferedReader = new BufferedReader(inputFileReader)) {
                int count = Integer.valueOf(bufferedReader.readLine());
                return new HworldInputData(count);
            }
        }
    }

    private static HworldOutputData solve(HworldInputData inputData) {
        String lines = Collections.nCopies(inputData.getCount(), "Hello world!");
        return new HworldOutputData(lines);
    }

    private static void writeOutput(String outputFileName, HworldOutputData outputData) throws IOException {
        try (Writer outputFileWriter = new FileWriter(outputFileName)) {
            for (String line: outputData.getLines()) {
                outputFileWriter.write(line);
                outputFileWriter.write("\n");
            }
        }
    }
}
