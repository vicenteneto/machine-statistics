from Crypto.Cipher import AES


class File(object):
    KEY = b'\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18'

    def __init__(self, filename):
        if not filename.endswith('.enc'):
            raise ValueError('Filename must ends with ".enc"')
        self.file = open(filename)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    def __decrypt_text(self, cipher_text):
        iv = cipher_text[:AES.block_size]
        cipher = AES.new(self.KEY, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(cipher_text[AES.block_size:])
        return plaintext.rstrip(b'\0')

    def decrypt(self):
        cipher_text = self.file.read()
        plaintext = self.__decrypt_text(cipher_text)
        with open(self.file.name[:-4], 'wb') as txt_file:
            txt_file.write(plaintext)
