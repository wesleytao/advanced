import re
import math
import numpy as np

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

class Expr:
  def __init__(self, op, l, r):
    self.op = op
    self.l = l
    self.r = r

  def __str__(self):
    return "%s %s %s" % (self.l, self.op, self.r)

class Literal:
  def __init__(self, v):
    self.v = v

  def __str__(self):
    return str(self.v)

grammar = Grammar(
	r"""
	exprstmt = ws expr ws
	expr     = biexpr / value
	biexpr   = value ws op ws expr
    op       = "+"
	value    = ~"\d*\.?\d+"i
	ws       = ~"\s*"i
	wsp      = ~"\s+"i
	""")

class Visitor(NodeVisitor):
  grammar = grammar

  def visit_expr(self, node, children):
	return children[0]

  def visit_op(self, node, children):
    return node.text

  def visit_biexpr(self, node, children):
	return Expr(children[2], children[0], children[-1])

  def visit_value(self, node, children):
	return Literal(float(node.text))

  def generic_visit(self, node, children):
	f = lambda v: v and (not isinstance(v, str) or v.strip())
	children = list(filter(f, children))
	if len(children) == 1: 
	  return children[0]
	return children

print Visitor().parse("1 + 2 + 3")

