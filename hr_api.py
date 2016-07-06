from flask import Flask
from flask import jsonify
from flask_restful import Resource, Api, reqparse
from uuid import uuid1
from os import scandir, remove
from os.path import join
from werkzeug.utils import secure_filename
from re import compile as regex_compile

from hierarchicalrecord.hierarchicalrecord import HierarchicalRecord
from hierarchicalrecord.recordconf import RecordConf
from hierarchicalrecord.recordvalidator import RecordValidator


# Globals
_ALPHANUM_PATTERN = regex_compile("^[a-zA-Z0-9]+$")
_NUMERIC_PATTERN = regex_compile("^[0-9]+$")
_STORAGE_ROOT = '/Users/balsamo/test_hr_api_storage'


# Most of these are abstracted because they should be hooked
# to some kind of database model in the future


def only_alphanumeric(x):
    if _ALPHANUM_PATTERN.match(x):
        return True
    return False


def retrieve_record(identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Record identifiers must be alphanumeric.")
    r = HierarchicalRecord(
        from_file=join(
            _STORAGE_ROOT, 'records', identifier
        )
    )
    return r


def write_record(record, identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Record identifiers must be alphanumeric.")
    with open(
        join(_STORAGE_ROOT, 'records', identifier), 'w'
    ) as f:
        f.write(record.toJSON())


def delete_record(identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Record identifiers must be alphanumeric.")
    rec_path = join(_STORAGE_ROOT, 'records', identifier)
    remove(rec_path)


def retrieve_conf(conf_str):
    conf_str = secure_filename(conf_str)
    c = RecordConf()
    if not only_alphanumeric(conf_str):
        raise ValueError("Conf identifiers must be alphanumeric.")
    c.from_csv(
        join(_STORAGE_ROOT, 'confs', conf_str+".csv")
    )
    return c


def delete_conf(identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Conf identifiers must be alphanumeric.")
    rec_path = join(_STORAGE_ROOT, 'confs', identifier+".csv")
    remove(rec_path)

def delete_category(identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Categories must be alphanumeric.")
    rec_path = join(_STORAGE_ROOT, 'org', identifier)
    remove(rec_path)

def build_validator(conf):
    return RecordValidator(conf)


def retrieve_validator(conf_id):
    c = retrieve_conf(conf_id)
    return build_validator(c)


def get_category(category):
    category = secure_filename(category)
    if not only_alphanumeric(category):
        raise ValueError("Category identifiers must be alphanumeric.")
    c = RecordCategory(category)
    p = join(_STORAGE_ROOT, 'org', category)
    try:
        with open(p, 'r') as f:
            for line in f.readlines():
                c.add_record(line.rstrip('\n'))
    except OSError:
        pass
    return c


def get_categories():
    r = []
    for x in scandir(join(_STORAGE_ROOT, 'org')):
        if not x.is_file():
            continue
        c = get_category(x.name)
        r.append(c)
    return r


def get_existing_record_identifiers():
    return (x.name for x in scandir(
        join(
            _STORAGE_ROOT, 'records'
        )) if x.is_file())


def get_existing_conf_identifiers():
    return (x.name for x in scandir(
        join(
            _STORAGE_ROOT, 'confs'
        )) if x.is_file())


def get_existing_categories():
    return (x.name for x in scandir(
        join(
            _STORAGE_ROOT, 'org'
        )) if x.is_file())


def parse_value(value):
    if value is "True":
        return True
    elif value is "False":
        return False
    elif value is "{}":
        return {}
    elif _NUMERIC_PATTERN.match(value):
        return int(value)
    else:
        return value


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

    def del_records(self):
        self._records = []

    def add_record(self, record_id):
        if record_id in get_existing_record_identifiers():
            self._records.append(record_id)
        else:
            raise ValueError("That identifier ({}) doesn't exist.".format(record_id))

    def remove_record(self, record_id, whiff_is_error=True):
        atleast_one = False
        for i, x in enumerate(self.records):
            if x == record_id:
                atleast_one = True
                del self.records[i]
        if not atleast_one and whiff_is_error:
            raise ValueError(
                "{} doesn't appear in the records list".format(record_id)
            )

    def serialize(self):
        # This next line shouldn't do anything,
        # and if it does things will break, but
        # security is security, I guess.
        t = secure_filename(self.title)
        outpath = join(_STORAGE_ROOT, 'org', t)
        self.records = set(self.records)
        with open(outpath, 'w') as f:
            for x in self.records:
                f.write(x+'\n')

    title = property(get_title, set_title)
    records = property(get_records, set_records, del_records)


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
            raise ValueError("errors must be an iterable of strings")

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
        All this information is out of date - but I'm leaving it in place
        so that in the future I remember to update it.

        #############

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


class RecordsRoot(Resource):
    def get(self):
        # List all records
        try:
            r = APIResponse(
                "success",
                data={"records": [x for x in get_existing_record_identifiers()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

# This function appears to be tricky because of nesting data structures in an
# iterable while still utilizing the RequestParser class. I'll have a look at it
# in the future.
#
#    def put(self):
#        # Bulk upload?
#        try:
#            parser = reqparse.RequestParser()
#            parser.add_argument('records', type=list)
#            args = parser.parse_args()
#            ids = []
#            if args.records:
#                for x in args.records:
#                    hr = HierarchicalRecord()
#                    hr.data = loads(x)
#                    identifier = uuid1().hex
#                    write_record(hr, identifier)
#                    ids.append({"identifier": identifier, "record": hr.data})
#            return jsonify(
#                APIResponse("success", data={"identifiers": ids}).dictify()
#            )
#        except Exception as e:
#            resp = APIResponse("fail",
#                               errors=[str(type(e)) + ":" + str(e)]
#                               )
#            return jsonify(resp.dictify())

    def post(self):
        # New Record
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record', type=dict)
            parser.add_argument('conf', type=str)
            args = parser.parse_args()
            identifier = uuid1().hex
            r = HierarchicalRecord()
            if args['record']:
                r.data = args['record']
            if args['conf']:
                validator = retrieve_validator(args['conf'])
                validity = validator.validate(r)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(r, identifier)
            resp = APIResponse("success",
                               data={"identifier": identifier,
                                     "record": r.data})
            return jsonify(resp.dictify())
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def delete(self):
        try:
            deleted = []
            for x in get_existing_record_identifiers():
                delete_record(x)
                deleted.append(x)
            return jsonify(
                APIResponse("success",
                            data={"deleted_identifiers": deleted}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())


class RecordRoot(Resource):
    def get(self, identifier):
        # Get the whole record
        try:
            r = retrieve_record(identifier)
            resp = APIResponse("success",
                               data={"record": r.data,
                                     "identifier": identifier})
            return jsonify(resp.dictify())
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def put(self, identifier):
        # overwrite a whole record
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record', type=dict, required=True)
            parser.add_argument('conf', type=str)
            args = parser.parse_args()
            record = retrieve_record(identifier)
            record.data = args.record
            if args['conf']:
                validator = retrieve_validator(args['conf'])
                validity = validator.validate(record)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(record, identifier)
            return jsonify(
                APIResponse("success",
                            data={'identifier': identifier,
                                  'record': record.data}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def delete(self, identifier):
        # delete a record
        try:
            delete_record(identifier)
            return jsonify(
                APIResponse(
                    "success", data={'identifier': identifier}
                ).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())


class EntryRoot(Resource):
    def get(self, identifier, key):
        try:
            r = retrieve_record(identifier)
            v = r[key]
            return jsonify(
                APIResponse("success", data={'value': v}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def post(self, identifier, key):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('value', required=True)
            parser.add_argument('conf', type=str)
            args = parser.parse_args()
            v = parse_value(args['value'])
            r = retrieve_record(identifier)
            r[key] = v
            if args['conf']:
                validator = retrieve_validator(args['conf'])
                validity = validator.validate(r)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(r, identifier)
            return jsonify(
                APIResponse("success",
                            data={'record': r.data,
                                  'identifier': identifier}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def delete(self, identifier, key):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('conf', type=str)
            args = parser.parse_args()
            r = retrieve_record(identifier)
            del r[key]
            if args['conf']:
                validator = retrieve_validator(args['conf'])
                validity = validator.validate(r)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(r, identifier)
            return jsonify(
                APIResponse("success",
                            data={'record': r.data,
                                  'identifier': identifier}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())


class ValidationRoot(Resource):
    def post(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record_identifier', type=str, required=True)
            parser.add_argument('conf_identifier', type=str, required=True)
            args = parser.parse_args(strict=True)

            v = retrieve_validator(args['conf_identifier'])
            r = retrieve_record(args['record_identifier'])
            validity = v.validate(r)
            resp = APIResponse("success",
                               data={"is_valid": validity[0],
                                     "validation_errors": validity[1],
                                     "identifier": args['record_identifier'],
                                     "conf": args['conf_identifier'],
                                     "record": r.data})
            return jsonify(resp.dictify())
        except Exception as e:
            resp = APIResponse("fail",
                               errors=[str(type(e)) + ":" + str(e)])
            return jsonify(resp.dictify())


class ConfsRoot(Resource):
    def get(self):
        # list all confs
        try:
            r = APIResponse(
                "success",
                data={"records": [x for x in get_existing_conf_identifiers()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

#    def put(self):
#        # bulk conf uplaod?
#        pass

#    def post(self):
#        # New Conf
#        pass

#    def delete(self):
#        # delete all the confs
#        pass


class ConfRoot(Resource):
    def get(self, identifier):
        # return a specific conf
        try:
            c = retrieve_conf(identifier)
            return jsonify(APIResponse("success", data={"identifier": identifier,"conf": c.data}).dictify())

        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

#    def put(self, identifier):
#        # overwrite a whole conf
#        pass

#    def post(self, identifier):
#        # set validation for a key that doesn't exist
#        pass

#    def delete(self, identifier):
#        # Delete this conf
#        pass


class CategoriesRoot(Resource):
    def get(self):
        # list all categories
        try:
            r = APIResponse(
                "success",
                data={"categories": [x for x in get_existing_categories()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

#    def put(self):
#        # overwrite all categories
#        pass

    def post(self):
        # Add a category
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('conf_id', type=str, required=True)
            parser.add_argument('records', type=list)
            args = parser.parse_args()

            if not only_alphanumeric(args['conf_id']):
                raise ValueError("Conf identifiers can only be alphanumeric.")

            # This line shouldn't do anything, but why not be paranoid about it
            args['conf_id'] = secure_filename(args['conf_id'])

            if args['conf_id'] in get_existing_categories():
                raise ValueError("That conf id already exists, " +
                                 "please specify a different identifier.")

            c = get_category(args['conf_id'])
            if args['records']:
                for x in args['records']:
                    c.add_record(x)
            c.serialize()

        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

#    def delete(self):
#        # delete all categories
#        pass

class CategoryRoot(Resource):
    def get(self, cat_identifier):
        # list all records in this category
        try:
            c = get_category(cat_identifier)
            return jsonify(
                APIResponse("success", data={"category": cat_identifier,
                                             "records": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def put(self, cat_identifier):
        # replace all records in this category
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('records', type=list, required=True)
            args = parser.parse_args()
            c = get_category(cat_identifier)
            del c.records
            for x in args['records']:
                c.add_record(x)
            c.serialize()
            return jsonify(
                APIResponse("success", data={"category": cat_identifier,
                                             "records": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def post(self, cat_identifier):
        # Add a record to this category
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record_identifier', type=str, required=True)
            args = parser.parse_args()

            c = get_category(cat_identifier)
            c.add_record(args['record_identifier'])
            c.serialize()

            return jsonify(
                APIResponse("success", data={"category": cat_identifier,
                                             "records": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

    def delete(self, cat_identifier):
        # delete this category
        try:
            delete_category(cat_identifier)
            return jsonify(
                APIResponse("success").dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())

class CategoryMember(Resource):
    def get(self, cat_identifier, rec_identifier):
        # Query the category to see if an identifier is in it
        try:
            c = get_category(cat_identifier)
            if rec_identifier in c.records:
                return jsonify(
                    APIResponse("success", data={"category": cat_identifier,
                                                 "records": c.records,
                                                 "record_present": True}).dictify()
                )
            else:
                raise ValueError("Record Identifier:{} not present in Category:{}".format(rec_identifier, cat_identifier))
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())


    def delete(self, cat_identifier, rec_identifier):
        #remove this member from the category
        try:
            c = get_category(cat_identifier)
            c.records = [x for x in c.records if x != rec_identifier]
            c.serialize()
            return jsonify(
                APIResponse("success", data={"category": cat_identifier,
                                             "records": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(APIResponse("fail", errors=[str(type(e)) + ":" + str(e)]).dictify())


app = Flask(__name__)
api = Api(app)
api.add_resource(Root, '/')
api.add_resource(RecordsRoot, '/record')
api.add_resource(RecordRoot, '/record/<string:identifier>')
api.add_resource(EntryRoot, '/record/<string:identifier>/<string:key>')
api.add_resource(ValidationRoot, '/validate')
api.add_resource(ConfsRoot, '/conf')
api.add_resource(ConfRoot, '/conf/<string:identifier>')
api.add_resource(CategoriesRoot, '/category')
api.add_resource(CategoryRoot, '/category/<string:cat_identifier>')
api.add_resource(CategoryMember, '/category/<string:cat_identifier>/<string:rec_identifier>')
