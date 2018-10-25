---
layout: page
---


[Advanced Assignments](./) > [DataBass](./databass)

## AA3: Query Compilation

* Released: 10/25
* Due: 11/8 10AM
* Value: 3.75% of your grade
* Max team of 2


This assignment is part of the [DataBass Series of Advanced Assignment](./).  Take a look at the [README](./) in this directory to get an overview of the system and how to set it up.  Then read these instructions.  Since these advanced assignments are new and experimental, please be patient with us and [ask any questions on Piazza](https://piazza.com/class/jgwnwiy186d6pu).


In this lab, you will go through the process of implementing query compilation for the projection operator in a very simple query plan.  Throughout this process, you will learn the basics of the producer-consumer model used to perform query compilation.  This can give you big performance speed ups.  

As an example, we ran the interpreted and compiled versions of the following query using the staff solutions to this assignment:

       SELECT COUNT(*)
         FROM (SELECT a AS a, b+c AS b
                 FROM data
                WHERE a < 9+1+1)
        WHERE a < b

The performance wins of compilation over interpretation was over 10x!

        Interpreted     3.8025290966
           Compiled     0.260922908783


## Background

We will first describe a simpler case of compiling arithmetic expressions, and then move onto the main idea behind compiling query plans.  We will then introduce the producer-consumer approach towards compilation, which you will implement in this assignment.

### Compiling Simple Expressions

Let's say we have the following expression in a SQL query

        a + (1 * 9)

This is parsed into an expression tree of the form:

            +
           / \
          a   *
             / \
            1   9
    
In a typical database, the expression is evaluated by interpreting this tree.  The root of the expression is actually a binary operator whose operator is `+`, and the left and right children are `a` and the subtree for `*`.  The expression is evaluated by recursively evaluating the children, getting their value, looking up the function to add the two values, and then returning:

        left_val = left_child.eval()
        right_val = right_child.eval()
        if op == "=":
          return left_val == right_val
        if op == "+":
          return left_val + right_val

This incurs the overhead of function calls, context switches, if/else statements, etc.  In contrast, if we now that the tuple is a dictionary called `row`, then we could magically compile the tree into the following Python statement that would run much much faster:

        row['a'] + (1 * 9)


#### Try it out

Take a look at `expr.py` and construct expression trees for the following expressions. 

        1 + 9
        (1 + 9) * 10
        a + 1
        a + b
        a = b

Now call `compile()` on the expressions and print the Python code that they generate.  


### Compiling Queries

The same idea applies to query plans.  Rather than using the Iterator model to interpret the query plan, we would like to generate raw Python code to run.  For example, the following query

        SELECT a + b AS val
        FROM data
        WHERE a > b

would ideally be compiled into the following program, where  `db` is a Database object that contains the table `data`.

        def q(db):
          for row in db['data']:
            if row['a'] > row['b']:
              val = row['a'] + row['b']
              yield dict(val=val)

The challenge is we can't just perform compilation in the same way we evaluate a query plan using the pull-based iterator model.  Take a look at the query plan for the above query:

            Project(a + b AS val)
                   |
              Filter(a > b)
                   |
              Scan(data)

Notice that project is at the _top_ of the query plan, whereas it is in the innermost block in the compiled program above.  In contrast, the Scan operator is at the _bottom_ of the query plan, even the for loop to scan the table is the first line of the compiled function.  If we asked Project to generate its code, and then called its child to generate the Filter code, we would have generated code in the opposite order:

        val = row['a'] + row['b']
        yield dict(val = val)
        if row['a'] > row['b']:
        ...

The produce-consumer model is one way to address this issue.  

### The Producer Consumer Model

The main idea is that we want Scan to generate its code first, and then Filter, and finally Project.
To do so, split compilation into two phases: a _produce_ phase that goes down from the top of the query plan to the bottom, followed by a _consume_ phase that goes from bottom to top.  The _consume_ phase is where most of the compiled code will be generated.

            Project(a + b AS val)
                 ↓    ↑
              Filter(a > b)
                 ↓    ↑       
               Scan(data) 
 

This is implemented by adding `produce()` and `consume()` methods to each query operator:

          class Op(object):

            def produce(self):
              # call child operator's produce()

            def consume(self):
              # generate Python code with proper indentation
              # then call parent operator's consume()


Calling `produce()` on the query plan's root operator (e.g., Project) will recursively call `produce()` for Filter and finally Scan.  The flow switches to the consume phase because the Scan operator's `produce()` method calls its own `consume()` method.    

To make this work, the produce phase will need to remember the order of operators that have been called.  We can do this by maintaining a stack, as in the following pseudocode:


          stack = []

          class Op(object):

            def produce(self):
              if has_child()
                stack.append(self)
                child.produce()
              else
                self.consume()

            def consume(self):
              # generate Python code with proper indentation
              stack.pop().consume()


## The Assignment

You will incrementally build a simple query compiler for queries consisting of Scan, Project, and Filter operators. [compiler.py](https://github.com/w4111/databass/blob/master/src/compiler/compiler.py)  contains scaffolding code for these operators as well as the implementation of the pull-based iterator execution model.  

Take a look at `Op.compile()` to see the driver that initiates the producer/consumer model and turns the generated to into a Python function object.  Each query operator subclasses `Op`, so calling `compile()` on any operator in the query plan will generate code for the operator's subtree.

We have also provided two helper classes: `CodeBlock` will help you when generating the compiled Python code,  and `Context` will help you manage the stack and other shared information during compilation.

Your task is to fill in the `produce()` and `consume()` methods in the operator classes.

#### Assignment 1: Expressions

As a warmup, you will add more functionality to expressions.  Edit the code in `exprs.py` to support the binary operations "-", ">=", "<=", and "!=".  We have added comments to the places where you may need to edit in the __call__ and compile functions.  Make sure that these operations can also be compiled!

Run the following as a sanity check that your implementation works.  Note that these tests are not exhaustive:

        python test_exprs.py


#### Assignment 2. Printing

Your first task is to implement query compilation for the Print and Scan operators.  This means that the following query plan: 

          Print
            |
          Scan("data")

Can be compiled into:

        for row in db["data"]:
          print row

To do so edit:

* `Op.produce(ctx)` to maintain the stack and ensure that the producer-phase of compilation flows top-down appropriately.
* `Print.consume(ctx)` to generate printing code
* `Scan.consume(ctx)` to generate the looping code.   It is ok to assume that the current record is always called `row` (or whatever you want to call it).  This is Ok because we will not implement Joins or more complex operators.  You will want to be careful to make sure that the generated code has proper indentation!


Test your code by running:

        python test_compiler.py

You should see that the print and scan tests pass but the other tests still fail.  

#### 3. Filtering

Now you will implement the Filter operator by editing `Filter.consume(ctx)`.  

Run `test_compiler.py`.  You should see that the filter tests now pass.
You can also just run `python test_compiler.py TestUnits.test_filter` to test filter in isolation.

#### 4: Projecting

Now you will implement the Projection operator by editing `Project.consume(ctx)`.    Take a look at how `Project.__iter__()` is implemented to understand how it works.  You will want to create a new record that is the result of the projection, and then assign `row` (or whatever you called the current record) to the new record so that the subsequent operators can use it.


Run `test_compiler.py`.  You should see that the projection tests now pass.
You can also just run `python test_compiler.py TestUnits.test_project` to test project in isolation.

#### 5: Counting

Now, you will implement a very simple version of Group By aggregation, where there is a single group and a single `COUNT(*)`.  In effect, it supports the following type of aggregation:

        SELECT COUNT(*) AS count
        FROM ...
        GROUP BY 1

Implement `Count.produce()` and `Count.consume()`, so that the following query plan:

          Count
            |
        Filter(a = b)
            |
         Scan(data)

Will be transformed into code that looks like the following.  Your code may be different, but should end up with a single row that is a dictionary with a key called `count` whose value is the number of records in the childe operator.

        n = 0
        for row in db["data"]:
          if row["a"] == row["b"]:
            n += 1
        row = dict(count=n)

You will need to need to also implement a custom `Count.produce()` method, because note how we needed to define and initialize `n = 0` before the Scan's for loop was generated.  Also after generating the Scan and Filter operators' code, we defined the final `row`.   

Once you implement this, all tests in `test_compiler.py` should now pass, and you can submit your code.

### Submission

Use the submit.py script to package your code. Run it from inside the main databass folder.

When prompted, give your UNI first, then your partner's.
If you did not work with a partner, put NONE in all caps.

Check the file to make sure no extra files were added.

This time, no points will be awarded for code that does not compile.
No points will be awarded to you if only your partner submits to Courseworks and
you do not.


### Final Comments


##### Limitations

You'll find that there are many limitations to our query compiled engine.  For one, it doesn't support joins.  The reason is because joins introduce >1 input tables, meaning we need to keep track of the names of each table, which table an attribute in an expression refers to, etc.  The amount of bookkeeping is a headache.  

Similarly, supporting aggregations can be challenging, because an aggregation like `avg()` tracks state (the sum and count so far) to incrementally compute the average.  This means you will want to allocate a `sum` and `count` variable inside the for loops.  However, what if your query computes two `avg()` statistics?  You can't blindly create the sam `sum` variable for both functions.  Now you need to keep track of variable names!

##### Further Reading

If you are interested, this idea was introduced in a paper called [Efficiently Compiling Efficient Query Plans for Modern Hardware](http://www.vldb.org/pvldb/vol4/p539-neumann.pdf), and forms the basis of most modern database engines.  Page 12 of [How to Architect a Query Compiler, Revisited](https://www.cs.purdue.edu/homes/rompf/papers/tahboub-sigmod18.pdf) has a diagram and writeup about the history of query compilation.

