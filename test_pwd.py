import bcrypt
def verify(plain, hashed):
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

h1 = "$2b$12$glvrskSBl2m4dxi.ECEfnOIpnTsCimQi/aL0WehiJ2k9bwxPwJhKK"
print("Testing 'admin123':", verify("admin123", h1))
print("Testing 'admin':", verify("admin", h1))

h2 = "$2b$12$n/dweowDMdMfJmZAxbKbOeo6RETtz5Ds/KOW8HiXbCDjf1Qq7Oez2"
print("Testing 'giri123':", verify("giri123", h2))
print("Testing 'giri':", verify("giri", h2))
