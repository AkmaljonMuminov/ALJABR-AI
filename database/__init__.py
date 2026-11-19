"""ALJABR DATABASE - SQLite access layer shared by memory (and later security logs).

Modules:
    migrations   versioned schema (PRAGMA user_version)
    connection   open_database(path): creates a private file and migrates it
"""
