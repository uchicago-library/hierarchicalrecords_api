from flask import Flask
from flask import request
from flask import jsonify
from flask_restful import Resource, Api, reqparse
from uuid import uuid1
from os.path import join
from werkzeug.utils import secure_filename

from hierarchicalrecord.hierarchicalrecord import HierarchicalRecord
from hierarchicalrecord.recordconf import RecordConf
from hierarchicalrecord.recordvalidator import RecordValidator

app = Flask(__name__)
api = Api(app)


def retrieve_record(identifier):
    identifier = secure_filename(identifier)
    r = HierarchicalRecord(from_file=join('/Users/balsamo/test_hr_api_storage', 'records', identifier))
    return r

def retrieve_conf(conf_str):
    c = RecordConf()
    c.from_csv(join('/Users/balsamo/test_hr_api_storage', 'confs', conf_str+".csv"))
    return c

def build_validator(conf):
    return RecordValidator(conf)

class APIResponse(Object):

    _status = None
    _data = None
    _errors = None

    def __init__(self, status, data=None, errors=None):
        self.status = status
        self.data = None
        self.errors = None

    def get_status(self):
        return self._status

    def set_status(self, status):
        if status not in ['success', 'fail']:
            raise ValueError("status MUST be 'success' or 'fail'")
        self._status = status

    def get_data(self):
        return self._data

    def set_data(self, data):
        if not isinstance(data, dict) and data is not None:
            raise ValueError("Data must be a dict")
        self._data = data

    def get_errors(self):
        return self._errors

    def set_errors(self, errors):
        if errors == None:
            self._errors = None
            return
        try:
            for x in errors:
                self.add_error(x)
        except TypeError:
            raise ValueError("errors must be an iterable")

    def add_error(self, error):
        if not isinstance(error, str):
            raise ValueError("error must be a string")
        self._errors.append(error)

    errors = property(get_errors, set_errors)
    data = property(get_data, set_data)
    status = property(get_status, set_status)


class Root(Resource):
    def get(self):
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

class NewRecord(Resource):
    def get(self):
        identifier = uuid1().hex
        r = HierarchicalRecord()
        with open(join('/Users/balsamo/test_hr_api_storage', 'records', identifier), 'w') as f:
            f.write(r.toJSON())
        return identifier

    def post(self):
        return self.get()

class GetRecord(Resource):
    def get(self, identifier):
        r = retrieve_record(identifier)
        return jsonify(r.data)

class SetValue(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('identifier', type=str)
        parser.add_argument('key', type=str)
        parser.add_argument('value', type=str)
        parser.add_argument('conf', type=str)
        args = parser.parse_args(strict=True)
        identifier = args['identifier']
        key = args['key']
        value = args['value']
        try:
            conf = args['conf']
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
        return jsonify(r.data)

class RemoveValue(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('identifier', type=str)
        parser.add_argument('key', type=str)
        parser.add_argument('value', type=str)
        parser.add_argument('conf', type=str)
        args = parser.parse_args(strict=True)
        identifier = args['identifier']
        key = args['key']
        value = args['value']
        try:
            conf = args['conf']
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
        return jsonify(r.data)

class Validate(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('identifier', type=str)
        parser.add_argument('conf', type=str)
        args = parser.parse_args(strict=True)

        conf = args['conf']
        identifier = args['identifier']

        v = build_validator(retrieve_conf(conf))
        return str(v.validate(retrieve_record(identifier)))

class RetrieveValue(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('identifier', type=str)
        parser.add_argument('key', type=str)
        args = parser.parse_args(strict=True)

        r = retrieve_record(identifier)
        return r[args[key]]

api.add_resource(Root, '/')
api.add_resource(GetRecord, '/getRecord/<string:identifier>')
api.add_resource(SetValue, '/setValue')
api.add_resource(RemoveValue, '/delValue')
api.add_resource(Validate, '/validate')
api.add_resource(RetrieveValue, '/getValue')
