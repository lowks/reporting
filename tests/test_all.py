""" test_all
"""
import os, sys
import unittest
from StringIO import StringIO
from contextlib import contextmanager

from report import config, report, truncate_file_path, console, Reporter

from pyparsing import (
    Literal, Word, Combine, Optional,
    Suppress, nums, delimitedList, oneOf, alphas)

ESC = Literal('\x1b')
integer = Word(nums)
escapeSeq = Combine(
    ESC + '[' + \
    Optional(delimitedList(integer,';')) + \
    oneOf(list(alphas)))
uncolor = lambda s : Suppress(escapeSeq).transformString(s)

TEST_MSG = "testing"

def function_name(a,b,c):
    report(TEST_MSG)

class MyClass(object):
    def method(self,a,b,c):
        report(TEST_MSG)
    @staticmethod
    def static_method(a, b, c):
        report(TEST_MSG)

class Tests(unittest.TestCase):

    def setUp(self):
        self.fxn = function_name
        self.kls = MyClass()
        new_out, new_err = StringIO(), StringIO()
        self.old_out, self.old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = new_out, new_err
        self.out = new_out
        self.err = new_err

    def tearDown(self):
        sys.stdout, sys.stderr = self.old_out, self.old_err

    def get_output(self):
        return uncolor(self.out.getvalue().strip())

    def assertOutputContains(self, x, err=None):
        output = self.get_output()
        err = err or "{0} not in {1}".format(x,output)
        self.assertTrue(x in output, err)

    def assertEndsWith(self, x, err=None):
        output = self.get_output()
        err = err or output
        self.assertTrue(output.endswith(x), err)

    def assertStartsWith(self, x, err=None):
        output = self.get_output()
        err = err or output
        self.assertTrue(output.startswith(x), err)

    def test_report_with_args(self):
        # this behaviour is not really well defined, as in it might not be stable
        # so here we will just exercise the function
        report("message",'random extra argument', 'another one')
        #output = self.get_output()

    def test_function(self):
        self.fxn(1, 2, 3)
        self.assertOutputContains(self.fxn.__name__)
        self.assertEndsWith(TEST_MSG)

    def test_method(self):
        self.kls.method(1,2,3)
        output = self.get_output()
        self.assertOutputContains(
            self.kls.__class__.__name__+'.'+self.kls.method.__name__)
        self.assertEndsWith(TEST_MSG)
        self.assertStartsWith(
            truncate_file_path(__file__))

    def test_newline_bug(self):
        self.kls.method(1,2,3)
        marker = 'MARKER'
        print marker
        output = self.get_output()
        output = output.split('\n')
        print output
        self.assertEqual(output[-1],marker)

    def test_static_method(self):
        self.kls.static_method(1,2,3)
        output = self.get_output()
        # frame info for staticmethod does not include class info
        self.assertOutputContains('<??>.static_method')

    def test_version_import(self):
        from report.version import __version__

    def test_draw_line_basic(self):
        console.draw_line()
        output = self.get_output()
        self.assertEqual(len(output), 80)

    def test_draw_line_msg(self):
        msg = 'hello world'
        console.draw_line(msg=msg)
        output = self.get_output()
        self.assertTrue(len(output)<80)
        self.assertOutputContains(msg)


    def test_external_module(self):
        import importlib
        demo = importlib.import_module('demo')
        demo.Object().instance_method()
        output = self.get_output()
        self.assertTrue(
            output.split()[0].endswith(
                os.path.join('tests','demo.py')))
        self.assertOutputContains('Object.instance_method')
        self.assertOutputContains('hello instance method!')

    def test_simple_reporter_object(self):
        reporter = Reporter()
        msg = "testing vanilla Reporter"
        reporter(msg)
        output = self.get_output()
        self.assertOutputContains(msg)

    def test_labeled_reporter_object(self):
        label = "some_label_here"
        reporter = Reporter(label)
        msg = "testing labeled Reporter"
        reporter(msg)
        output = self.get_output()
        self.assertOutputContains(msg)
        self.assertStartsWith(label)

    def test_labeled_reporter_object_warning(self):
        label = "some_label_here"
        reporter = Reporter(label)
        msg = "testing labeled Reporter warning"
        reporter.warn(msg)
        output = self.get_output()
        self.assertOutputContains(msg)
        self.assertStartsWith(label + '.WARNING')

    def test_nested_labeled_reporter_object(self):
        label = "some_label_here"
        reporter = Reporter(label)
        reporter = reporter.some_sub_label
        msg = "testing nested labeled Reporter"
        reporter(msg)
        output = self.get_output()
        self.assertOutputContains(msg)
        self.assertStartsWith(label+'.some_sub_label')
