# Disabling naming convention and method could be a function check.
# pylint: disable=C0103,R0201

import ast


#TODO: improve linemutator to also allows entities in which we look for the
#specific one.
#TODO: add tests for that case X True, x+y yield
class StringMutator(ast.NodeTransformer):
    def visit_Str(self, node):
        return ast.Str('XX' + node.s)


class NumberMutator(ast.NodeTransformer):
    def visit_Num(self, node):
        return ast.Num(node.n + 1)


class ArithmeticMutator(ast.NodeTransformer):
    mapping = {ast.Add: ast.Sub,
               ast.Sub: ast.Add,
               ast.Mult: ast.Div,
               ast.Div: ast.Mult,
               ast.FloorDiv: ast.Div,
               ast.Mod: ast.Div,
               ast.LShift: ast.RShift,
               ast.RShift: ast.LShift,
               ast.BitAnd: ast.BitOr,
               ast.BitOr: ast.BitAnd,
               ast.BitXor: ast.BitAnd,
               ast.Pow: ast.Mult}

    def visit_BinOp(self, node):
        return ast.BinOp(node.left, self.mapping[type(node.op)](), node.right)


class ComparisonMutator(ast.NodeTransformer):
    mapping = {ast.Eq: ast.NotEq,
               ast.NotEq: ast.Eq,
               ast.Gt: ast.LtE,
               ast.GtE: ast.Lt,
               ast.Lt: ast.GtE,
               ast.LtE: ast.Gt,
               ast.In: ast.NotIn,
               ast.NotIn: ast.In,
               ast.Is: ast.IsNot,
               ast.IsNot: ast.Is}

    def visit_Compare(self, node):
        return ast.Compare(node.left,
                           [self.mapping[type(op)]() for op in node.ops],
                           node.comparators)


class LogicalMutator(ast.NodeTransformer):
    mapping = {ast.And: ast.Or,
               ast.Or: ast.And}

    def visit_BoolOp(self, node):
        return ast.BoolOp(self.mapping[type(node.op)](), node.values)


class FlowMutator(ast.NodeTransformer):
    def visit_Continue(self, node):  # pylint: disable=W0613
        return ast.Break()

    def visit_Break(self, node):  # pylint: disable=W0613
        return ast.Continue()


class YieldMutator(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Yield):
            return ast.Return(node.value.value)
        return node


class BooleanMutator(ast.NodeTransformer):
    mapping = {'True': 'False',
               'False': 'True'}

    def visit_Name(self, node):
        if node.id in self.mapping:
            return ast.Name(self.mapping[node.id], node.ctx)
        return node


class LineMutator(ast.NodeTransformer):
    def __init__(self, mutator, code):
        super(LineMutator, self).__init__()
        self.line = 0
        self.mutator = mutator
        self.code = code.strip()
        self.found = False
        self.counter = 1
        self.current_counter = 0
        self.add_methods()

    def add_methods(self):
        visit_methods = [getattr(self.mutator, m)
                         for m in dir(self.mutator) if m.startswith('visit_')]
        for visit_method in visit_methods:
            def visit_helper(node):
                self.current_counter += 1
                if self.current_counter == self.counter:
                    modified_node = visit_method(node)
                    if modified_node != node:
                        self.found = True
                        if hasattr(node, 'lineno'):
                            self.line = node.lineno
                            modified_node.lineno = node.lineno
                            modified_node.col_offset = node.col_offset
                    return modified_node
                return node
            setattr(self, visit_method.__name__, visit_helper)

    def __iter__(self):
        return self

    def next(self):
        self.found = False
        self.current_counter = 0
        node = self.visit(ast.parse(self.code))
        if self.found:
            self.counter += 1
            return self.line, self.counter - 1, node
        else:
            raise StopIteration
