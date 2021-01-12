import pytest
import time
import uuid
from fe.access import auth
from fe.access.new_seller import register_new_seller
from fe import conf
from fe.access import book

class TestGlobalSearchTag:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.auth = auth.Auth(conf.URL)
        # 注册一个用户进行搜索
        self.user_id = "test_global_search_tag_store_id_1_{}".format(time.time())
        self.password = "password_" + self.user_id
        self.terminal = "terminal_" + self.user_id
        assert self.auth.register(self.user_id, self.password) == 200

        # 注册一个店铺，对其进行增加库存，进行被搜索
        self.another_user_id = "test_global_search_tag_store_id_2_{}".format(time.time())
        self.seller = register_new_seller(self.another_user_id, self.password)
        self.store_id = "test_global_search_tag_store_id_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 对其增加库存（100本书）
        book_db = book.BookDB()
        self.books = book_db.get_book_info(0, 100)
        for b in self.books:
            code = self.seller.add_book(self.store_id, 0, b)
            assert code == 200
        # 搜索的标题内容

        self.book_id = '1000067'

        yield

    def test_ok(self):
        code = self.auth.get_store_id(self.user_id, self.book_id)
        assert code == 200

    # 用户的 id 不存在
    def test_error_user_id(self):
        code = self.auth.get_store_id(self.user_id + "_x", self.book_id)
        assert code == 533





