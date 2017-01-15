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
    """
    An built-in File object wrapper that provides the remote_statistics encrypt function. The built-in File object
    created is accessible using the file attribute.

    The filename argument must can not end with .enc, otherwise and ValueError is raised.
    """
    KEY = b'\xbf\xc0\x85)\x10nc\x94\x02)j\xdf\xcb\xc4\x94\x9d(\x9e[EX\xc8\xd5\xbfI{\xa2$\x05(\xd5\x18'

    def __init__(self, name):
        if name.endswith('.enc'):
            raise ValueError('Name cannot ends with ".enc"')
        self.file = open(name, 'rb')

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


class MachineStatistics(object):
    """
    This class is used to collect remote machine statics, such as uptime, CPU, memory and disk partitions usage.

    The collect statics methods are: collect_cpu_usage(), collect_memory_usage(), collect_uptime() and
    collect_disks_usage().
    """

    def __init__(self):
        self.execution_date = datetime.utcnow()
        self.cpu_percent = None
        self.memory_used = None
        self.memory_percent = None
        self.uptime = None
        self.disk_partitions = list()

    def collect_cpu_usage(self):
        self.cpu_percent = psutil.cpu_percent(interval=1)

    def collect_memory_usage(self):
        virtual_memory = psutil.virtual_memory()
        self.memory_used = virtual_memory.used
        self.memory_percent = virtual_memory.percent

    def collect_uptime(self):
        self.uptime = psutil.boot_time()

    def collect_disks_usage(self):
        for partition in psutil.disk_partitions():
            usage = psutil.disk_usage(partition.mountpoint)
            partition_usage = {'mountpoint': partition.mountpoint, 'used': usage.used, 'percent': usage.percent}
            self.disk_partitions.append(partition_usage)


statistics = MachineStatistics()
statistics.collect_cpu_usage()
statistics.collect_memory_usage()
statistics.collect_uptime()
statistics.collect_disks_usage()

with open('/tmp/client_data.json', 'wb') as data_file:
    pickle.dump(statistics.__dict__, data_file)

with File('/tmp/client_data.json') as data_file:
    data_file.encrypt()
