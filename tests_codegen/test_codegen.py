import re
import os
import sys
import ast
from collections import Counter

from unittest2 import TestCase

from elcap import codegen


class TestCodegen(TestCase):
    def test_codegen(self):
        os.path.walk('/home/skreft/sympy/', check_files, self)

def check_files(arg, dirname, filenames):
    for filename in filenames:
        if dirname.find('polys') != -1 or dirname.find('printing') != -1 or dirname.find('examples') != -1 or dirname.find('thirdparty') != -1 or dirname.find('mpmath') != -1 or dirname.find('plotting') != -1 or dirname.find('simplify') != -1:
            continue
        if filename in ['facts.py', 'evalf.py']:
            continue
        #if not filename.endswith('.py') or dirname.find('win32') != -1 or dirname.find('thirdparty') != -1 or filename in ['plot.py','pretty_symbology.py', 'test_repr.py', 'clock.py', 'glx.py', 'circuitplot.py', 'matrixutils.py', 'test_dagger.py', 'test_represent.py', 'test_matrixutils.py', 'avbin.py', 'ttf.py', 'identification.py', 'math2.py', 'elliptic.py', 'zeta.py', 'extratest_gamma.py', 'optimization.py', 'extrapolation.py', 'quadrature.py']:
        #    continue
        filename = os.path.join(dirname, filename)
        try:
            original_source = open(filename).read()
            node = ast.parse(original_source)
        except IndentationError:
            continue
        except TypeError:
            continue
        except IOError:
            print filename
            continue
        except SyntaxError:
            continue
        source = codegen.to_source(node)
        with open('/tmp/bla2.py', 'w') as fd:
            fd.write(source)
        #print filename
        try:
            new_node = ast.parse(source)
        except Exception as e:
            print filename
            raise e
        compiled_original = compile(node, '<string>', 'exec')
        compiled_new = compile(new_node, '<string>', 'exec')         
        a = compiled_original.co_code
        b = compiled_new.co_code
        #print source
        print 'FILENAME:', filename
        arg.assertEquals(Counter(a), Counter(b), filename)
