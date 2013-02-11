import ast

from unittest2 import TestCase

import codegen
from elcap import mutator
import testpackage.samplemutator as samplemutator

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

    def test_boolean_mutator_on_assignment(self):
        self.code = 'x = True'
        self.modified_code = 'x = False'
        self.mutator = mutator.BooleanMutator()

class TestLineMutator(TestCase):
    def test_line_mutator(self):
        code = "x = 1\ny = -1 + 10\nz = 'skip this'\nw = 200.0"
        number_mutator = mutator.NumberMutator()
        mutations = list(mutator.LineMutator(number_mutator, code))
        self.assertEquals([codegen.to_source(m) for line_no, pos, m in mutations],
                          ["x = 2\ny = -1 + 10\nz = 'skip this'\nw = 200.0",
                           "x = 1\ny = 0 + 10\nz = 'skip this'\nw = 200.0",
                           "x = 1\ny = -1 + 11\nz = 'skip this'\nw = 200.0",
                           "x = 1\ny = -1 + 10\nz = 'skip this'\nw = 201.0"])

    def test_line_visitor_skips_nodes(self):
        code = "x = True"
        boolean_mutator = mutator.BooleanMutator()
        mutations = list(mutator.LineMutator(boolean_mutator, code))
        self.assertEquals([codegen.to_source(m) for line_no, pos, m in mutations],
                          ["x = False"])

    def test_line_mutator_compiles(self):
        # TODO: it would be nice to grab the code from all the examples above.
        code = """def f(x, y):
    for i in xrange(10):
        if i == 3 and True:
            continue
        yield x*i + y

def g(x, y, z):
    return x < y and z or x == 'bla'"""
        mutators = [mutator.LogicalMutator(),
                    mutator.ArithmeticMutator(),
                    mutator.ComparisonMutator(),
                    mutator.YieldMutator(),
                    mutator.FlowMutator(),
                    mutator.StringMutator(),
                    mutator.NumberMutator()]
        for m in mutators:
            mutations = list(mutator.LineMutator(m, code))
            for line_no, pos, mutation in mutations:
                self._check_ast_compiles(mutation)

    def _check_ast_compiles(self, node):
        compile(node, '<string>', 'exec')


class TestCodeMutator(TestCase):
    def test_code_mutator_multiple_classes(self):
        def line_filter(line, line_no):
            return True

        code = "x = 1\ny = True"
        mutators = [mutator.NumberMutator, mutator.BooleanMutator]
        mutations = list(mutator.code_mutator(mutators, code, line_filter))
        self.assertEquals(["x = 2\ny = True",
                           "x = 1\ny = False"],
                          [codegen.to_source(m) for line_no, pos, m, class_name in mutations])

    def test_code_mutator_with_filter(self):
        def line_filter(line, line_no):
            return line_no % 2 == 1

        code = "x = 1\ny = 2\nz = 3\nw = 4"
        mutators = [mutator.NumberMutator]
        mutations = list(mutator.code_mutator(mutators, code, line_filter))
        self.assertEquals(["x = 2\ny = 2\nz = 3\nw = 4",
                           "x = 1\ny = 2\nz = 4\nw = 4"],
                          [codegen.to_source(m) for line_no, pos, m, class_name in mutations])

class TestMutatorDiscoverer(TestCase):
    def test_discoverer_no_arguments(self):
        mutators = [mutator.ArithmeticMutator,
                    mutator.BooleanMutator,
                    mutator.ComparisonMutator,
                    mutator.FlowMutator,
                    mutator.LogicalMutator,
                    mutator.NumberMutator,
                    mutator.StringMutator,
                    mutator.YieldMutator]
        self.assertTrue(mutators, mutator.discover())

    def test_discoverer_with_default_module(self):
        mutators = [mutator.ArithmeticMutator,
                    mutator.BooleanMutator,
                    mutator.ComparisonMutator,
                    mutator.FlowMutator,
                    mutator.LogicalMutator,
                    mutator.NumberMutator,
                    mutator.StringMutator,
                    mutator.YieldMutator]
        self.assertEqual(mutators, mutator.discover(['elcap.mutator']))

    def test_discoverer_with_default_module_and_classes(self):
        mutators = [mutator.BooleanMutator,
                    mutator.YieldMutator]
        self.assertEqual(mutators, mutator.discover(['elcap.mutator'],
                                                    ['BooleanMutator',
                                                     'YieldMutator']))

    def test_discoverer_with_modules(self):
        mutators = [samplemutator.MutatorA,
                    samplemutator.MutatorB,
                    mutator.ArithmeticMutator,
                    mutator.BooleanMutator,
                    mutator.ComparisonMutator,
                    mutator.FlowMutator,
                    mutator.LogicalMutator,
                    mutator.NumberMutator,
                    mutator.StringMutator,
                    mutator.YieldMutator]
        self.assertEqual(mutators,
                         mutator.discover(['testpackage.samplemutator',
                                           'elcap.mutator']))

    def test_discoverer_with_modules_and_classes(self):
        mutators = [samplemutator.MutatorB,
                    mutator.ArithmeticMutator]
        self.assertEqual(mutators,
                         mutator.discover(['testpackage.samplemutator',
                                           'elcap.mutator'],
                                          ['MutatorB', 'ArithmeticMutator']))