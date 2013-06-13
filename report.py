""" report.py
"""
import os
import sys
import inspect
from collections import namedtuple
from datetime import datetime, timedelta
import pygments
from pygments import highlight
from pygments.lexers import PythonLexer, PythonTracebackLexer
from pygments.formatters import HtmlFormatter, Terminal256Formatter
from pygments.console import colorize as console_color
from pygments.console import codes as console_codes

plex  = PythonLexer()
tblex = PythonTracebackLexer()
hfom  = HtmlFormatter()
hfom2 = HtmlFormatter(cssclass="autumn")
colorize  = lambda code: highlight(code, plex, hfom)
colorize2 = lambda code: highlight(code, plex, hfom2)
ROW_LEN_CACHE = dict(timestamp=None, stdout_row_length=None)

if not sys.stdout.isatty():
    # let's not work too hard if there is no one
    # to notice all the color
    console_color = lambda name, string: string
    stdout_row_length = lambda: 80
else:
    def stdout_row_length():
        """ returns the number of cols in the display.
            this is cached for CACHE_LENGTH amount of time,
            but after that it's recomputed.  this allows for
            terminal windows that are getting resized to behave
            as expected
        """
        if ROW_LEN_CACHE['stdout_row_length'] is None or \
           ROW_LEN_CACHE['timestamp'] < (datetime.now()-timedelta(seconds=10)):
            try:
                cols, rows = os.popen('stty size', 'r').read().split()
                rows = int(rows)
            except:
                rows = 80
            ROW_LEN_CACHE['stdout_row_length'] = int(rows)
            ROW_LEN_CACHE['timestamp'] = datetime.now()
        return ROW_LEN_CACHE['stdout_row_length']

def console2html(txt):
    return txt.replace('\n', '<br/>')

class console:
    """ from the pygments code--

        dark_colors  = ["black", "darkred", "darkgreen", "brown", "darkblue",
            "purple", "teal", "lightgray"]
        light_colors = ["darkgray", "red", "green", "yellow", "blue",
            "fuchsia", "turquoise", "white"]

        codes["darkteal"]   = codes["turquoise"]
        codes["darkyellow"] = codes["brown"]
        codes["fuscia"]     = codes["fuchsia"]
        codes["white"]      = codes["bold"]
    """
    html = staticmethod(console2html)
    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError
        def func(string, _print=False):
            z = console_color(name, string)
            if _print:
                print z
            return z
        return func

    def vertical_space(self):
        print

    @staticmethod
    def colortb(string):
        return highlight(string, tblex, Terminal256Formatter())

    if sys.stdout.isatty():
        def color(string):
            return highlight(string, plex, Terminal256Formatter()).strip()
    else:
        color = lambda string:string
    color = staticmethod(color)

    @staticmethod
    def draw_line(msg='', length=80, display=True):
        if msg and not msg.startswith(' '): msg = ' '+msg
        if msg and not msg.endswith(' '):   msg = msg+' '
        rlength = length - len(msg)
        out = '-' * (rlength/2)
        out+= msg + out
        out = console.red(out)
        if display:
            print out
        return out
console = console()

def whoami():
    """ gives information about the caller """
    return inspect.stack()[1][3]

def getcaller(level=2):
    """ """
    x = inspect.stack()[level]
    frame = x[0]
    file_name = x[1]
    flocals = frame.f_locals
    func_name = x[3]
    file = file_name
    self = flocals.get('self',None)
    kls  = (self is not None) and self.__class__
    kls_func = getattr(kls, func_name, None)
    if type(kls_func)==property:
        func = kls_func
    else:
        try:
            func = self and getattr(self, func_name)
        except AttributeError:
            func = func_name+'[nested]'
    return dict(file=file_name,
                kls=kls,
                self=self,
                func=func,
                func_name=func_name)

def whosdaddy(frames_back=3):
    """ displays information about the caller's caller """
    # if self is a named argument in the locals, print
    # the class name, otherwise admit that we don't know
    caller_info = getcaller(frames_back)
    kls         = caller_info['kls']
    file_name   = caller_info['file']
    func_name   = caller_info['func_name']
    header      = (kls and kls.__name__) or '<??>'
    header      = header + '.' + func_name
    file_parts  = file_name.split(os.path.sep)
    if len(file_parts) > 4:
        file_name = os.path.sep.join(file_parts[-4:])
    return file_name,header
    #return ' + ' + console.darkblue(file_name) + ' --  ' + console.blue(header)

def report(*args, **kargs):
    """ reporting mechanism with inspection and colorized output """
    stream = kargs.pop('stream', sys.stdout)
    frames_back = kargs.pop('frames_back', 3)
    header = kargs.pop('header', '')
    #_header = whosdaddy(frames_back);
    fname, caller = whosdaddy(frames_back)
    colored_header = ' ' + console.darkblue(fname) + ' --  ' + console.blue(caller)
    extra_length = len(' + '+' --  ') #ugh
    header_length = len(fname+caller)+extra_length
    if len(args)==1:
            _args = str(args[0])
            # if kargs appears to be a formatting string for the one and only
            # argument, then use it as such and set kargs to empty so it wont
            # be printed
            if len([ k for k in kargs if '{'+k+'}' in _args]) == len(kargs):
                try:
                    _args = _args.format(**kargs)
                except KeyError:
                    pass
                kargs = {}
            _args = _args.strip()
            # whenever terminal is wide enough to show both,
            # mash up the header with the other output
            if (len(_args+' -- ') + header_length) < stdout_row_length():
                _header = colored_header + ' -- ' + console.darkteal(_args)
                _args = ''
            else:
                _args = '  '+console.darkteal(_args)
                _header = colored_header
    else:
        from pprint import pprint
        from StringIO import StringIO
        s = StringIO()
        tmptmp = pprint(args, s)
        s.seek(0); tmptmp=s.read()
        _args = 'args=' + console.color(tmptmp).strip()+'\n'
    print _header
    _args = _args + '\n' if _args else _args
    _kargs =  console.color(str(kargs)) if kargs else ''
    _kargs = _kargs +'\n' if _kargs else _kargs
    sep = ' '
    output= sep + _args + sep + _kargs
    stream.write(output)
    stream.flush()

def getReporter(**unused):
    """ TODO: return a partial function """
    return report

report = getReporter()
report.console = console


class Reporter(object):
    """ syntactic sugar for reporting """
    def __init__(self, label=u'>>'):
        self.label = label

    def __getattr__(self, label):
        return self.__class__(label)

    def _report(self,msg):
        print colorize('{red}' + self.label + '{normal}: ' + msg)

    def _warn(self,msg):
        return self._report(msg)

    def __call__(self, msg):
        return self._report(msg)

simple = Reporter()
