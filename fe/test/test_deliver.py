import pytest
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book

class TestDeliver:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        # 创建一个用户，开一家店
        self.seller_id = "test_deliver_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_deliver_store_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok

        self.seller = gen_book.get_seller()

        self.buyer_id = "test_deliver_buyer_id_{}".format(str(uuid.uuid1()))
        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        code, self.order_id = b.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            self.total_price = self.total_price + book.price * num

        self.another_seller_id = self.seller_id + "_another"
        self.another_seller = register_new_seller(self.another_seller_id, self.password)
        yield

    def test_error_set_pay(self):
        code = self.seller.deliver(self.seller_id, self.order_id)
        assert code == 522

    def test_error_non_order_id(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.seller.deliver(self.seller_id, self.order_id + "_x")
        assert code == 521

    def test_error_non_user(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.seller.deliver(self.seller_id + "_x", self.order_id+"_x")
        assert code == 511

    def test_error_non_exist_user_store_relation(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.another_seller.deliver(self.another_seller_id, self.order_id)
        assert code == 520

    def test_ok(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200
        code = self.seller.deliver(self.seller_id, self.order_id)
        assert code == 200

