import base64
import os
import yaml


def load_problem(directory):
  assert os.path.isdir(directory)
  problem = os.path.basename(directory)
  config_file = os.path.join(directory, problem + '.yml')
  config = yaml.load(open(config_file, 'r').read())
  obj = {'problem': problem}
  obj['title'] = config['title']
  obj['checker'] = config['checker']
  obj['limits'] = config['limits']
  obj['testsets'] = []
  config_testsets = config['testsets']
  for config_testset in config_testsets:
    obj_testset = {'testset': config_testset['testset']}
    obj_testset['type'] = config_testset['type']
    if obj_testset['type'] == 'prepared':
      obj_testset['tests'] = []
      testset_dir = os.path.join(directory, config_testset['testset'])
      for f in os.listdir(testset_dir):
        test_input_file = os.path.join(testset_dir, f)
        test_answer_file = os.path.join(testset_dir, f) + '.a'
        if os.path.isfile(test_input_file) and os.path.isfile(test_answer_file):
          input_base64 = base64.b64encode(open(test_input_file, 'r').read())
          answer_base64 = base64.b64encode(open(test_answer_file, 'r').read())
          obj_testset['tests'].append({
            'test': f,
            'input_b64': input_base64,
            'answer_b64': answer_base64
          })
    else:
      raise Exception('Unsupported testset type: %s', obj_testset['type'])
    obj['testsets'].append(obj_testset)
  obj['yaml_b64'] = base64.b64encode(open(config_file, 'r').read())
  return obj


def save_problem(obj, parent_dir):
  problem_dir = os.path.join(parent_dir, obj['problem'])
  assert os.path.isdir(parent_dir), 'Directory not found: %s' % parent_dir
  assert not os.path.exists(problem_dir), 'Directory already exists: %s' % problem_dir
  os.makedirs(problem_dir)
  for testset in obj['testsets']:
    if 'tests' in testset:
      testset_dir = os.path.join(problem_dir, testset['testset'])
      os.makedirs(testset_dir)
      for test in testset['tests']:
        f = test['test']
        input = base64.b64decode(test['input_b64'])
        answer = base64.b64decode(test['answer_b64'])
        input_file = os.path.join(testset_dir, f)
        answer_file = input_file + '.a'
        with open(input_file, 'w') as input_stream:
          input_stream.write(input)
        with open(answer_file, 'w') as answer_stream:
          answer_stream.write(answer)
  config_file = os.path.join(problem_dir, obj['problem'] + '.yml')
  with open(config_file, 'w') as config_stream:
    config_stream.write(base64.b64decode(obj['yaml_b64']))
