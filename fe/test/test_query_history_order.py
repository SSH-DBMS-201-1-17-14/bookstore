import pytest
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.test.gen_book_data import GenBook
from fe.access.book import Book


class TestQueryHistoryOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 创建一个用户，开一家店
        self.seller_id = "test_query_history_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_query_history_order_store_id_{}".format(str(uuid.uuid1()))
        # self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, self.buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)

        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            self.total_price = self.total_price + book.price * num

        self.seller = gen_book.get_seller()

        self.buyer_id = "test_query_history_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.buyer_id
        self.buyer = register_new_buyer(self.buyer_id, self.password)

        # 未付款
        code, self.order_id1 = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200


        # 已付款
        code, self.order_id2 = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        # assert self.buy_book_id_list==[]
        assert code == 200
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id2)
        assert code == 200

        # 已发货
        code, self.order_id3 = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id3)
        assert code == 200
        code = self.seller.deliver(self.seller_id, self.order_id3)
        assert code == 200

        # 已收货
        code, self.order_id4 = self.buyer.new_order(self.store_id, self.buy_book_id_list)
        assert code == 200
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id4)
        assert code == 200
        code = self.seller.deliver(self.seller_id, self.order_id4)
        assert code == 200
        code = self.buyer.receive(self.buyer_id, self.order_id4)
        assert code == 200
        yield

    def test_ok(self):
        code = self.buyer.query_history_order(self.buyer_id, self.password)
        assert code == 200

    def test_error_user_id(self):
        code = self.buyer.query_history_order(self.buyer_id + "_x", self.password)
        assert code == 511

    def test_error_password(self):
        code = self.buyer.query_history_order(self.buyer_id, self.password + "_x")
        assert code == 401
