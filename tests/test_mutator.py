import ast

from unittest2 import TestCase

import codegen
from elcap import mutator


class TestMutators(TestCase):
    def tearDown(self):
        node = ast.parse(self.code)
        modified_node = self.mutator.visit(node)
        self.assertEquals(codegen.to_source(modified_node), self.modified_code)

    def test_number_mutator(self):
        self.code = '2'
        self.modified_code = '3'
        self.mutator = mutator.NumberMutator()

    def test_string_mutator(self):
        self.code = "'string'"
        self.modified_code = "'XXstring'"
        self.mutator = mutator.StringMutator()

    def test_arithmetic_mutator(self):
        self.code = '\n'.join(['x + y', 'x - y', 'x * y', 'x / y', 'x // y', 'x % y', 'x << y', 'x >> y', 'x & y', 'x | y', 'x ^ y', 'x ** y'])
        self.modified_code = '\n'.join(['x - y', 'x + y', 'x / y', 'x * y', 'x / y', 'x / y', 'x >> y', 'x << y', 'x | y', 'x & y', 'x & y', 'x * y'])
        self.mutator = mutator.ArithmeticMutator()

    def test_comparison_mutator(self):
        self.code = '\n'.join(['x == y', 'x != y', 'x > y', 'x >= y', 'x < y', 'x <= y', 'x in y', 'x not in y', 'x is y', 'x is not y'])
        self.modified_code = '\n'.join(['(x != y)', '(x == y)', '(x <= y)', '(x < y)', '(x >= y)', '(x > y)', '(x not in y)', '(x in y)', '(x is not y)', '(x is y)'])
        self.mutator = mutator.ComparisonMutator()

    def test_logical_mutator(self):
        self.code = 'x and y\nx or y'
        self.modified_code = '(x or y)\n(x and y)'
        self.mutator = mutator.LogicalMutator()

    def test_yield_mutator(self):
        self.code = 'yield x'
        self.modified_code = 'return x'
        self.mutator = mutator.YieldMutator()

    def test_yield_mutator_on_another_expression(self):
        self.code = 'x < y'
        self.modified_code = '(x < y)'
        self.mutator = mutator.YieldMutator()

    def test_flow_mutator(self):
        self.code = """for i in x:
    continue
for i in x:
    break"""
        self.modified_code = """for i in x:
    break
for i in x:
    continue"""
        self.mutator = mutator.FlowMutator()

    def test_boolean_mutator(self):
        self.code = 'True\nFalse'
        self.modified_code = 'False\nTrue'
        self.mutator = mutator.BooleanMutator()

    def test_boolean_mutator_on_another_name(self):
        self.code = 'X'
        self.modified_code = 'X'
        self.mutator = mutator.BooleanMutator()

class TestLineMutator(TestCase):
    def test_line_mutator(self):
        code = "x = 1\ny = -1 + 10\nz = 'skip this'\nw = 200.0"
        number_mutator = mutator.NumberMutator()
        mutations = list(mutator.LineMutator(number_mutator, code))
        self.assertEquals([codegen.to_source(m) for line_no, pos, m in mutations], ["x = 2\ny = -1 + 10\nz = 'skip this'\nw = 200.0",
            "x = 1\ny = 0 + 10\nz = 'skip this'\nw = 200.0",
            "x = 1\ny = -1 + 11\nz = 'skip this'\nw = 200.0",
            "x = 1\ny = -1 + 10\nz = 'skip this'\nw = 201.0"])

    def test_line_mutator_compiles(self):
        #TODO: it would be nicer to grab the code from all the examples above
        code = """def f(x, y):
    for i in xrange(10):
        if i == 3 and True:
            continue
        yield x*i + y

def g(x, y, z):
    return x < y and z or x == 'bla'"""
        mutators = [mutator.LogicalMutator(), mutator.ArithmeticMutator(), mutator.ComparisonMutator(), mutator.YieldMutator(), mutator.FlowMutator(), mutator.StringMutator(), mutator.NumberMutator()]
        for m in mutators:
            mutations = list(mutator.LineMutator(m, code))
            for line_no, pos, mutation in mutations:
                self._check_ast_compiles(mutation)

    def _check_ast_compiles(self, node):
        compile(node, '<string>', 'exec')
