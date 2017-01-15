import errno
import logging
import sys
from xml.etree import ElementTree
from xml.etree.ElementTree import ParseError

__author__ = 'Vicente Neto <sneto.vicente@gmail.com>'


def load_configuration(config_path):
    try:
        tree = ElementTree.parse(config_path)
        logging.info('Configuration file loaded with success!')

        config_root = tree.getroot()
        database = config_root.find('database')
        smtp = config_root.find('smtp')
        clients = config_root.find('clients')

        return database, smtp, clients
    except IOError as error:
        logging.error('%s. Configuration file does not found. Terminating program.', error)
        sys.exit(errno.ENOENT)
    except ParseError as error:
        logging.error('%s. Bad configuration file format. Terminating program', error)
        sys.exit(errno.EBFONT)
