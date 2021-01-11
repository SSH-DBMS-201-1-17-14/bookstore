import pytest
import uuid
from fe.access.new_buyer import register_new_buyer


class TestQueryHistoryOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.user_id = "test_query_history_order_{}".format(str(uuid.uuid1()))
        self.password = self.user_id
        self.buyer = register_new_buyer(self.user_id, self.password)
        yield

    def test_ok(self):
        code = self.buyer.query_history_order(self.user_id, self.password)
        assert code == 200

    def test_error_user_id(self):
        code = self.buyer.query_history_order(self.user_id + "_x", self.password)
        assert code == 511

    def test_error_password(self):
        code = self.buyer.query_history_order(self.user_id, self.password + "_x")
        assert code == 401
