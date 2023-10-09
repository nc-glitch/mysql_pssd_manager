import cryptography
import login_db as DB
import sys

if len(sys.argv) < 3:
    raise Exception('Not enough cmd line arguments.')
elif len(sys.argv) > 4:
    raise Exception('Too many cmd line arguments.')

db_name = sys.argv[1]
admin_usr = sys.argv[2]
admin_pssd = ''
if len(sys.argv) == 4:
    admin_pssd = sys.argv[3]
db = DB.login(db_name, admin_usr, admin_pssd)

while True:
    usr = input('Enter usr?')
    pssd = input('Enter pssd?')
    try:
        table = db.login(usr, pssd)
        print('Successfully Logged in.')
        break
    except cryptography.fernet.InvalidToken:
        print('Incorrect Login Information. Try again')

while True:
    inp = input()
    try:
        cmd = inp.split()
        if cmd[0] == 'search':
            print(table.general_search(cmd[1]))
        elif cmd[0] == 'entries':
            print(table.get_entries())
        elif cmd[0] == 'add':
            entries = {'usr': '', 'pssd': '', 'name': '', 'url': '', 'description': ''}
            for arg in cmd[1:]:
                parts = arg.split('=')
                if len(parts) != 2:
                    raise Exception('Incorrectly formatted flags')
                if parts[0] in entries:
                    entries[parts[0]] = parts[1]
            if entries[pssd] == '':
                raise Exception('No passwod was entered')
            entry_pssd = entries[pssd]
            entries = { key: value for key, value in entries.items() if key != pssd }
            table.add_entry(entry_pssd, entries)
        elif cmd[0] == 'delete':
            entries = { 'ID': None, 'url': None, 'name': None, 'description': None, 'usr': None, 'pssd': None }
            for arg in cmd[1:]:
                parts = arg.split('=')
                if len(parts) != 2:
                    raise Exception('Incorrectly formatted flags')
                if parts[0] in entries:
                    entries[parts[0]] = parts[1]
            table.delete(**entries)
        elif cmd[0] == 'edit':
            entries = { 'ID': None, 'url': None, 'name': None, 'description': None, 'usr': None, 'pssd': None,
             'new_url': None, 'new_name': None, 'new_description': None, 'new_usr': None, 'new_pssd': None }
            for arg in cmd[1:]:
                parts = arg.split('=')
                if len(parts) != 2:
                    raise Exception('Incorrectly formatted flags')
                if parts[0] in entries:
                    entries[parts[0]] = parts[1]
            executed = table.edit(**entries)
            if executed:
                print('Successfully edited')
            else:
                print('Too many or no matches to search')
        elif cmd[0] == 'exit':
            break
        else:
            raise Exception()
    except:
        print(f'Your input of "{inp}" is incorrectly formatted.')




