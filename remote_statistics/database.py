import logging

from sqlalchemy.engine import create_engine, url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.session import sessionmaker

from remote_statistics.models import Base


class SessionError(Exception):
    pass


class Session(object):
    @staticmethod
    def from_config_element(database_config):
        if database_config is None:
            logging.warning('MySQL configuration element does not found!')
            return None

        logging.info('MySQL configuration element found!')

        host = database_config.get('host')
        port = database_config.get('port')
        username = database_config.get('username')
        password = database_config.get('password')
        database_name = database_config.get('database')

        if not database_name:
            logging.info('Database name does not found on MySQL configuration')
            return None

        engine = create_engine(url.URL('mysql', username, password, host, port, database_name))

        try:
            Base.metadata.create_all(engine)
            session = sessionmaker(bind=engine)()
            logging.info('MySQL session configured with success!')
        except OperationalError as error:
            logging.error('%s', error)
            raise SessionError()

        return session
