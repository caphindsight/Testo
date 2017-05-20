import os
import shutil

from constants import WHICH_ISOLATE, SANDBOX_DATA_DIR
from subprocess import *


class MountOpts:
  READ_ONLY = 1,
  READ_AND_WRITE = 2,


class FileMod:
  INPUT = 0644
  OUTPUT = 0666
  EXECUTABLE = 0555


class MountPoint:
  def __init__(self, host_path, cont_path, dir_opts):
    self.cont_path = cont_path
    self.host_path = host_path
    self.dir_opts = dir_opts

  def to_cmd_args(self):
    suffix = ''
    if self.dir_opts == MountOpts.READ_AND_WRITE:
      suffix = ':rw'
    return ['-d', '%s=%s%s' % (self.cont_path, self.host_path, suffix)]


class Redirects:
  def __init__(self, stdin=None, stdout=None, stderr=None):
    self.stdin = stdin
    self.stdout = stdout
    self.stderr = stderr

  def to_cmd_args(self):
    args = []
    if self.stdin is not None:
      args.extend(['--stdin', self.stdin])
    if self.stdout is not None:
      args.extend(['--stdout', self.stdout])
    if self.stderr is not None:
      args.extend(['--stderr', self.stderr])
    return args


class Limits:
  def __init__(self, time_limit=None,
      mem_limit=None, disk_limit=None, stack_limit=None):
    self.time_limit = time_limit
    self.mem_limit = mem_limit
    self.disk_limit = disk_limit
    self.stack_limit = stack_limit

  def to_cmd_args(self):
    args = []
    if self.time_limit is not None:
      args.extend(['-t', self.time_limit, '-x', self.time_limit * 0.2])
    if self.mem_limit is not None:
      args.extend(['-m', self.mem_limit])
    if self.disk_limit is not None:
      args.extend(['-f', self.disk_limit])
    if self.stack_limit is not None:
      args.extend(['-k', self.stack_limit])
    return args

  def merge(global_limits, limits):
    if limits is None:
      return global_limits
    return Limits(
      time_limit = limits.time_limit if limits.time_limit is not None
                   else global_limits.time_limit,
      mem_limit = limits.mem_limit if limits.mem_limit is not None
                   else global_limits.mem_limit,
      disk_limit = limits.disk_limit if limits.disk_limit is not None
                   else global_limits.disk_limit,
      stack_limit = limits.stack_limit if limits.stack_limit is not None
                   else global_limits.stack_limit
    )


class IsolateRes:
  def __init__(self, return_code, isolate_stderr, meta):
    self.return_code = return_code
    self.isolate_stderr = isolate_stderr
    self.meta = meta


def _run_isolate(args):
  p = Popen([WHICH_ISOLATE] + [str(i) for i in args],
      stdin=PIPE, stdout=PIPE, stderr=PIPE)
  p.wait()
  return p


def _read_meta(meta_file):
  if not os.path.exists(meta_file):
    return dict()
  with open(meta_file, 'r') as f:
    lines = f.readlines()
  meta = dict()
  for line in lines:
    line_stripped = line.strip('\n')
    line_splitted = line_stripped.split(':')
    if len(line_splitted) > 0:
      key = line_splitted[0]
      val = ':'.join(line_splitted[1:])
      meta[key] = val
  return meta


class Sandbox:
  def __init__(self, box_id):
    self.box_id = box_id
    self.box_dir = os.path.join(SANDBOX_DATA_DIR, 'isolated_box_%s' % box_id)
    self.mounts = dict()

  def create(self):
    _run_isolate(['-b', self.box_id, '--init'])
    self.clean()

  def delete(self):
    if os.path.exists(self.box_dir):
      shutil.rmtree(self.box_dir)
    _run_isolate(['-b', self.box_id, '--cleanup'])

  def clean(self, subdir=''):
    relevant_dir = os.path.join(self.box_dir, subdir)
    if os.path.exists(relevant_dir):
      shutil.rmtree(relevant_dir)
    os.makedirs(relevant_dir)

  def get_file(self, relative_path):
    return os.path.join(self.box_dir, relative_path)

  def mount(self, dir_name, mount_opts):
    internal_dir = self.get_file(dir_name)
    if not os.path.exists(internal_dir):
      os.makedirs(internal_dir)
    self.mounts[dir_name] = MountPoint(internal_dir, '/%s' % dir_name, mount_opts)

  def umount(self, dir_name):
    del self.mounts[dir_name]

  def prepare_file(self, relative_path, mod=FileMod.INPUT):
    internal_file_path = self.get_file(relative_path)
    open(internal_file_path, 'w').close()
    os.chmod(internal_file_path, mod)
    return internal_file_path

  def open_prepared_file(self, relative_path, mod=FileMod.INPUT):
    internal_file_path = prepare_file(self, relative_path, mod)
    return open(internal_file_path, 'w')

  def copy_file(self, origin, relative_path, mod=FileMod.INPUT):
    internal_file_path = self.get_file(relative_path)
    shutil.copyfile(origin, internal_file_path)
    os.chmod(internal_file_path, mod)

  def run(self, program, redirects=Redirects(), limits=Limits()):
    args = []
    meta_file = self.get_file('META')
    args.extend(['-b', self.box_id, '-M', meta_file])
    for mount in self.mounts:
      args.extend(self.mounts[mount].to_cmd_args())
    args.extend(redirects.to_cmd_args())
    args.extend(limits.to_cmd_args())
    args.extend(['--run', program])
    p = _run_isolate(args)
    meta = _read_meta(meta_file)
    os.remove(meta_file)
    return IsolateRes(return_code=p.returncode,
        isolate_stderr=p.stderr.read(), meta=meta)
