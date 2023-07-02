# all2gpx
Extract track information from multibeam stored in Kongsberg .all format.
Can process a single file, or a directory of files.
Output does not contain elevation-data, but may be imlemented later, if I feel the need for it.
This is supposed to be a GUI-application, and is currently only tested on Windows.
May work on other .all files (sub bottom profiler etc), and should disregard data it does not recognize.

Uses pyall, a python module licensed under Apache License 2.0
[https://github.com/guardiangeomatics/pyall](https://github.com/guardiangeomatics/pyall)

## Usage
1. Select a file or folder containing .all-files.

2. Choose output .gpx file.

![A screenshot of the GUI](media/gui.png?raw=true "GUI")

Output will be split into tracks according to filename.