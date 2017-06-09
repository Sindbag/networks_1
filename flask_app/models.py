class User:
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def encode_password(self):
        return self.password