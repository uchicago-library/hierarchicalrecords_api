from flask import Flask
from flask import jsonify
from flask_restful import Resource, Api, reqparse
from uuid import uuid1
from os import scandir
from os.path import join
from werkzeug.utils import secure_filename
from re import compile as regex_compile

from hierarchicalrecord.hierarchicalrecord import HierarchicalRecord
from hierarchicalrecord.recordconf import RecordConf
from hierarchicalrecord.recordvalidator import RecordValidator

_ALPHANUM_PATTERN = regex_compile("^[a-zA-Z0-9]+$")

def only_alphanumeric(x):
    if _ALPHANUM_PATTERN.match(x):
        return True
    return False


def retrieve_record(identifier):
    identifier = secure_filename(identifier)
    r = HierarchicalRecord(
        from_file=join(
            '/Users/balsamo/test_hr_api_storage', 'records', identifier
        )
    )
    return r


def write_record(record, identifier):
    identifier = secure_filename(identifier)
    with open(
        join('/Users/balsamo/test_hr_api_storage', 'records', identifier), 'w'
    ) as f:
        f.write(record.toJSON())


def retrieve_conf(conf_str):
    c = RecordConf()
    c.from_csv(
        join('/Users/balsamo/test_hr_api_storage', 'confs', conf_str+".csv")
    )
    return c


def build_validator(conf):
    return RecordValidator(conf)


def get_category(category):
    c = RecordCategory(category)
    p = join('/Users/balsamo/test_hr_api_storage', 'org', category)
    try:
        with open(p, 'r') as f:
            for line in f.readlines():
                c.add_record(line.rstrip('\n'))
    except FileNotFoundError:
        pass
    return c

def get_existing_record_identifiers():
    return (x.name for x in scandir(
        join(
            '/Users/balsamo/test_hr_api_storage', 'records'
        )) if x.is_file())


class RecordCategory(object):
    def __init__(self, title):
        self._title = None
        self._records = []
        self.title = title

    def get_title(self):
        return self._title

    def set_title(self, title):
        if not only_alphanumeric(title):
            raise ValueError("Category titles can only be alphanumeric")
        self._title = title

    def get_records(self):
        return self._records

    def set_records(self, record_ids):
        self._records = []
        for x in record_ids:
            self.add_record(x)

    def add_record(self, record_id):
        if record_id in get_existing_record_identifiers():
            self._records.append(record_id)
        else:
            raise ValueError("That identifier doesn't exist.")

    def remove_record(self, record_id, whiff_is_error=True):
        atleast_one = False
        for i, x in enumerate(self.records):
            if x == record_id:
                atleast_one = True
                del self.records[i]
        if not atleast_one and whiff_is_error:
            raise ValueError("{} doesn't appear in the records list".format(record_id))

    def serialize(self):
        outpath = join('/Users/balsamo/test_hr_api_storage', 'org', self.title)
        self.records = set(self.records)
        with open(outpath, 'w') as f:
            for x in self.records:
                f.write(x+'\n')


    title = property(get_title, set_title)
    records = property(get_records, set_records)


class APIResponse(object):

    _status = None
    _data = None
    _errors = None

    def __init__(self, status, data=None, errors=None):
        self.status = status
        self.data = data
        self.errors = errors

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
        if errors is None:
            self._errors = None
            return
        try:
            self._errors = []
            for x in errors:
                self.add_error(x)
        except TypeError:
            raise ValueError("errors must be an iterable")

    def add_error(self, error):
        if not isinstance(error, str):
            raise ValueError("error must be a string")
        self._errors.append(error)

    def dictify(self):
        r = {}
        r['status'] = self.status
        r['data'] = self.data
        r['errors'] = self.errors
        return r

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
        try:
            identifier = uuid1().hex
            r = HierarchicalRecord()
            write_record(r, identifier)
            resp = APIResponse("success",
                               data={"identifier": identifier})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)]
                               )
            return jsonify(resp.dictify())


class GetRecord(Resource):
    def get(self, identifier):
        try:
            if not only_alphanumeric(identifier):
                raise ValueError("Identifiers may only be alpha-numeric")
            r = retrieve_record(identifier)
            resp = APIResponse("success",
                               data={"record": r.data,
                                     "identifier": identifier})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)]
                               )
            return jsonify(resp.dictify())


class SetValue(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('identifier', type=str, required=True)
            parser.add_argument('key', type=str, required=True)
            parser.add_argument('value', type=str, required=True)
            parser.add_argument('conf', type=str)
            args = parser.parse_args()
            identifier = args['identifier']
            if not only_alphanumeric(identifier):
                raise ValueError("Identifiers may only be alpha-numeric")
            key = args['key']
            value = args['value']
            try:
                conf = args['conf']
                if not only_alphanumeric(conf):
                    raise ValueError("Configs may only be alpha-meric")
            except KeyError:
                conf = None
            if value == "True":
                value = True
            if value == "False":
                value = False
            if value == "{}":
                value = {}
            print(identifier)
            r = retrieve_record(identifier)
            if conf is not None:
                v = build_validator(retrieve_conf(conf))
                r[key] = value
                validity = v.validate(r)
                if validity[0]:
                    pass
                else:
                    resp = APIResponse("fail",
                                       errors=validity[1])
                    return jsonify(resp.dictify())
            else:
                r[key] = value
            write_record(r, identifier)
            resp = APIResponse("success",
                               data={"record": r.data,
                                     "identifier": identifier,
                                     "conf": conf})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())


class RemoveValue(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('identifier', type=str)
            parser.add_argument('key', type=str)
            parser.add_argument('value', type=str)
            parser.add_argument('conf', type=str)
            args = parser.parse_args(strict=True)
            identifier = args['identifier']
            if not only_alphanumeric(identifier):
                raise ValueError("Identifiers may only be alpha-numeric")
            key = args['key']
            try:
                conf = args['conf']
                if not only_alphanumeric(conf):
                    raise ValueError("Configs may only be alpha-meric")
            except KeyError:
                conf = None
            r = retrieve_record(identifier)
            if conf is not None:
                v = build_validator(retrieve_conf(conf))
                try:
                    del r[key]
                except KeyError:
                    resp = APIResponse("fail",
                                       errors=['Key Error: {}'.format(key)])
                    return jsonify(resp.dictify())
                validity = v.validate(r)
                if validity[0]:
                    pass
                else:
                    resp = APIResponse("fail",
                                       errors=validity[1])
                    return jsonify(resp.dictify())
            else:
                try:
                    del r[key]
                except KeyError:
                    resp = APIResponse("fail",
                                       errors=['Key Error: {}'.format(key)])
                    return jsonify(resp.dictify())
            write_record(r, identifier)
            resp = APIResponse("success",
                               data={"record": r.data,
                                     "identifier": identifier,
                                     "conf": conf})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())


class Validate(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('identifier', type=str)
            parser.add_argument('conf', type=str, required=True)
            args = parser.parse_args(strict=True)

            conf = args['conf']
            if not only_alphanumeric(conf):
                raise ValueError("Identifiers may only be alpha-numeric")
            identifier = args['identifier']
            if not only_alphanumeric(identifier):
                raise ValueError("Identifiers may only be alpha-numeric")

            v = build_validator(retrieve_conf(conf))
            validity = v.validate(retrieve_record(identifier))
            resp = APIResponse("success",
                               data={"is_valid": validity[0],
                                     "validation_errors": validity[1],
                                     "identifier": identifier,
                                     "conf": conf})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())


class RetrieveValue(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('identifier', type=str)
            parser.add_argument('key', type=str)
            args = parser.parse_args(strict=True)

            if not only_alphanumeric(args['identifier']):
                raise ValueError("Identifiers may only be alpha-numeric")

            r = retrieve_record(args['identifier'])
            try:
                val = r[args["key"]]
            except KeyError:
                resp = APIResponse("fail",
                                   errors=['Key Error: {}'.format(args["key"])])
                return jsonify(resp.dictify())
            resp = APIResponse("success", data={"value": val,
                                                "identifier": args['identifier'],
                                                "key": args["key"]})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())


class AssociateRecord(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('identifier', type=str)
            parser.add_argument('category', type=str)

            args = parser.parse_args(strict=True)

            if not only_alphanumeric(args['identifier']):
                raise ValueError("Identifiers may only be alpha-numeric.")

            if not only_alphanumeric(args['category']):
                raise ValueError("Categories may only be alpha-numeric.")

            if args['identifier'] not in get_existing_record_identifiers():
                raise ValueError("That identifier doesn't exist.")

            category = get_category(args["category"])
            category.add_record(args['identifier'])
            category.serialize()

            resp = APIResponse("success",
                               data={"identifier": args['identifier'],
                                     "category": args['category']})
            return jsonify(resp.dictify())

        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())


class DisassociateRecord(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('identifier', type=str)
            parser.add_argument('category', type=str)

            args = parser.parse_args(strict=True)

            if not only_alphanumeric(args['identifier']):
                raise ValueError("Identifiers may only be alpha-numeric.")

            if not only_alphanumeric(args['category']):
                raise ValueError("Categories may only be alpha-numeric.")

            category = get_category(args["category"])
            category.remove_record(args['identifier'])
            category.serialize()

            resp = APIResponse("success",
                               data={"identifier": args['identifier'],
                                     "category": args['category']})
            return jsonify(resp.dictify())

        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())


class ListCategory(Resource):
    def get(self, category):
        try:
            if not only_alphanumeric(category):
                raise ValueError("Categories have to be alpha-numeric.")

            c = get_category(category)
            data = {"category":category,
                    "records": c.records}
            resp = APIResponse("success", data=data)
            return jsonify(resp.dictify())

        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(e)])
            return jsonify(resp.dictify())



app = Flask(__name__)
api = Api(app)
api.add_resource(Root, '/')
api.add_resource(NewRecord, '/newRecord')
api.add_resource(GetRecord, '/getRecord/<string:identifier>')
api.add_resource(SetValue, '/setValue')
api.add_resource(RemoveValue, '/delValue')
api.add_resource(Validate, '/validate')
api.add_resource(RetrieveValue, '/getValue')
api.add_resource(AssociateRecord, '/associateRecord')
api.add_resource(DisassociateRecord, '/disassociateRecord')
api.add_resource(ListCategory, '/listCategory/<string:category>')
