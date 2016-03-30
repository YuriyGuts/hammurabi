This is the default location for problem definitions and submissions.

The problems should follow this directory layout:

```
|
|-- %problem1_name%
|   |-- solutions
|   |   |-- %author1_name%
|   |   |   |-- %sourcefile1%.java
|   |   |   |-- %sourcefile2%.java
|   |   |-- %author2_name%
|   |   |   |-- %sourcefile1%.py
|   |   |-- %author3_name%
|   |   |   |-- (...arbitrary tree depth...)
|   |   |   | ...... |-- %sourcefile%.java
|   |-- testcases
|   |   |-- 01.in
|   |   |-- 02.in
|   |   |-- 03.in
|   |-- answers
|   |   |-- 01.out
|   |   |-- 02.out
|   |   |-- 03.out
|   |-- problem.conf
|-- %problem2_name%
|   |-- solutions
|   |-- testcases
|   |-- answers
|   |-- problem.conf
```
