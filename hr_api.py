from flask import Flask
from flask import request
from flask import jsonify
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

@app.route('/', methods=['GET'])
def hello_world():
    if request.method == 'GET':
        docs = """
        This is the root of the HierarchicalRecords API Application.
        It has the following endpoints:

        GET
            - /getRecord

        POST
            - /newRecord
            - /setValue
            - /delValue
            - /validate
        """
        return docs

@app.route('/newRecord', methods=['POST'])
def mint_record():
    identifier = uuid1().hex
    r = HierarchicalRecord()
    with open(join('/Users/balsamo/test_hr_api_storage', 'records', identifier), 'w') as f:
        f.write(r.toJSON())
    return identifier

@app.route('/getRecord/<string:identifier>', methods=['GET'])
def get_record(identifier):
    r = retrieve_record(identifier)
    return r.toJSON()

@app.route('/setValue', methods=['POST'])
def set_value():
    j = request.get_json()
    identifier = j['identifier']
    key = j['key']
    value = j['value']
    try:
        conf = j['conf']
    except KeyError:
        conf = None

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

@app.route('/delValue')
def remove_value():
    j = request.get_json()

    identifier = j['identifier']
    key = j['key']
    value = j['value']
    try:
        conf = j['conf']
    except KeyError:
        conf = None

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

@app.route('/validate')
def validate(identifier, conf):
    j = request.get_json()

    identifier = j['identifier']
    conf = j['conf']

    v = build_validator(retrieve_conf(conf))
    return str(v.validate(retrieve_record(identifier)))
