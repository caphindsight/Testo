class TestingSystemError(Exception):
  def __init__(msg):
    super(TestingSystemError, self).__init__(msg)

class GeneratorError(TestingSystemError):
  def __init__(msg, return_code=None, stdout=None):
    super(GeneratorError, self).__init__(msg)
    self.return_code = return_code
    self.stdout = stdout

class CheckerError(TestingSystemError):
  def __init__(msg, return_code=None, stdout=None, stderr=None):
    super(GeneratorError, self).__init__(msg)
    self.return_code = return_code
    self.stdout = stdout
    self.stderr = stderr

class ConfigError(Exception):
  def __init__(msg):
    super(ConfigError, self).__init__(msg)
