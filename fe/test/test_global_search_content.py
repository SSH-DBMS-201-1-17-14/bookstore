import pytest
import time
import uuid
from fe.access import auth
from fe.access.new_seller import register_new_seller
from fe import conf
from fe.access import book

class TestGlobal_search_content:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.auth = auth.Auth(conf.URL)
        # 注册一个用户进行搜索
        self.user_id = "test_global_search_content_store_id_1_{}".format(time.time())
        self.password = "password_" + self.user_id
        self.terminal = "terminal_" + self.user_id
        assert self.auth.register(self.user_id, self.password) == 200
        # 注册一个店铺，对其进行增加库存，进行被搜索
        self.another_user_id = "test_global_search_content_store_id_2_{}".format(time.time())
        self.seller = register_new_seller(self.another_user_id, self.password)
        self.store_id = "test_global_search_content_store_id_{}".format(str(uuid.uuid1()))
        assert self.seller.create_store(self.store_id) == 200
        # 对其增加库存（80本书）
        book_db = book.BookDB()
        self.books = book_db.get_book_info(0, 100)
        for b in self.books:
            code = self.seller.add_book(self.store_id, 0, b)
            assert code == 200
        # 搜索的标题内容
        self.search_info = "一个 女生的自白 \n"
        # 搜索的页数
        self.page = 1
        self.large_page = 20
        yield

    def test_global_search_content(self):
        code = self.auth.global_search_content(self.user_id, self.search_info,self.page)
        assert code == 200

    # 测试用户不存在
    def test_error_non_user_id(self):
        user_id = self.user_id + "_x"
        code = self.auth.global_search_content(user_id, self.search_info, self.page)
        assert code == 511

    #测试用户输入页码太大
    def test_error_page_too_large(self):
        code = self.auth.global_search_content(self.user_id, self.search_info, self.large_page)
        assert code == 532
