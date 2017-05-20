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


class TableCol:
  def __init__(self, name, width=None, align_mode=AlignMode.LEFT):
    self.name = name
    self.width = width
    self.align_mode = align_mode


class ConsoleTable:
  def __init__(self, cols):
    self.cols = cols

  def post(self, **kw):
    for col in self.cols:
      val = kw.get(col.name)
      if val is None: val = ''
      if col.width is not None:
        val = _align(val, col.width, col.align_mode)
      sys.stdout.write(val + '  ')
    sys.stdout.write('\n')
    sys.stdout.flush()
