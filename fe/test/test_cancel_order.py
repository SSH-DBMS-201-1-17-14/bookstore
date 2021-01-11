import pytest
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book


class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 创建一个用户，开一家店
        self.seller_id = "test_cancel_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_cancel_order_store_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        self.seller = gen_book.get_seller()

        self.buyer_id = "test_cancel_order_buyer_id_{}".format(str(uuid.uuid1()))
        buyer1 = register_new_buyer(self.buyer_id, self.password)
        self.buyer = buyer1
        self.another_buyer_id = self.buyer_id + "_another"
        buyer2 = register_new_buyer(self.another_buyer_id, self.password)

        code, self.order_id = buyer1.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            self.total_price = self.total_price + book.price * num

        yield

    def test_error_non_user(self):
        code = self.buyer.cancel_order(self.buyer_id + "_x", self.password, self.order_id)
        assert code == 511

    def test_error_password(self):
        code = self.buyer.cancel_order(self.buyer_id, self.password + "_x", self.order_id)
        assert code == 401

    def test_error_order_id(self):
        code = self.buyer.cancel_order(self.buyer_id, self.password, self.order_id + "_x")
        assert code == 522

    def test_error_buyer_order_belong(self):
        code = self.buyer.cancel_order(self.another_buyer_id, self.password, self.order_id)
        assert code == 541

    def test_error_pay(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.cancel_order(self.buyer_id, self.password, self.order_id)
        assert code == 543

    def test_ok(self):
        code = self.buyer.cancel_order(self.buyer_id, self.password, self.order_id)
        assert code == 200


