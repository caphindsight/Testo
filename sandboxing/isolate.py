import os
import shutil

from subprocess import *


WHICH_ISOLATE = '/usr/local/bin/isolate'
SANDBOX_DATA_DIR = '/tmp'


class IsolationError(Exception):
  def __init__(self, return_code, stderr):
    self.return_code = return_code
    self.stderr = stderr


class IsolationArgs:
  def __init__(self, time_limit=None,
      mem_limit=None, disk_limit=None, stack_limit=None):
    self.time_limit = time_limit
    self.mem_limit = mem_limit
    self.disk_limit = disk_limit
    self.stack_limit = stack_limit


class IsolationResult:
  def __init__(self, return_code, output_file, metadata):
    self.return_code = return_code
    self.output_file = output_file
    self.metadata = metadata


def _run_isolate(*args):
  p = Popen([WHICH_ISOLATE] + [str(i) for i in args],
      stdin=PIPE, stdout=PIPE, stderr=PIPE)
  p.wait()
  return p


def _check_return_code(p):
  if p.returncode != 0:
    raise IsolationError(p.returncode, p.stderr.read())


def sandbox_init(boxId):
  p = _run_isolate('-b', boxId, '--init')
  _check_return_code(p)


def sandbox_cleanup(boxId):
  p = _run_isolate('-b', boxId, '--cleanup')
  _check_return_code(p)


def _prepared_data_dir(boxId):
  return os.path.join(SANDBOX_DATA_DIR, 'isolated_box_' + str(boxId))


def _touch_out_file(f):
  open(f, 'w').close()
  os.chmod(f, 0666)


def sandbox_prepare(boxId, program_file, input_file):
  prepared_data_dir = _prepared_data_dir(boxId)
  prepared_program_file = os.path.join(prepared_data_dir, 'program')
  prepared_input_file = os.path.join(prepared_data_dir, 'input.txt')

  if os.path.exists(prepared_data_dir):
    shutil.rmtree(prepared_data_dir)
  os.makedirs(prepared_data_dir)

  assert os.path.isfile(program_file)
  shutil.copyfile(program_file, prepared_program_file)
  os.chmod(prepared_program_file, 0775)
  
  assert os.path.isfile(input_file)
  shutil.copyfile(input_file, prepared_input_file)
  os.chmod(prepared_input_file, 0664)
  
  prepared_out_dir = os.path.join(prepared_data_dir, 'out')
  os.makedirs(prepared_out_dir)
  _touch_out_file(os.path.join(prepared_out_dir, 'stdout.txt'))
  _touch_out_file(os.path.join(prepared_out_dir, 'stderr.txt'))


def _read_metadata(meta_file):
  if not os.path.exists(meta_file):
    return dict()
  with open(meta_file, 'r') as f:
    lines = f.readlines()
  results = dict()
  for line in lines:
    line_stripped = line.strip('\n')
    line_splitted = line_stripped.split(':')
    if len(line_splitted) > 0:
      key = line_splitted[0]
      val = ':'.join(line_splitted[1:])
      results[key] = val
  return results


def sandbox_run(boxId, isolation_args):
  prepared_data_dir = _prepared_data_dir(boxId)
  prepared_program_file = os.path.join(prepared_data_dir, 'program')
  prepared_input_file = os.path.join(prepared_data_dir, 'input.txt')
  
  prepared_out_dir = os.path.join(prepared_data_dir, 'out')
  prepared_stdout_file = os.path.join(prepared_out_dir, 'stdout.txt')
  prepared_stderr_file = os.path.join(prepared_out_dir, 'stderr.txt')
  prepared_metadata_file = os.path.join(prepared_out_dir, 'metadata.txt')
  
  args = []
  args.extend(['-b', boxId, '-s', '-M', prepared_metadata_file])
  args.extend(['-d', '/ienv=' + prepared_data_dir])
  args.extend(['-d', '/iout=' + prepared_out_dir + ':rw'])
  args.extend(['-c', '/ienv'])
  args.extend(['--stdin', '/ienv/input.txt'])
  args.extend(['--stdout', '/iout/stdout.txt'])
  args.extend(['--stderr', '/iout/stderr.txt'])
  if isolation_args.time_limit is not None:
    args.extend(['-t', isolation_args.time_limit])
    args.extend(['-x', isolation_args.time_limit * 0.2])
  if isolation_args.mem_limit is not None:
    args.extend(['-m', isolation_args.mem_limit])
  if isolation_args.disk_limit is not None:
    args.extend(['-f', isolation_args.disk_limit])
  if isolation_args.stack_limit is not None:
    args.extend(['-k', isolation_args.stack_limit])

  args.extend(['--run', '/ienv/program'])

  p = _run_isolate(*args)
  metadata = _read_metadata(prepared_metadata_file)
  return IsolationResult(p.returncode, prepared_stdout_file, metadata)
