"""
1. This script will be uploaded and executed to 100s of machines in the intranet. These machines are meant to be
monitored for system level statistics like memory usage, CPU usage, total uptime and windows security event logs (in
case of windows OS).

2. When executed, the client script collects the statistics and return them to the server script for cumulation.
3. The client script must encrypt the data before returning it to server.
"""
