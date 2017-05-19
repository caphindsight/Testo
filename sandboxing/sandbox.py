from sandboxing import isolate

class Sandbox:
  def __init__(self, box_id):
    self.box_id = box_id

  def init(self):
    isolate.sandbox_init(self.box_id)

  def prepare(self, program_file, input_file):
    isolate.sandbox_prepare(self.box_id, program_file, input_file)

  def run(self, isolate_args):
    self.result = isolate.sandbox_run(self, isolate_args)
    return self.result

  def open_output(self):
    return open(self.output_file, 'r')

  def cleanup(self):
    isolate.sandbox_cleanup(self.box_id)
