"""
1. This script will be uploaded and executed to 100s of machines in the intranet. These machines are meant to be
monitored for system level statistics like memory usage, CPU usage, total uptime and windows security event logs (in
case of windows OS).

2. When executed, the client script collects the statistics and return them to the server script for cumulation.
3. The client script must encrypt the data before returning it to server.
"""
import pickle
from datetime import datetime

import psutil
from Crypto import Random
from Crypto.Cipher import AES


class File(object):
    KEY = b'\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18'

    def __init__(self, name, mode):
        if name.endswith('.enc'):
            raise ValueError('name cannot ends with ".enc"')
        self.file = open(name, mode)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()

    @staticmethod
    def pad(s):
        return s + b'\0' * (AES.block_size - len(s) % AES.block_size)

    def __encrypt_text(self, message):
        message = self.pad(message)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.KEY, AES.MODE_CBC, iv)
        return iv + cipher.encrypt(message)

    def encrypt(self):
        plaintext = self.file.read()
        cipher_text = self.__encrypt_text(plaintext)
        with open(self.file.name + '.enc', 'wb') as enc_file:
            enc_file.write(cipher_text)


execution_date = datetime.utcnow()
cpu_percent = psutil.cpu_percent(interval=1)
virtual_memory = psutil.virtual_memory()
disk_partitions = psutil.disk_partitions()
uptime = psutil.boot_time()

disk_usage = dict()
for partition in disk_partitions:
    usage = psutil.disk_usage(partition.mountpoint)
    disk_usage[partition.mountpoint] = {'used': usage.used, 'percent': usage.percent}

metrics = {
    'execution_date': execution_date,
    'cpu': cpu_percent,
    'memory': {
        'used': virtual_memory.used,
        'percent': virtual_memory.percent
    },
    'disk': disk_usage,
    'uptime': uptime
}

with open('/tmp/client_data.json', 'wb') as data_file:
    pickle.dump(metrics, data_file)

with File('/tmp/client_data.json', 'rb') as data_file:
    data_file.encrypt()
