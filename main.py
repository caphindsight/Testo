import loader
import runner
import sandbox
import reporter

def run_tests():
  box = sandbox.Sandbox(3)
  prob = loader.load_problem('/home/solenodonus/ienv/testo_data/a_plus_b')
  rn = runner.Runner(box)
  prog = '/home/solenodonus/ienv/main'
  rep = reporter.Reporter()
  return rn.run_tests(prob, prog, rep)
