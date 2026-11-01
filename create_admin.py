
from getpass import getpass
from auth import init_auth_db, create_user

init_auth_db()

username = input("Admin username: ").strip()
password = getpass("Admin password (minimum 12 characters): ")
confirm = getpass("Confirm password: ")

if password != confirm:
    print("Passwords do not match")
else:
    try:
        create_user(username, password, "ADMIN")
        print("Administrator created successfully")
    except ValueError as error:
        print("Error:", error)
