import os
import sys
import termcolor


class AlignMode:
  LEFT = 1
  RIGHT = 2


def _align(text, width, mode=AlignMode.LEFT, placeholder=' '):
  n = len(text)
  if n < width:
    extra = width - n
    extra_str = placeholder * extra
    if mode == AlignMode.LEFT:
      return text + extra_str
    elif mode == AlignMode.RIGHT:
      return extra_str + text
  elif n > width:
    k = n - 2
    circumsized = text[:k]
    return circumsized + '..'
  else:
    return text


class TableCol:
  def __init__(self, name, width=None, align_mode=AlignMode.LEFT):
    self.name = name
    self.width = width
    self.align_mode = align_mode


class ConsoleTable:
  def __init__(self, cols):
    self.cols = cols

  def fit_width(self, cs):
    if cs == 0:
      cs = int(os.popen('stty size', 'r').read().split()[1])
    cs -= 2 * len(self.cols)
    total_width = sum([col.width for col in self.cols])
    ratio = float(cs) / float(total_width)
    for col in self.cols:
      col.width = int(float(col.width) * ratio)

  def post(self, **kw):
    for col in self.cols:
      val = kw.get(col.name)
      if val is None: val = ''
      val = str(val).replace('\n', '  ')
      if col.width is not None:
        val = _align(val, col.width, col.align_mode)
      sys.stdout.write(val + '  ')
    sys.stdout.write('\n')
    sys.stdout.flush()

  def post_header(self, **kw):
    for col in self.cols:
      val = kw.get(col.name)
      if val is None: val = ''
      val = val.replace('\n', '  ')
      if col.width is not None:
        val = _align(val, col.width, col.align_mode)
      sys.stdout.write(termcolor.colored(val + '  ', attrs=['underline']))
    sys.stdout.write('\n')
    sys.stdout.flush()
