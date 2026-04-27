"""
Generate password hashes for sample accounts
Run this script to get proper password hashes for database.sql
"""

from werkzeug.security import generate_password_hash

passwords = {
    'admin': 'admin123',
    'juan': 'barber123',
    'pedro': 'barber123',
    'miguel': 'barber123',
    'customer1': 'customer123',
    'customer2': 'customer123'
}

print("Copy these into database.sql:\n")
for username, password in passwords.items():
    hash_value = generate_password_hash(password)
    print(f"-- {username}: {password}")
    print(f"'{hash_value}'")
    print()
