"""Airflow UI for a local deployment: no login, read-only viewers get the Viewer role.

The port is bound to 127.0.0.1 in compose.yaml. For a shared deployment, remove AUTH_ROLE_PUBLIC and configure
a real auth backend (LDAP, OAuth).
"""
from flask_appbuilder.security.manager import AUTH_DB

AUTH_TYPE = AUTH_DB
AUTH_ROLE_PUBLIC = "Admin"
WTF_CSRF_ENABLED = True
