import login_db as DB

db = DB.LoginDB('test', 'admin', 'admin')

# causes weird __del__ error
table = db.login('admin', 'admin')
table = db.login('admin', 'admin1')


table.add_entry(name='test', url='test.com', description='first trial', usr='testing', pssd='123')
print(table.get_entries())

table.delete(name='test')
print(table.get_entries())

