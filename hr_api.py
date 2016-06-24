from flask import Flask
from uuid import uuid1
from os.path import join

from hierarchicalrecord.hierarchicalrecord import HierarchicalRecord
from hierarchicalrecord.recordconf import RecordConf
from hierarchicalrecord.recordvalidator import RecordValidator

app = Flask(__name__)


def retrieve_record(identifier):
    r = HierarchicalRecord(from_file=join('/Users/balsamo/test_hr_api_storage', 'records', identifier))
    return r

def retrieve_conf(conf_str):
    c = RecordConf()
    c.from_csv(join('/Users/balsamo/test_hr_api_storage', 'confs', conf_str+".csv"))
    return c

def build_validator(conf):
    return RecordValidator(conf)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/newRecord')
def mint_record():
    identifier = uuid1().hex
    r = HierarchicalRecord()
    with open(join('/Users/balsamo/test_hr_api_storage', 'records', identifier), 'w') as f:
        f.write(r.toJSON())
    return identifier

@app.route('/getRecord/<string:identifier>')
def get_record(identifier):
    r = retrieve_record(identifier)
    return r.toJSON()

@app.route('/setValue/<string:identifier>/<string:key>/<string:value>')
@app.route('/setValue/<string:identifier>/<string:key>/<string:value>/<string:conf>')
def set_value(identifier, key, value, conf=None):
    if value == "True":
        value = True
    if value == "False":
        value = False
    if value == "{}":
        value = {}
    r = retrieve_record(identifier)
    if conf is not None:
        v = build_validator(retrieve_conf(conf))
        r[key] = value
        if v.validate(r)[0]:
            pass
        else:
            return "BAD NO"
    else:
        r[key] = value
    with open(join('/Users/balsamo/test_hr_api_storage', 'records', identifier), 'w') as f:
        f.write(r.toJSON())
    return r.toJSON()

@app.route('/delValue/<string:identifier>/<string:key>')
@app.route('/delValue/<string:identifier>/<string:key>/<string:conf>')
def remove_value(identifier, key, conf=None):
    r = retrieve_record(identifier)
    if conf is not None:
        v = build_validator(retrieve_conf(conf))
        del r[key]
        if v.validate(r)[0]:
            pass
        else:
            return "BAD NO"
    else:
        del r[key]
    with open(join('/Users/balsamo/test_hr_api_storage', 'records', identifier), 'w') as f:
        f.write(r.toJSON())
    return r.toJSON()

@app.route('/validate/<string:identifier>/<string:conf>')
def validate(identifier, conf):
    v = build_validator(retrieve_conf(conf))
    return str(v.validate(retrieve_record(identifier)))
    pass
