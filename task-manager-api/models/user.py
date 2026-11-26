import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.helpers import utcnow

LEGACY_MD5_RE = re.compile(r"^[0-9a-f]{32}$")


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # o hash da senha não sai na resposta
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def uses_legacy_hash(self):
        return bool(self.password and LEGACY_MD5_RE.match(self.password))

    def check_password(self, pwd):
        if self.uses_legacy_hash():
            # bancos antigos guardavam MD5; aceita e o service regrava com hash novo
            return hmac.compare_digest(self.password, hashlib.md5(pwd.encode()).hexdigest())
        return check_password_hash(self.password, pwd)

    def is_admin(self):
        return self.role == 'admin'
