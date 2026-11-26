"""Airflow UI for a local deployment: visitors who are not logged in get the Viewer role (read-only).

The port is bound to 127.0.0.1 in compose.yaml. To trigger or change anything, log in as `admin` (the password
`airflow standalone` prints in the container log). For a shared deployment, remove AUTH_ROLE_PUBLIC and configure
a real auth backend (LDAP, OAuth).
"""
from flask_appbuilder.security.manager import AUTH_DB

AUTH_TYPE = AUTH_DB
AUTH_ROLE_PUBLIC = "Viewer"  # was Admin: anyone, or any web page talking to localhost, could run and edit pipelines
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
WTF_CSRF_ENABLED = True
