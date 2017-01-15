=== Instructions to install and configure prerequisites or dependencies ===

To install dependencies, you must be on the Source directory.
It's necessary Python 2 >= 2.7.13.

Use virtualenv:
    virtualenv --python=/usr/local/lib/python2.7.13/bin/python pyEnv
    source pyEnv/bin/activate
    pip install -r requirements/server.txt


=== Instructions to create the database ===

The database initialization script can be found on the Source/sql directory.

In the MySQL interactive client you can type:
source init_database.sql

Alternatively you can pipe the data into mysql from the command line:
mysql < init_database.sql


=== Assumptions about the requirements ===

...


=== Not covered requirements ===

...


=== Faced issues ===

...

=== Feedback to improve the assignment ===

...
