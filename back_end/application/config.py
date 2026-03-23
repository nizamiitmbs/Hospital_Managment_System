class Config():
    DEBUG=False
    SQLALCHMY_TRACK_MODICATIONS=False

class LocalDvelopmentConfig(Config):
    SQLALCHMY_database_URI='sqlite:///db.sqlite3'
    DEBUG=True

    SECRET_KEY="1234567890"  #hash user c in session
    SECURITY_PASSWORD_HASH="bcrypt" # mech for hashing pass
    SECURITY_PASSWORD_SALT="567890" #helps in hash pass
    WTF_CSRF_ENABLE=False 
    SECURITY_TOKEN_AUTHENTICATION_HEADER="Authentication-Token"
