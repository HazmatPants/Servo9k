import json
import hashlib
import os

DB_FILE = 'data.json'
EXIT = False

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r') as file:
        return json.load(file)

def save_data(data):
    with open(DB_FILE, 'w') as file:
        json.dump(data, file, indent=2)

def add_user(name):
    data = load_data()
    new_id = hashlib.sha256(name.encode()).hexdigest()
    data.append({'id': new_id, 'name': name, 'points': 0})
    save_data(data)
    print(f'added user {name} ({new_id})')

def get_user(name):
    data = load_data()
    s_user = next((user for user in data if user['name'].startswith(name)), None)
    if s_user is None:
        s_user = next((user for user in data if user['id'].startswith(name)), None)
    return s_user

def update_user(target, update, new):
    data = load_data()
    for user in data:
        if user['id' if len(target) == 64 else 'name'].startswith(target):
            if update in user:
                if type(new) is int:
                    user[update] = new
                else:
                    user[update] = int(new) if new.isdigit() else new
                print(f'{target}\'s {update} updated to {new}')
            save_data(data)
            return True
    return False

def delete_user(user_id):
    data = load_data()
    new_data = [user for user in data if not user['id' if len(user_id) == 64 else 'name'].startswith(user_id)]
    save_data(new_data)
    print(f"{user_id} deleted")

def list_users():
    data = load_data()
    for user in data:
        print(f"{user['name']} ({user['id'][:4]}...) §{user['points']}")

def main():
    global EXIT
    while not EXIT:
        cmd = input("§ ")
        cmdArgs = cmd.split(' ')
        if cmdArgs[0] == 'help':
            print('''
                add: initialize a new user. usage: add <name>
                eg. add gordon-freeman
                get: get user data. usage: get <name/id> <key>
                eg. get gordon-freeman points
                set: set user data. usage: set <name/id> <key> <data>
                eg. set gordon-freeman points 50
                del: delete a user. usage: del <name/id>
                eg. del solari
                ls: list users.
                pts: add/remove points. usage: pts <name/id> <value>
                eg. pts gordon-freeman 100
                eg. pts solari -999
            ''')
        elif cmdArgs[0] == 'add':
            if len(cmdArgs) > 1:
                add_user(cmdArgs[1])
        elif cmdArgs[0] == 'get':
            if len(cmdArgs) > 2:
                data = get_user(cmdArgs[1])
                if cmdArgs[2] in data:
                    print(data[cmdArgs[2]])
            elif len(cmdArgs) > 1:
                print(get_user(cmdArgs[1]))
        elif cmdArgs[0] == 'set':
            if len(cmdArgs) > 3:
                update_user(cmdArgs[1], cmdArgs[2], cmdArgs[3])
        elif cmdArgs[0] == 'del':
            if len(cmdArgs) > 1:
                delete_user(cmdArgs[1])
        elif cmdArgs[0] == 'ls':
           list_users()
        elif cmdArgs[0] == 'pts':
           if len(cmdArgs) > 2 and cmdArgs[2].isdigit():
               user = get_user(cmdArgs[1])
               if user:
                   user['points'] += int(cmdArgs[2])
                   update_user(user['id'], 'points', user['points'])
        elif cmdArgs[0] == 'exit':
            print('bye')
            EXIT = True

if __name__ == "__main__":
    main()

