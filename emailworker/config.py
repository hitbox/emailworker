import types

class Config(dict):
    """
    A clone of the Flask configuration object.
    """
    def from_pyfile(self, filename):
        """
        Pull UPPERCASE attributes from `filename` and store in self.

        :param filename: Path to `.py` file.
        :type filename: str or pathlib.Path
        """
        filename = str(filename)
        d = types.ModuleType('config')
        d.__file__ = filename
        with open(filename, 'rb') as config_file:
            exec(compile(config_file.read(), filename, 'exec'), d.__dict__)
        self.from_object(d)
        return True

    def from_object(self, obj):
        """
        Pull UPPERCASE attributes from `obj` and store in self.

        :type obj: object
        """
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)
