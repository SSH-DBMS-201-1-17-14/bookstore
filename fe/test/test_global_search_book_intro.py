# import time
#
# import pytest
#
# from fe.access import auth
# from fe import conf
#
# class TestGlobal_search_book_intro:
#     @pytest.fixture(autouse=True)
#     def pre_run_initialization(self):
#         self.user_id = "test_register_user_{}".format(time.time())
#         self.auth = auth.Auth(conf.URL)
#         self.search_info = '作者生平自述，获今年最佳文学奖'  # 查询的book_intro
#         self.page = 1
#         yield
#
#     def test_global_search_book_intro(self):
#         code = self.auth.global_search_title(self.user_id, self.search_info,self.page)
#         assert code == 200
#
#     # 测试用户不存在
#     def test_error_non_user_id(self):
#         user_id = self.user_id + "_x"
#         code, token = self.auth.global_search_book_intro(user_id, self.search_info, self.page)
#         assert code == 511
#
#     #测试用户输入页码太大
#     def test_error_page_too_large(self):
#         large_page = 20
#         code, token = self.auth.global_search_book_intro(self.user_id, self.search_info, large_page)
#         assert code == 532
