from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
import mysql.connector
import subprocess
import hashlib
import base64


# best source: https://www.freecodecamp.org/news/connect-python-with-sql/
# add sql injection protection

# PODMAN
# https://hub.docker.com/_/mysql
# https://www.redhat.com/sysadmin/specify-architecture-pulling-podman-images
# podman run -it --name login_db -e MYSQL_ROOT_PASSWORD=admin -d docker.io/mysql:latest
# docker run -it --name login_db -e MYSQL_ROOT_PASSWORD=admin -d mysql:latest

def generate_fernet_key(text):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'safest storage!',
        iterations=100000,
        backend=default_backend()
    )

    text = text.encode()
    key = kdf.derive(text)
    key = base64.b64encode(key)
    return Fernet(key)


def encrypt_str(fern, text):
    if isinstance(text, str):
        text = text.encode()
    return fern.encrypt(text)


def decrypt_str(fern, text):
    if isinstance(text, str):
        text = text.encode()
    decrypted = fern.decrypt(text)
    return decrypted.decode()


def alpha_hash(hash_text):
    hashed = base64.b32encode(hash_text)
    hashed = hashed.decode('ascii').rstrip('=')
    return hashed.lower()


def hash_text(text):
    salt = 'iRmh94OX5H'
    salt = salt.encode()
    salted_text = salt + text.encode()
    hashed = hashlib.sha256(salted_text).digest()
    return alpha_hash(hashed)


def list_tables(cursor):
    cursor.execute(f'SHOW TABLES;')
    tables_it = cursor.fetchall()
    tables = [table[0] for table in tables_it]
    return tables


# might have to change host to 172.17.0.2 if there is a port
def connect_to_db(db_name, port=None):
    params = {'user': 'root', 'host': 'localhost', 'database': db_name}
    if port != None:
        params['port'] = port
        if 0:
            connection = mysql.connector.connect(
                user='root',
                host='localhost',
                port=port,
                database=db_name
            )
    connection = mysql.connector.connect(**params)
    cursor = connection.cursor()
    return connection, cursor


def compare_arrs(arr1, arr2):
    if len(arr1) != len(arr2):
        return False

    try:
        for item1, item2 in zip(arr1, arr2):
            if item1 != item2:
                return False
        return True
    except:
        return False


class Table:
    __LOGIN_TEST = 'Successfully Logged In!'
    field_idxs = {'id': 0, 'name': 1, 'url': 2, 'description': 3, 'usr': 4, 'pssd': 5}

    def encrypted(self, text):
        if text:
            return encrypt_str(self.fern, text).decode()
        else:
            return ''

    def decrypted(self, text):
        if text:
            return decrypt_str(self.fern, text)
        else:
            return ''

    def decrypt_row(self, row):
        decrypt = [row[0]]
        for item in row[1:]:
            decrypt.append(self.decrypted(item))
        return decrypt

    def general_search(self, sql_query, raw=False):
        self.__cursor.execute(sql_query)
        entries = self.__cursor.fetchall()
        if not raw:
            entries = [self.decrypt_row(entry) for entry in entries]
        return entries

    def get_entries(self, raw=False, include_test=False):
        start = 1
        if include_test:
            start = 0
        return self.general_search(f'SELECT * FROM {self.__usr_hash}', raw=raw)[start:]

    def table_search(self, query, raw=False):
        return self.general_search(f"SELECT * FROM {self.__usr_hash} WHERE {query};", raw=raw)

    def get_row(self, id):
        row = self.table_search(f'id = {id}', raw=True)
        if row:
            row = row[0]
        return row

    def add_entry(self, pssd, name='', url='', description='', usr=''):
        values = (name, url, description, usr, pssd)

        for entry in self.get_entries():
            if compare_arrs(values, entry[1:]):
                return False
        values = (self.encrypted(value) for value in values)

        name, url, description, usr, pssd = values
        sql = f"INSERT INTO {self.__usr_hash} (name, url, description, usr, pssd) VALUES ('{name}', '{url}', '{description}', '{usr}', '{pssd}');"
        self.__cursor.execute(sql)
        self.__connection.commit()

        return True

    def __create_table(self):
        self.__cursor.execute(
            f'CREATE TABLE {self.__usr_hash} ( id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), url VARCHAR(255), description VARCHAR(255), usr VARCHAR(255), pssd VARCHAR(255) NOT NULL );')
        self.__connection.commit()

        self.add_entry(name=self.__usr_hash, pssd=self.__LOGIN_TEST)
        # add base case for logging in

    def __table_exists(self):
        tables = list_tables(self.__cursor)
        return self.__usr_hash in tables

    def login(self):
        row = self.get_row(1)
        print(row)
        if row is None:
            return False

        decrypt = decrypt_str(self.fern, row[5])
        print(decrypt)
        if decrypt == self.__LOGIN_TEST:
            return True
        return False

    def __init__(self, db_name, usr, pssd, port=None):
        self.__db_name = db_name
        self.port = port
        self.__usr_hash = hash_text(usr)
        self.fern = generate_fernet_key(pssd)
        self.__connection, self.__cursor = connect_to_db(self.__db_name, port=self.port)

        # creating table
        if self.__table_exists():
            if not self.login():
                raise Exception('Could Not Log In')
        else:
            self.__create_table()

    def __del__(self):
        self.__cursor.close()
        self.__connection.close()

    def query(self, ID=None, url=None, name=None, description=None, usr=None, pssd=None):
        entries = self.get_entries()
        entry_vals = {'id': ID, 'url': url, 'name': name, 'description': description, 'usr': usr, 'pssd': pssd}
        entry_vals = {key: value for key, value in entry_vals.items() if value is not None}

        results = []
        for entry in entries:
            add = True
            for key, value in entry_vals.items():
                if entry[self.field_idxs[key]] != value:
                    add = False
                    break
            if add:
                results.append(entry)

        return results

    def delete(self, ID=None, url=None, name=None, description=None, usr=None, pssd=None):
        results = self.query(ID=ID, url=url, name=name, description=description, usr=usr, pssd=pssd)

        sql = f'DELETE FROM {self.__usr_hash} WHERE id IN (%s);'
        values = [(result[0],) for result in results]
        values = [value for value in values if value[0] != 1]

        self.__cursor.executemany(sql, values)
        self.__connection.commit()

    def edit(self, ID=None, url=None, name=None, description=None, usr=None, pssd=None,
             new_url=None, new_name=None, new_description=None, new_usr=None, new_pssd=None):
        results = self.query(ID=ID, url=url, name=name, description=description, usr=usr, pssd=pssd)
        if len(results) != 1:
            return False
        entry = {'url': new_url, 'name': new_name, 'description': new_description,
                 'usr': new_usr, 'pssd': new_pssd}
        entry = {key: value for key, value in entry.items() if value != None}
        sql = 'UPDATE {self.__usr_hash} SET '
        for key, value in entry.items():
            sql += f"{key} = '{value}', "
        sql = sql[:-2] + f' WHERE id = {results[0][0]}'
        self.__cursor.execute(sql)
        self.__connection.commit()
        return True


class LoginDB:
    def connect_to_db(self, db_name):
        self.__cursor, self.__connection = connect_to_db(db_name, port=self.port)

    def __init__(self, db_name, admin_usr, admin_pssd, port=None):
        self.db_name = db_name
        self.port = port
        try:
            self.connect_to_db(db_name)
        except mysql.connector.errors.ProgrammingError as e:
            if 'Unknown database' in str(e):
                connection = mysql.connector.connect(
                    user='root',
                    host='localhost'
                )
                cursor = connection.cursor()
                cursor.execute(f'CREATE DATABASE {db_name}')
                connection.close()

                self.connect_to_db(db_name)
            else:
                raise e

        self.__admin_usr = admin_usr
        self.__admin_pssd = admin_pssd

    def __del__(self):
        self.__connection.close()
        self.__cursor.close()

    def login(self, usr, pssd):
        return Table(self.db_name, usr, pssd, port=self.port)

    def list_usr_hashes(self):
        return list_tables(self.__cursor)

# connection = psycopg2.connect(user="postgres", password="pynative@#29", host="127.0.0.1", port="5432", database="passwords")
# cursor = connection.cursor()
