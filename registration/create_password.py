from hashlib import sha256

def create_password():
	return sha256(b'a dummy password').hexdigest()

if __name__ == '__main__':
	print(create_password())
