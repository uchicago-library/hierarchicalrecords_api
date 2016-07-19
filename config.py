class Config(object):
    with open('secret_key', 'r') as f:
        secret_key = f.read()
    storage_root = '/Users/balsamo/test_hr_api_storage'
