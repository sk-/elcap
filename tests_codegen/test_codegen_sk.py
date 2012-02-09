import ast
from collections import Counter

from unittest2 import TestCase

from elcap import codegen


class TestCodegen(TestCase):
    def test_if_elif_else(self):
        code = """if a:
    x()
elif b:
    y()
else:
    if c:
        z()"""
        self._check_code(code)

    def test_pow_to_expr(self):
        code = "(a) ** (b + c)"
        self._check_code(code)

    def test_composite_pow(self):
        code = "(a + b) ** (2)"
        self._check_code(code)

    def test_negative_expr(self):
        code = "(-(size_re - size_im))"
        self._check_code(code)

    def test_triple_quote_string(self):
        code = '''"""
    This
    is a multiline
    comment
."""'''
        self._check_code(code)

    def test_try_finally(self):
        code = """try:
    x()
finally:
    w()"""
        self._check_code(code)

    def test_except_finally(self):
        code = """try:
    x()
except:
    y()
finally:
    w()"""
        self._check_code(code)

    def test_else_except_finally(self):
        code = """try:
    x()
except:
    y()
else:
    z()
finally:
    w()"""
        self._check_code(code)

    def test_else_except(self):
        code = """try:
    x()
except:
    y()
else:
    z()"""
        self._check_code(code)

    def test_except(self):
        code = """try:
    x()
except:
    y()"""
        self._check_code(code)

    def _check_code(self, code):
        node = ast.parse(code)
        new_code = codegen.to_source(node)
        self.assertEquals(code, new_code)
