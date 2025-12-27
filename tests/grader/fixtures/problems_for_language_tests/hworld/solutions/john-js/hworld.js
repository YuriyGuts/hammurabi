"use strict";

var fs = require("fs");

var readInput = function(fileName) {
    var fileLines = fs.readFileSync(fileName).toString().split("\n");
    var count = parseInt(fileLines[0], 10);
    return count;
};

var solve = function(count) {
    return Array(count).fill("Hello world!");
};

var writeOutput = function(fileName, lines) {
    fs.writeFileSync(fileName, lines.join("\n"));
};

var inputFileName = process.argv[2] || "hworld.in";
var outputFileName = process.argv[3] || "hworld.out";

var count = readInput(inputFileName);
var lines = solve(count);
writeOutput(outputFileName, lines);
