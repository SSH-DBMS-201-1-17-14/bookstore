import time
from fe.access import auth
import pytest
from fe.access.new_seller import register_new_seller
from fe.test.gen_book_data import GenBook
import uuid
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book
from fe import conf
import pytest
import time
import uuid
from fe.access import auth
from fe.access.new_seller import register_new_seller
from fe import conf
from fe.access import book




class TestGlobal_search_book_intro:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.auth = auth.Auth(conf.URL)
        self.user_id = "test_register_user_{}".format(time.time())
        self.password = "password_" + self.user_id
        self.terminal = "terminal_" + self.user_id
        assert self.auth.register(self.user_id, self.password) == 200
        self.search_info = '一个女生的自白'  # 查询的book_intro
        self.page = 1
        yield

    def test_ok_global_search_book_intro(self):
        code  = self.auth.global_search_book_intro(self.user_id, self.search_info,self.page)
        assert code == 200

    # 测试用户不存在
    def test_error_non_user_id(self):
        user_id = self.user_id + "_x"
        code = self.auth.global_search_book_intro(user_id, self.search_info, self.page)
        assert code == 511

    # 测试用户输入页码太大
    def test_error_page_too_large(self):
        large_page = 20
        code = self.auth.global_search_book_intro(self.user_id, self.search_info, large_page)
        assert code == 532
