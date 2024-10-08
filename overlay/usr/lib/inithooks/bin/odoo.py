#!/usr/bin/python3

"""Set Odoo Admin Password
Option:
    --pass=    unless provided, will ask interactively
"""

import re
import sys
import getopt

import crypt
import random
import hashlib
import configparser

import subprocess
from libinithooks.dialog_wrapper import Dialog
from pgsqlconf import PostgreSQL
from passlib.context import CryptContext

def usage(s=None):
    if s:
        print("Error:", s, file=sys.stderr)
    print("Syntax: %s [options]" % sys.argv[0], file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h", ['help', 'pass=', 'dbname='])
    except getopt.GetoptError as e:
        usage(e)

    password = ""
    db_name = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt == '--pass':
            password = val
        elif opt == '--dbname':
            db_name = val

    d = Dialog('TurnKey Linux - First boot configuration')
    if not password:
        password = d.get_password(
            "Odoo Database Management & 'admin' Password",
            "Enter new password for Odoo Database Management and 'admin' account:",
            blacklist=['\\', '/'])
    
    if not db_name:
        db_name = d.get_input(
            "Odoo Database Name",
            "Enter the name for the Odoo database:")

    processed_password = CryptContext(['pbkdf2_sha512']).hash(password)

    default_db = 'TurnkeylinuxExample'
    default_db_exists = True
    try:
        p = PostgreSQL(default_db)
        p.execute("UPDATE res_users SET password='{}' WHERE id=2".format(
            processed_password).encode('utf8'))
    except subprocess.CalledProcessError as e:
        default_db_exists = False
        print(f"Default DB ({default_db}) not found - skipping setting passsword for that")

    sys.path.insert(0, '/usr/lib/python3/dist-packages')
    import odoo
    odoo.tools.config.parse_config(['--config=/etc/odoo/odoo.conf'])
    odoo.tools.config.set_admin_password(password)
    odoo.tools.config.save()

    # restart odoo to apply updated password
    subprocess.run(['systemctl', 'restart', 'odoo'])

    if not default_db_exists:
        sys.exit(1)

if __name__ == "__main__":
    main()
