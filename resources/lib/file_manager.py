import os
import simplejson as json


class FileManager(object):

    def __init__(self, file_path, file_name='store.json', file_version=1):
        self.file_path = file_path
        self.file_name = file_name
        self.file_version = file_version
        self.__read_file()

    def __read_file(self):
        self.log('__read_file started')
        __file = os.path.join(self.file_path, self.file_name)
        if os.path.isfile(__file):
            try:
                f = json.load(open(__file, 'r'))
                if f.get('version') == self.file_version:
                    self.__file = f
                else:
                    self.log('__read_file in wrong version')
                    self.__recreate_file()
            except ValueError:
                self.log('__read_file could not read: "%s"' % __file)
                self.__recreate_file()
        else:
            self.log('__read_file file does not exist: "%s"' % __file)
            self.__recreate_file()
        self.log('__read_file finished')

    def __recreate_file(self):
        self.log('__recreate_file to version: %d' % self.file_version)
        self.__file = {
            'version': self.file_version,
            'content': {},
        }
        self.__write_file()

    def __write_file(self):
        self.log('__write_file started')
        if not os.path.isdir(self.file_path):
            os.makedirs(self.file_path)
        full_name = os.path.join(self.file_path, self.file_name)
        json.dump(self.__file, open(full_name, 'w'), indent=1)
        self.log('__write_file finished')

    def list_elements(self):
        self.log('list started')
        return self.__file['content']

    def add_element(self, element_id, content, sync=True):
        self.__file['content'][element_id] = content
        if sync:
            self.__write_file()

    def del_element(self, element_id, sync=True):
        try:
            del self.__file['content'][element_id]
        except KeyError:
            self.log('del_element failed')
            return False
        else:
            self.log('del_element succeeded')
            if sync:
                self.__write_file()
            return True

    def sync(self):
        self.__write_file()

    @staticmethod
    def log(msg):
        print msg
