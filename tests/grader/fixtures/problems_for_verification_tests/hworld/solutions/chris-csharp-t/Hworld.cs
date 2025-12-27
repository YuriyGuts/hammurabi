using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading;

namespace Hworld
{
    internal class InputData
    {
        public int Count { get; private set; }

        public InputData(int count)
        {
            Count = count;
        }
    }

    internal class OutputData
    {
        public List<String> Lines { get; private set; }
        
        public OutputData(List<String> lines)
        {
            Lines = lines;
        }
    }
    
    internal class Hworld
    {
        public static void Main(string[] args)
        {
            string inputFileName = args.Length == 0 ? "hworld.in" : args[0];
            string outputFileName = args.Length == 0 ? "hworld.out" : args[1];
            
            InputData inputData = ReadInput(inputFileName);
            OutputData outputData = Solve(inputData);
            WriteOutput(outputFileName, outputData); 
        }
        
        private static InputData ReadInput(string fileName)
        {
            int count = int.Parse(File.ReadAllText(fileName));
            return new InputData(count);
        }
        
        private static OutputData Solve(InputData inputData)
        {
            Thread.Sleep(TimeSpan.FromSeconds(5));
            var lines = Enumerable.Range(0, inputData.Count).Select(i => "Hello world!").ToList(); 
            return new OutputData(lines);
        }
        
        private static void WriteOutput(string fileName, OutputData outputData)
        {
            File.WriteAllLines(fileName, outputData.Lines);
        }
    }
}
