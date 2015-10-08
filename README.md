# hammurabi
An online judge for algorithmic contests. Strict, but fair.

This project is currently in development. The goal is to support the following major features:

1. (Kinda done) Automatic grader component.
2. Web UI for dashboards and submissions.
3. Operational datastore and a Web API for accessing execution results and stats.
4. Deployability: Cloud-ready, Docker-ready, etc.

## Grader

An alpha version of the automated grader is currently usable.

It can discover, compile and run solutions in Java, Python, Ruby, Node.js, and C# (more languages to come in the future). It can detect compilation and runtime errors, invalid output formats, terminate programs on timeout and report execution timings.

At the end of a run, it generates HTML reports with detailed logs.

![Sample output from grader](/assets/grader-sample-output.png)
