from flask import Flask, jsonify, g, session, make_response
from flask_restful import Resource, Api, reqparse
from flask_login import LoginManager, login_required
from uuid import uuid1
from os import scandir, remove
from os.path import join
from werkzeug.utils import secure_filename
from re import compile as regex_compile
from hashlib import sha256
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired, \
    BadSignature
from json import loads as json_loads
from json import dumps as json_dumps
from os import urandom

from uchicagoldrapicore.responses.apiresponse import APIResponse
from uchicagoldrapicore.lib.apiexceptionhandler import APIExceptionHandler

from hierarchicalrecord.hierarchicalrecord import HierarchicalRecord
from hierarchicalrecord.recordconf import RecordConf
from hierarchicalrecord.recordvalidator import RecordValidator


from config import Config


# Globals
_ALPHANUM_PATTERN = regex_compile("^[a-zA-Z0-9]+$")
_NUMERIC_PATTERN = regex_compile("^[0-9]+$")
_EXCEPTION_HANDLER = APIExceptionHandler()

_SECRET_KEY = Config.secret_key
_STORAGE_ROOT = Config.storage_root


# Most of these are abstracted because they should be hooked
# to some kind of database model in the future
#
# TODO
# Probably make these base functions delegators to
# implementation specific functions


def only_alphanumeric(x):
    if _ALPHANUM_PATTERN.match(x):
        return True
    return False


def get_users():
    r = []
    for x in scandir(join(_STORAGE_ROOT, 'users')):
        if not x.is_file():
            continue
        r.append(x.name)
    return r


def retrieve_user_dict(identifier):
    if identifier != secure_filename(identifier):
        raise ValueError("Invalid User Identifier")
    try:
        r = None
        with open(join(_STORAGE_ROOT, 'users', identifier), 'r') as f:
            r = json_loads(f.read())
            return r
    except:
        raise ValueError("Invalid User Identifier")


def make_user_dict(identifier, password, clobber=False):
    if identifier != secure_filename(identifier):
        raise ValueError("Invalid id")
    if not clobber:
        if identifier in get_users():
            raise ValueError("That user already exists!")
    with open(join(_STORAGE_ROOT, 'users', identifier), 'w') as f:
        salt = str(urandom(32))
        f.write(
            json_dumps(
                {"id": identifier,
                 "password": User.hash_password(identifier, password, salt),
                 "salt": salt}
            )
        )


def write_user_dict(user, identifier):
    if not isinstance(user, User):
        raise ValueError("Must pass a user instance")
    if identifier != secure_filename(identifier):
        raise ValueError("Invalid user identifier")
    try:
        with open(join(_STORAGE_ROOT, 'users', identifier), 'w') as f:
            f.write(json_dumps(user.dictify()))
    except:
        raise ValueError("Bad user identifier")


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


def write_conf(conf, conf_id):
    conf_id = secure_filename(conf_id)
    if not only_alphanumeric(conf_id):
        raise ValueError("Conf identifiers must be alphanumeric.")
    path = join(_STORAGE_ROOT, 'confs', conf_id+".csv")
    conf.to_csv(path)


def delete_conf(identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Conf identifiers must be alphanumeric.")
    rec_path = join(_STORAGE_ROOT, 'confs', identifier+".csv")
    remove(rec_path)


def retrieve_category(category):
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


def write_category(c, identifier):
    identifier = secure_filename(identifier)
    if not only_alphanumeric(identifier):
        raise ValueError("Categories must be alphanumeric.")
    path = join(_STORAGE_ROOT, 'org', identifier)
    recs = set(c.records)
    with open(path, 'w') as f:
        for x in recs:
            f.write(x+'\n')


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


def get_categories():
    r = []
    for x in scandir(join(_STORAGE_ROOT, 'org')):
        if not x.is_file():
            continue
        c = retrieve_category(x.name)
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
    elif value is "[]":
        return []
    elif _NUMERIC_PATTERN.match(value):
        return int(value)
    else:
        return value


class User(object):
    def __init__(self, id_or_token, password=None):
        try:
            # token login
            validated = self.validate_token(id_or_token)
            id = validated['id']
            self.id = id
            try:
                user_dict = retrieve_user_dict(self.id)
            except:
                raise ValueError("Token implied bad user id")
            self.password = user_dict['password']
            self.is_authenticated = True
            self.is_active = True
            self.is_anonymous = False
        except (BadSignature, SignatureExpired):
            # password login
            self.id = id_or_token
            try:
                user_dict = retrieve_user_dict(self.id)
            except:
                raise ValueError("Bad Token / Bad ID")
            if self.hash_password(self.id, password, user_dict['salt']) !=  \
                    user_dict['password']:
                raise ValueError("Bad password")
            self.password = user_dict['password']
            self.salt = user_dict['salt']
            self.is_authenticated = True
            self.is_active = True
            self.is_anonymous = False

    def __repr__(self):
        return str(self.dictify())

    def get_id(self):
        return self.id

    def dictify(self):
        r = {}
        r['id'] = self.id
        r['password'] = self.password
        r['salt'] = self.salt
        return r

    def generate_token(self, expiration=60*60*24):
        s = TimedJSONWebSignatureSerializer(_SECRET_KEY, expires_in=expiration)
        x = s.dumps({'id': self.id}).decode("utf-8")
        return x

    @staticmethod
    def validate_token(token):
        s = TimedJSONWebSignatureSerializer(_SECRET_KEY)
        x = s.loads(token)
        return x

    @staticmethod
    def hash_password(id, password, salt):
        return sha256(
            "{}{}{}".format(id, password, salt).encode("utf-8")
        ).hexdigest()

    def verify_password(self, password):
        if self.hash_password(self.id, password, self.salt) == self.password:
            return True
        return False


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
            raise ValueError(
                "That identifier ({}) doesn't exist.".format(record_id)
            )

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

    title = property(get_title, set_title)
    records = property(get_records, set_records, del_records)


class Login(Resource):
    def get(self):
        # A handy dandy HTML interface for use in the browser
        return make_response("""<center>
                                <form action="#" method="post">
                                Username:<br>
                                <input type="text" name="user">
                                <br>
                                Password:<br>
                                <input type="password" name="password">
                                <br><br>
                                <input type="submit" value="Submit">
                                </form>
                             </center>""")

    def post(self):
        # Generate a token (valid for default token lifespan) and set it in the
        # session so that the user can stop passing credentials manually if they
        # want
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user', type=str, required=True,
                                location=['values', 'json', 'form'])
            parser.add_argument('password', type=str,
                                location=['values', 'json', 'form'])
            args = parser.parse_args()
            session['user_token'] = User(
                args['user'],
                password=args['password']
            ).generate_token()
            return jsonify(APIResponse("success").dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class Logout(Resource):

    method_decorators = [login_required]

    def get(self):
        # Pop the token out of the session if login generated one
        try:
            del session['user_token']
            return jsonify(
                APIResponse("success").dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class GetToken(Resource):

    method_decorators = [login_required]

    def get(self):
        # Generate a token for the user to use instead of their credentials
        try:
            t = g.user.generate_token()
            return jsonify(
                APIResponse("success", data={'token': t}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class UsersRoot(Resource):
    def get(self):
        try:
            return make_response("""<center>
                                    <form action="#" method="post">
                                    New Username:<br>
                                    <input type="text" name="new_user">
                                    <br>
                                    New User Password:<br>
                                    <input type="text" name="new_password">
                                    <br><br>
                                    <input type="submit" value="Submit">
                                    </form>
                                </center>""")
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self):
        # create a new user
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('new_user', type=str, required=True,
                                location=['values', 'json', 'form'])
            parser.add_argument('new_password', type=str, required=True,
                                location=['values', 'json', 'form'])
            args = parser.parse_args()
            make_user_dict(args['new_user'], args['new_password'])
            return jsonify(APIResponse("success").dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class UserRoot(Resource):

    method_decorators = [login_required]

    def get(self, identifier):
        # get a specific user record
        try:
            x = retrieve_user_dict(identifier)
            del x['password']
            del x['salt']
            return jsonify(APIResponse("success", data=x).dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, identifier):
        # remove a specific user
        pass


class Me(Resource):

    method_decorators = [login_required]

    def get(self):
        try:
            return UserRoot.get(self, g.user.get_id())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class RecordsRoot(Resource):
    def get(self):
        # List all records
        try:
            r = APIResponse(
                "success",
                data={"record_identifiers": [x for x in
                                             get_existing_record_identifiers()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self):
        # New Record
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record', type=dict)
            parser.add_argument('conf_identifier', type=str)
            args = parser.parse_args()
            identifier = uuid1().hex
            r = HierarchicalRecord()
            if args['record']:
                r.data = args['record']
            if args['conf_identifier']:
                validator = retrieve_validator(args['conf_identifier'])
                validity = validator.validate(r)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(r, identifier)
            resp = APIResponse("success",
                               data={"record_identifier": identifier,
                                     "record": r.data})
            return jsonify(resp.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class RecordRoot(Resource):
    def get(self, identifier):
        # Get the whole record
        try:
            r = retrieve_record(identifier)
            resp = APIResponse("success",
                               data={"record": r.data,
                                     "record_identifier": identifier})
            return jsonify(resp.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def put(self, identifier):
        # overwrite a whole record
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record', type=dict, required=True)
            parser.add_argument('conf_identifier', type=str)
            args = parser.parse_args()
            record = retrieve_record(identifier)
            record.data = args.record
            if args['conf_identifier']:
                validator = retrieve_validator(args['conf_identifier'])
                validity = validator.validate(record)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(record, identifier)
            return jsonify(
                APIResponse("success",
                            data={'record_identifier': identifier,
                                  'record': record.data}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, identifier):
        # delete a record
        try:
            delete_record(identifier)
            r = APIResponse(
                "success",
                data={"records": [x for x in get_existing_record_identifiers()],
                      "deleted_identifier": identifier}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class EntryRoot(Resource):
    def get(self, identifier, key):
        # get a value
        try:
            r = retrieve_record(identifier)
            v = r[key]
            return jsonify(
                APIResponse(
                    "success",
                    data={'record_identifier': identifier,
                          'key': key, 'value': v}
                ).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self, identifier, key):
        # Set a value
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('value', required=True)
            parser.add_argument('conf_identifier', type=str)
            args = parser.parse_args()
            v = parse_value(args['value'])
            r = retrieve_record(identifier)
            r[key] = v
            if args['conf_identifier']:
                validator = retrieve_validator(args['conf_identifier'])
                validity = validator.validate(r)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(r, identifier)
            return jsonify(
                APIResponse("success",
                            data={'record': r.data,
                                  'record_identifier': identifier}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, identifier, key):
        # delete a value
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('conf_identifier', type=str)
            args = parser.parse_args()
            r = retrieve_record(identifier)
            del r[key]
            if args['conf_identifier']:
                validator = retrieve_validator(args['conf_identifier'])
                validity = validator.validate(r)
                if not validity[0]:
                    return jsonify(
                        APIResponse("fail", errors=validity[1]).dictify()
                    )
            write_record(r, identifier)
            return jsonify(
                APIResponse("success",
                            data={'record': r.data,
                                  'record_identifier': identifier}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


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
                               data={
                                   "is_valid": validity[0],
                                   "validation_errors": validity[1],
                                   "record_identifier": args['record_identifier'],
                                   "conf_identifier": args['conf_identifier'],
                                   "record": r.data
                                   }
                               )
            return jsonify(resp.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class ConfsRoot(Resource):
    def get(self):
        # list all confs
        try:
            r = APIResponse(
                "success",
                data={"conf_identifiers": [x for x in
                                           get_existing_conf_identifiers()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self):
        # New Conf
        try:
            new_conf_identifier = uuid1().hex
            c = RecordConf()
            write_conf(c, new_conf_identifier)
            r = APIResponse(
                "success",
                data={"conf_identifier": new_conf_identifier,
                      "conf": c.data}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class ConfRoot(Resource):
    def get(self, identifier):
        # return a specific conf
        try:
            c = retrieve_conf(identifier)
            return jsonify(
                APIResponse("success",
                            data={"conf_identifier": identifier,
                                  "conf": c.data}
                            ).dictify()
            )

        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self, identifier):
        # set validation rule
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('rule', type=dict, required=True)
            args = parser.parse_args()
            c = retrieve_conf(identifier)
            c.add_rule(args['rule'])
            write_conf(c, identifier)
            return jsonify(
                APIResponse("success",
                            data={"conf_identifier": identifier,
                                  "conf": c.data}
                            ).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, identifier):
        # Delete this conf
        try:
            delete_conf(identifier)
            r = APIResponse(
                "success",
                data={"conf_identifiers": [x for x in
                                           get_existing_conf_identifiers()],
                      "deleted_conf_identifier": identifier}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class RulesRoot(Resource):
    def get(self, identifier, rule_id):
        # get a rule
        try:
            c = retrieve_conf(identifier)
            found_one = False
            for x in c.data:
                if x['id'] == rule_id:
                    rule = x
                    found_one = True
            if not found_one:
                raise ValueError(
                    "No rule with id {} in conf {}".format(rule_id, identifier)
                )
            r = APIResponse(
                "success",
                data={"conf_identifier": identifier,
                      "rule": rule}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, identifier, rule_id):
        # delete a rule
        try:
            c = retrieve_conf(identifier)
            c.data = [x for x in c.data if x['id'] != rule_id]
            write_conf(c, identifier)
            return jsonify(
                APIResponse("success", data={"conf_identifier": identifier,
                                             "conf": c.data}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class RuleComponentRoot(Resource):
    def get(self, identifier, rule_id, component):
        # get a rule component
        try:
            c = retrieve_conf(identifier)
            rule = None
            for x in c.data:
                if x['id'] == rule_id:
                    rule = x
            if rule is None:
                raise ValueError(
                    "No rule with id {} in conf {}".format(rule_id, identifier)
                )
            try:
                value = x[component]
            except KeyError:
                raise ValueError(
                    "No component named {} in rule {} in conf {}".format(component,
                                                                         rule_id,
                                                                         identifier)
                )
            return jsonify(
                APIResponse("success", data={"conf_identifier": identifier,
                                             "rule_id": rule_id,
                                             "component": component,
                                             "value": value}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, identifier, rule_id, component):
        # remove a rule component
        try:
            c = retrieve_conf(identifier)
            rule = None
            for x in c.data:
                if x['id'] == rule_id:
                    rule = x
            if rule is None:
                raise ValueError(
                    "No rule with id {} in conf {}".format(rule_id, identifier)
                )
            try:
                x[component] = ""
                value = x[component]
            except KeyError:
                raise ValueError(
                    "No component named {} in rule {} in conf {}".format(component,
                                                                         rule_id,
                                                                         identifier)
                )
            write_conf(c, identifier)
            return jsonify(
                APIResponse("success", data={"conf_identifier": identifier,
                                             "rule_id": rule_id,
                                             "component": component,
                                             "value": value}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())
        pass

    def post(self, identifier, rule_id, component):
        # Add a rule component to this rule
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('component_value', type=str, required=True)
            args = parser.parse_args()

            c = retrieve_conf(identifier)
            rule = None
            for x in c.data:
                if x['id'] == rule_id:
                    rule = x
            if rule is None:
                raise ValueError(
                    "No rule with id {} in conf {}".format(rule_id, identifier)
                )
            try:
                x[component] = args['component_value']
                value = x[component]
            except KeyError:
                raise ValueError(
                    "No component named {} in rule {} in conf {}".format(component,
                                                                         rule_id,
                                                                         identifier)
                )
            write_conf(c, identifier)
            return jsonify(
                APIResponse("success", data={"conf_identifier": identifier,
                                             "rule_id": rule_id,
                                             "component": component,
                                             "value": value}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class CategoriesRoot(Resource):
    def get(self):
        # list all categories
        try:
            r = APIResponse(
                "success",
                data={"category_identifiers": [x for x in
                                               get_existing_categories()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self):
        # Add a category
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('category_identifier', type=str, required=True)
            args = parser.parse_args()

            if not only_alphanumeric(args['category_identifier']):
                raise ValueError(
                    "Category identifiers can only be alphanumeric."
                )

            # This line shouldn't do anything, but why not be paranoid about it
            args['category_identifier'] = secure_filename(
                args['category_identifier']
            )

            if args['category_identifier'] in get_existing_categories():
                raise ValueError("That cat id already exists, " +
                                 "please specify a different identifier.")

            c = retrieve_category(args['category_identifier'])
            write_category(c, args['category_identifier'])
            return jsonify(
                APIResponse(
                    "success",
                    data={"category_identifier": args['category_identifier'],
                          "record_identifiers": c.records}
                ).dictify()
            )

        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class CategoryRoot(Resource):
    def get(self, cat_identifier):
        # list all records in this category
        try:
            c = retrieve_category(cat_identifier)
            return jsonify(
                APIResponse("success",
                            data={"category_identifier": cat_identifier,
                                  "record_identifiers": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def post(self, cat_identifier):
        # Add a record to this category
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('record_identifier', type=str, required=True)
            args = parser.parse_args()

            c = retrieve_category(cat_identifier)
            c.add_record(args['record_identifier'])
            write_category(c, cat_identifier)
            return jsonify(
                APIResponse("success",
                            data={"category_identifier": cat_identifier,
                                  "record_identifiers": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, cat_identifier):
        # delete this category
        try:
            delete_category(cat_identifier)
            r = APIResponse(
                "success",
                data={"category_identifiers": [x for x in
                                               get_existing_categories()]}
            )
            return jsonify(r.dictify())
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


class CategoryMember(Resource):
    def get(self, cat_identifier, rec_identifier):
        # Query the category to see if an identifier is in it
        try:
            c = retrieve_category(cat_identifier)
            if rec_identifier in c.records:
                return jsonify(
                    APIResponse("success",
                                data={"category_identifier": cat_identifier,
                                      "record_identifiers": c.records,
                                      "record_present": True}).dictify()
                )
            else:
                raise ValueError(
                    "Record Identifier: {} not present in Category: {}".format(rec_identifier,
                                                                               cat_identifier)
                )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())

    def delete(self, cat_identifier, rec_identifier):
        # remove this member from the category
        try:
            c = retrieve_category(cat_identifier)
            c.records = [x for x in c.records if x != rec_identifier]
            write_category(c, cat_identifier)
            return jsonify(
                APIResponse("success",
                            data={"category_identifier": cat_identifier,
                                  "record_identifiers": c.records}).dictify()
            )
        except Exception as e:
            return jsonify(_EXCEPTION_HANDLER.handle(e).dictify())


# Create our app, hook the API to it, and add our resources
app = Flask(__name__)

# Set our secret key so we can use sessions.
# This value comes from the config

app.secret_key = _SECRET_KEY

# Tell people everything they did wrong, instead of just the first instance of
# what they did wrong when posting a request through the request parser
# interface

app.config['BUNDLE_ERRORS'] = True

# Define the login manager for flask-login for authenticated endpoints

login_manager = LoginManager()


@login_manager.request_loader
def load_user(request):
    # Try really hard to get the user out of where ever it could be
    # First look in the URL args
    user, password = request.args.get('user'), request.args.get('password')
    # Then look in the JSON args
    if user is None:
        if request.get_json():
            user, password = request.get_json().get('user'),  \
                request.get_json().get('password')
    # Then look in the session
    if user is None:
        if session.get('user_token'):
            user = session.get('user_token')
    if user is not None:
        try:
            g.user = User(user, password)
            return g.user
        except:
            return None
    return None

login_manager.init_app(app)

api = Api(app)

# Login and Logout
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')

# User endpoints
api.add_resource(UsersRoot, '/users')
api.add_resource(UserRoot, '/users/<string:identifier>')
api.add_resource(Me, '/users/me')

# Record manipulation endpoints
api.add_resource(RecordsRoot, '/record')
api.add_resource(RecordRoot, '/record/<string:identifier>')
api.add_resource(EntryRoot, '/record/<string:identifier>/<string:key>')

# Validation endpoint
api.add_resource(ValidationRoot, '/validate')

# Conf manipulation endpoints
api.add_resource(ConfsRoot, '/conf')
api.add_resource(ConfRoot, '/conf/<string:identifier>')
api.add_resource(RulesRoot, '/conf/<string:identifier>/<string:rule_id>')
api.add_resource(RuleComponentRoot, '/conf/<string:identifier>/<string:rule_id>/<string:component>')

# Organization manipulation endpoints
api.add_resource(CategoriesRoot, '/category')
api.add_resource(CategoryRoot, '/category/<string:cat_identifier>')
api.add_resource(CategoryMember, '/category/<string:cat_identifier>/<string:rec_identifier>')

# Token endpoint
api.add_resource(GetToken, '/token')
