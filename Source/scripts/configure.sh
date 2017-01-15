#!/bin/bash

# Install the build dependencies
sudo apt-get install -y autotools-dev blt-dev bzip2 dpkg-dev g++-multilib gcc-multilib libbluetooth-dev libbz2-dev \
libexpat1-dev libffi-dev libffi6 libffi6-dbg libgdbm-dev libgpm2 libncursesw5-dev libreadline-dev libsqlite3-dev \
libssl-dev libtinfo-dev mime-support net-tools netbase python-crypto python-mox3 python-pil python-ply quilt tk-dev \
zlib1g-dev


if [ ! -d "/usr/local/lib/python2.7.13" ]; then
    # Get Python sources and compile:
    wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tgz
    tar xfz Python-2.7.13.tgz
    cd Python-2.7.13/
    ./configure --prefix /usr/local/lib/python2.7.13 --enable-ipv6
    make
    sudo make install


    # Removing files
    cd ..
    rm Python-2.7.13.tgz
    rm -rf Python-2.7.13/
fi
