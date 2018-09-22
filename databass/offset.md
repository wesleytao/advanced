## AA1: Add OFFSET to the LIMIT Clause


* Released: 9/13
* Due: 9/27 10AM
* Value: 3.75% of class grade
* Max team of 2



This assignment is part of the [DataBass Series of Advanced Assignment](./).  Take a look at the [README](./) in this directory to get an overview of the system and how to set it up.  Then read these instructions.  Since these advanced assignments are new and experimental, please be patient with us and [ask any questions on Piazza](https://piazza.com/class/jgwnwiy186d6pu).


The goal of this assignment is to modify the SQL parser, the operator implementations, and the interpretor to support the OFFSET statement in the LIMIT clause.    After completing this assignment, DataBass will be able to eecute queries such as 

        SELECT * FROM data LIMIT 10 OFFSET 5
        SELECT * FROM data LIMIT 10 OFFSET 2*5+1

But should fail for inputs with incorrect syntax

        SELECT * FROM data LIMIT 10 OFFSET

In addition, syntactically correct queries should be parsed but fail to run (`foo` is not defined):

        SELECT 1 LIMIT 10 OFFSET foo

#### Edits

* Updated specs to reflect that negative OFFSET values should raise an exception

#### The Parser

You will edit `parse_sql.py` in two places.  You will edit the [PEG grammar](https://pegjs.org/) to support the "OFFSET expression" syntax.   OFFSET is an optional part of the LIMIT clause.  If OFFSET is specified, then it should be followed by one or more white spaces, followed by an expression that evaluates to a number.  The expression cannot reference any attributes.
Further, the Visitor object transforms the parsed abstract syntax tree into the query plan.  Edit the `visit_limit` method to take into account the new OFFSET syntax.  


##### Parsing 101

A SQL query (or any program) is just a string.  The parser turns the string into a data structure that the system knows how to execute.  For SQL, this data structure is a query plan.  To do so, we typically use a _grammar_ to define the syntax of the language.  For example, let's say we want to support arithmetic expressions consisting of numbers and plus symbols.  Then we would write a list of _grammar rules_ such as the following:

        grammar = Grammar(
            r"""
            exprstmt = ws expr ws
            expr     = biexpr / value
            biexpr   = value ws op ws expr
            value    = ~"\d*\.?\d+"i
            op = "+" 
            ws       = ~"\s*"i
            wsp      = ~"\s+"i
            """)


A rule is composed of a head that is the rule's name (e.g., `exprstmt`) and the body (e.g., `ws expr ws`).  The body is a list of string literals (e.g., `+`) or another defined rule (e.g., `ws`).    For example, `ws expr ws` has three means that an expression is any number of white spaces (`ws`) as defined by the regular expression (`\s*`) followed by input characters that match an expression rule `expr` followed by any number of white spaces.  

The rule `expr = biexpr / value` contains a `/` symbol.  This means the input should either match `biexpr` or, if it doesn't match, a single `value`.  `biexpr` is further defined as a `value` followed by some whitespaces, a binary operator `+`, some whitespace, and an `expr`.

This grammar can parse expression strings such as

        1 + 2
        1.1
        1 + 2 + 3


A grammar itself is not enough to magically parse an input string.  What we want to turn the input string into an expression tree, such as

            +
           / \
          1   +
             / \
            2   3

Where each node is an object we have defined elsewhere.  To do so, the library we use provides a class called `NodeVisitor`.  Each time the parser successfully matches a grammar rule (e.g., `expr`), it will try to call the corresponding visitor method (e.g., `visit_expr()`) or the default method `generic_visit()`.  We can implement these `visit_XXX` rules to build our expression tree.   The final parsed object is whatever the visitor method for the root rule `exprstmt` returns.  


        class Visitor(NodeVisitor):
          grammar = grammar

          def visit_expr(self, node, children):
            return children[0]

          def visit_biexpr(self, node, children):
            return Expr(children[2], children[0], children[-1])

          def visit_op(self, node, children):
            return node.text

          def visit_value(self, node, children):
            return Literal(float(node.text))

          def generic_visit(self, node, children):
            f = lambda v: v and (not isinstance(v, str) or v.strip())
            children = list(filter(f, children))
            if len(children) == 1: 
              return children[0]
            return children

Each visitor method is passed the AST node of the matched rule, and the children for each nonterminal in the rule's body.  `children` is a list the same size as the rule's body, and each element is the return value of visiting the corresponding nonterminal.  For example, `children` for the `biexpr` rule has 5 elements:

        [<return value of visit_value>, None, <return value of visit_op>, None, <return value of visit_expr>]

This is why `visit_biexpr` creates an `Expr` object with the operator ("+"), and the left and right operands.

Finally, the following code parses "1 + 2 + 3" using our grammar and visitor implementation.

      print Visitor().parse("1 + 2 + 3")

The full example can be found in [parse_plus.py](./parse_plus.py).  Finally, take a look at the [parsimonious module's documentation](https://github.com/erikrose/parsimonious) for more detail.  It is an implementation of a PEG parser library. 

## The Assignment

In this assignment you will edit the parser in `parse_sql.py` to support the OFFSET syntax, and edit the LIMIT operator in `ops.py` to take offset information and take it into account during query execution.

#### Parse OFFSET

Edit the `limit` rule in the SQL grammar to recognize the `OFFSET [expression]` syntax.  The offset keyword in a query should be capitalized, followed by one or more spaces, and then an expression.  Note that the offset can be an expression:

        SELECT 1 FROM data LIMIT 1 OFFSET 1
        SELECT 1 FROM data LIMIT 1 OFFSET 10
        SELECT 1 FROM data LIMIT 1 OFFSET 1+10
        SELECT 1 FROM data LIMIT 1 OFFSET 1*10+4

However, it is NOT valid for OFFSET to be negative!

Further, you can assume that the offset expression will only be tested with arithmetic expressions that well not reference any attributes.  Thus do you don't need to worry about the following:

        SELECT 1 FROM data LIMIT 1 OFFSET 'blue'
        SELECT 1 FROM data LIMIT 1 OFFSET data.attr + 1

Further, make sure to edit the rule's visitor so that it initializes the Limit operator properly.  

#### The LIMIT Operator

At this point, databass will throw an exception during parsing because the Limit class' constructor needs to be modified to store the offset value.  Edit `ops.py` so that the Limit operator can take the offset as an optional paramater.  At this point, you should be able to parse queries with OFFSET, but it will not run correctly.

Now edit `Limit.__iter__()` so that if an offset is specified, the execution engine will correctly return the results offset by the amount specified in the OFFSET clause.

The SQL specs state that LIMIT and OFFSET cannot be negative.  Please make sure that if the OFFSET is negative, that you raise an exception (of any kind).


### Unit Tests

Copy `test_offset.py` into the `databass/src/engine/` folder and then run it.  All the tests should pass.  Take a look at the file to see what we are testing.   Feel free to add additional tests that we may not have included.  Our autograder contains a more complete set of test cases that we will evaluate your submission with.

### Submission Instructions


Go to the root of your databass codebase repository, and run `git pull` to make sure you have the most recent version.  You should see a submission script `submit.py`.

Run the submission script `submit.py` to package and zip your file.  It will ask you to submit you and your partners' UNIs and specify the assignment. It will create a zip file in the current directory.  Submit the generated ZIP file to Canvas. 

        python submit.py --help

Both partners should submit on their Canvas accounts to AA1.
