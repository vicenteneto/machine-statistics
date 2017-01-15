import logging

from sqlalchemy.engine import create_engine, url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.session import sessionmaker

from remote_statistics.models import Base


class SessionError(Exception):
    """
    This exception is raised if the SQLAlchemy create_all or sessionmaker functions raises an OperationalError.
    """


class Session(object):
    """
    An Session instance encapsulates an SQLAlchemy session object.

    You can instantiate this class, passing to the from_config_element method an xml.tree.ElementTree configuration on
    the following format:
        <database host="localhost" port="3306" username="root" password="password" database="db_name"/>
    """

    @staticmethod
    def from_config_element(database_config):
        if database_config is None:
            logging.warning('MySQL configuration element does not found!')
            raise SessionError()

        logging.info('MySQL configuration element found!')

        host = database_config.get('host')
        port = database_config.get('port')
        username = database_config.get('username')
        password = database_config.get('password')
        database_name = database_config.get('database')

        if not database_name:
            logging.info('Database name does not found on MySQL configuration')
            raise SessionError()

        engine = create_engine(url.URL('mysql', username, password, host, port, database_name))

        try:
            Base.metadata.create_all(engine)
            session = sessionmaker(bind=engine)()
            logging.info('MySQL session configured with success!')
        except OperationalError as error:
            logging.error('%s', error)
            raise SessionError()

        return session
