from unittest import TestCase

from remote_statistics.models import Client
from remote_statistics.tests import util


class TestClient(TestCase):
    def test_instantiate_from_element(self):
        self.assertIsInstance(Client.from_element(util.create_client_element()), Client)
