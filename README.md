# Connections-Monitor
The project allows to evaluate connections which are created - both local and foreign ones. 
Information about processes, foreign hosts IPv4 addresses, country of connection's source/destination, software ports, interfaces, date and time, connections' state, servers' names and server description are saved to a local database file. It allows users to explore different aspects regarding registered connections.

The application was written in Python and is still under development. For now, only the CMD version is available, however, a GUI version will be available soon.

The application accepts a command line argument of `u` in order to update database file regularly using a batch file. Providing `u` updates the database file and quits the program.
