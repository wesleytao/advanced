## DataBass Assignments

This series of assignments are self contained, and will ask you to modify parts of the [DataBass](https://www.github.com/w4111/databass-public) database system.  DataBass is pretty full featured!  It can:

* Parse and translate SQL queries into a query plan, optimize the plan, and run it
* Supports SELECT, PROJECT, JOIN, GROUP BY, LIMIT, ORDER BY statements
* Supports nested queries
* Automatically registers CSV files as database tables
* Uses a simple cost-based optimizer to join ordering optimization

To get started, follow the instructions in the [project README](https://github.com/w4111/databass-public/blob/master/README.md) to install and run the database.

Now you are ready to [read the system architecture and documentation](https://github.com/w4111/databass-public/blob/master/docs/design.md)

Each assignment modifies a different part of the engine:

1. [Add OFFSET to DataBass](./offset.md)
1. [Query compilation](./compile.md)
1. [Join ordering optimization](./join.md)

