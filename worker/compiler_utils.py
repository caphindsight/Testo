from subprocess import Popen, PIPE


class Language:
  CXX_11 = 'cxx11'


def file_extension(language):
  if language == Language.CXX_11:
    return '.cc'
  else:
    return '.txt'


class CompilationRes:
  def __init__(self, success, compiler_log):
    self.success=success
    self.compiler_log = compiler_log


def _run_compiler(*cmdline):
  p = Popen([str(i) for i in cmdline], stdin=PIPE, stdout=PIPE, stderr=PIPE,
      timeout=5)  # 5 seconds timeout for all compilers
  p.wait()
  compiler_log = p.stderr.read()
  if compiler_log == '':
    compiler_log = p.stdout.read()
  return CompilationRes(p.returncode == 0, compiler_log)


def _compile_cxx_11(sandbox, source_file, target_file):
  return _run_compiler('/usr/bin/g++', '-O2', '-std=c++11', '-ftemplate-depth-128',
                '-fstack-protector-all', '-o', target_file,
                source_file)


def compile(sandbox, source_file, target_file, language):
  if language == Language.CXX_11:
    return _compile_cxx_11(sandbox, source_file, target_file)
  else:
    return CompilationRes(False, 'Unsupported compiler: %s' % language)
