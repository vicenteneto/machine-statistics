=== Instructions to install and configure prerequisites or dependencies (linux server) ===

First of all, to install dependencies, you must be on the Source directory.
Then, execute the script called configure.sh in scripts directory. This script will install the new Python 2.7.13.

    ./scripts/configure.sh

    # After the installation, you will be able to use the new Python 2.7.13 to create a new Python virtual environment.
    virtualenv --python=/usr/local/lib/python2.7.13/bin/python pyEnv
    source pyEnv/bin/activate
    pip install -r requirements/server.txt


=== Instructions to create the database ===

The database initialization script can be found on the Source/sql directory.

In the MySQL interactive client you can type:
source init_database.sql

Alternatively you can pipe the data into mysql from the command line:
mysql < init_database.sql


=== How to execute tests ===

On the Source directory, with the virtual environment activated, run:

    nosetests --with-coverage --cover-xml --cover-package=remote_statistics


=== Not covered requirements ===

Requirement 1.1 says to monitore the windows security event logs (in case of Windows OS), but my solution does not cover
this requirement.

Because my solution did not involve getting the Windows log events, they are not sent by email, as required in
requirement 2.5.
