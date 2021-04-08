# Connections-Monitor
The project allows to evaluate connections which are created, as well as local connections. Information about processes, foreign hosts, country of connection's source/destination, software ports, interfaces, date and time, connections' state, servers' names and server description are saved to a local database file. It allows the user to explore different aspects regarding registered connections.

The application was written in Python and is still under development. For now, only the CMD version is available, however, a GUI version will be available soon.
Apart from Python files, it is possible to download an executable version for Windows (EXE), which is preapred to run instantly.
https://github.com/p-stachyra/Connections-Monitor/tree/master

The application accepts a command line argument of `u` in order to update database file regularly using a batch file. Providing `u` updates the database file and quits the program.
