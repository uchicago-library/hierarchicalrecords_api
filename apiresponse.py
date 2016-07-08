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
