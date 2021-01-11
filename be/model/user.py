import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
from initial_database import initial_search
import psycopg2
import jieba
import re
from math import ceil
from be.model import search
import traceback

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }

def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    # return encoded.decode("utf-8")
    return encoded


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }

def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            return False

        # try:
        #     if db_token != token:
        #         return False
        #     jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
        #     ts = jwt_text["timestamp"]
        #     if ts is not None:
        #         now = time.time()
        #         if self.token_lifetime > now - ts >= 0:
        #             return True
        # except jwt.exceptions.InvalidSignatureError as e:
        #     logging.error(str(e))
        #     return False

    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT into \"user\"(user_id, password, balance, token, terminal) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, password, 0, token, terminal))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError):
            return error.error_exist_user_id(user_id)
        cursor.close()
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT token from \"user\" where user_id=%s", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return error.error_authorization_fail()
        db_token = row[0]
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        cursor.close()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password from \"user\" where user_id=%s", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return error.error_authorization_fail()

        if password != row[0]:
            return error.error_authorization_fail()
        cursor.close()
        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" set token= %s , terminal = %s where user_id = %s",
                (token, terminal, user_id), )
            if cursor.rowcount == 0:
                return error.error_authorization_fail() + ("",)
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str):
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" SET token = %s, terminal = %s WHERE user_id=%s",
                (dummy_token, terminal, user_id), )
            if cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message
            cursor = self.conn.cursor()
            cursor.execute("DELETE from \"user\" where user_id=%s", (user_id,))
            if cursor.rowcount == 1:
                self.conn.commit()
            else:
                return error.error_authorization_fail()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str):
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" set password = %s, token= %s , terminal = %s where user_id = %s",
                (new_password, token, terminal, user_id), )
            if cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    # 对一个字符串进行分词，获得词项对应的列表
    def split_user_input(self, string):
        new_string = re.sub(r'[^\w\s]', '', string)  # 只保留中文和英文字符，去掉符号
        terms = jieba.lcut(new_string)  # 分词 得到分词列表
        # 去除为空的
        while ' ' in terms:
            terms.remove(' ')
        while '\n' in terms:
            terms.remove('\n')
        return terms

    # 根据关键词列表获得 book_id 对应 其包含关键词个数 的字典
    def find_ids(self, terms, index_dic):  # ['三毛','的','三毛']
        term_in_id = {}
        for term in terms:
            if term in index_dic.keys():
                value_ids = index_dic[term]
                for id in value_ids:
                    if id in term_in_id.keys():
                        term_in_id[id] = term_in_id[id] + 1
                    else:
                        term_in_id[id] = 1
        return term_in_id

    # 传入 book_id 对应 其包含关键词个数 的字典以及 book_id 对应 分词后词项长度 的字典
    # 对每个 book_id 的重要程度打分并且降序排序，返回对应页数的 book_id 列表
    def sort_id_importance_pagek(self, term_in_id, freqdic, pagek):
        importance_score = {}
        # 对id
        for id_num in term_in_id.keys():
            word_num = freqdic[id_num]  # 得到id对应字符串本身分词个数
            score = term_in_id[id_num] / word_num * 1.0  # 得分
            importance_score[id_num] = score  # 得到所有排序
        importance_score = sorted(importance_score.items(), key=lambda d: d[1], reverse=True)  # 由分数的从高到低进行排序
        # 因为最后一页不一定能显10个，判断一下能分几页
        id_n = len(importance_score)
        # print('.........id_n......... = %d'%id_n)
        pages_num = ceil(id_n / 10 * 1.0)  # 共有pages_num
        # print('.........pages_num......... = %d'%pages_num)
        # 输入页码超过最大页数,输出空列表
        if pagek > pages_num:
            return []
        # 输入页码小于等于最大页数
        # 分页 第k页：下标（从0开始）  ： 10*(k-1) 到 k*10-1
        start = 10 * (pagek - 1)
        end = pagek * 10 - 1
        # 如果是最后一页,不一定能输10个，只能输出到最后一个
        if pagek == pages_num:
            end = id_n - 1
        id_l = []  # 最后输出的id
        for i in range(start, end + 1):
            id_l.append(importance_score[i][0])
        return id_l

    def store_search_title(self, user_id: str, store_id: str, search_info: str, page: int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 进行查询
            ## 先找出这家店的book_id
            cursor = self.conn.cursor()
            # query =   #global 的时候去掉where
            # cursor.execute("SELECT book_id FROM \"store\" WHERE stock_level > 0 AND store_id = %s", (store_id,)  )
            cursor.execute("SELECT book_id FROM \"store\" WHERE store_id = %s", (store_id,))
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            title_search = search.Search(search_info, page, book_id) #实例化一个search类
            book_list = title_search.search_bookid_title()  # !!!!!调用函数，得到返回结果
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)

        except (Exception, psycopg2.DatabaseError) as e:
            traceback.print_exc()
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e))," "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e))," "
        return 200, "ok", book_list


    def store_search_book_intro(self, user_id: str, store_id: str, search_info: str, page: int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 查询
            ## 先找出这家店的book_id
            cursor = self.conn.cursor()
            # query =     #global 的时候去掉where
            cursor.execute("SELECT book_id FROM \"store\" WHERE store_id = %s", (store_id,))
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            book_intro_search = search.Search(search_info, page, book_id) #实例化一个search类
            book_list = book_intro_search.search_bookid_book_intro()  # !!!!!调用函数，得到返回结果
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.log(logging.CRITICAL, "*****"+store_id+"*******")
            traceback.print_exc()
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), " "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), " "
        return 200, "ok", book_list

    def store_search_content(self, user_id: str, store_id: str, search_info: str, page: int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 查询
            # # 先找出这家店的book_id
            cursor = self.conn.cursor()
            # query =    #global 的时候去掉where
            cursor.execute("SELECT book_id FROM \"store\" WHERE store_id = %s", (store_id,) )
            rows=cursor.fetchall()
            if rows is None:
                return error.error_page_out_of_range(user_id)
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            content_search = search.Search(search_info, page, book_id) #实例化一个search类
            book_list = content_search.search_bookid_content()  # !!!!!调用函数，得到返回结果 返回得到相关排列
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)


        except (Exception, psycopg2.DatabaseError) as e:
            traceback.print_exc()
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e))," "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e))," "
        return 200, "ok", book_list

    def store_search_tag(self, user_id: str, store_id: str, search_info: str, page: int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 进行查询
            cursor = self.conn.cursor()
            # query =
            cursor.execute("SELECT book_id FROM \"store\" WHERE store_id = %s", (store_id,))
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            title_search = search.Search(search_info, page, book_id)
            # 考虑到用户会输入多个 tag 的情况，选出覆盖全部 tag 的 bookid
            tag_search = search_info.split(" ")  # 获得用户输入的多个 tag
            book_list = title_search.search_bookid_tag(tag_search)
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), " "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), " "
        return 200, "ok", book_list


    def global_search_title(self, user_id: str, search_info: str, page: int):
        try:
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 查询
            # # 先找出这家店的book_id
            cursor = self.conn.cursor()
            query = "SELECT book_id FROM \"store\" "   #global 的时候去掉where
            cursor.execute(query)
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            title_search = search.Search(search_info, page, book_id) #实例化一个search类
            book_list =  title_search.search_bookid_content()  # !!!!!调用函数，得到返回结果 返回得到相关列表
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), " "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), " "
        return 200, "ok", book_list

    def global_search_book_intro(self, user_id: str, search_info: str, page: int):
        try:
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 查询
            # # 先找出这家店的book_id
            cursor = self.conn.cursor()
            query = "SELECT book_id FROM \"store\" "  # global 的时候去掉where
            cursor.execute(query)
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            book_intro_search = search.Search(search_info, page, book_id)  # 实例化一个search类
            book_list = book_intro_search.search_bookid_content()  # !!!!!调用函数，得到返回结果 返回得到相关列表
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e))," "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e))," "
        return 200, "ok", book_list

    def global_search_content(self, user_id: str, search_info: str, page: int):
        try:  # 判断是否存在用户 id
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 查询
            # # 先找出这家店的book_id
            cursor = self.conn.cursor()
            query = "SELECT book_id FROM \"store\" "  # global 的时候去掉where
            cursor.execute(query)
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            _content_search = search.Search(search_info, page, book_id)  # 实例化一个search类
            book_list = _content_search.search_bookid_content()  # !!!!!调用函数，得到返回结果 返回得到相关列表
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e))," "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e))," "
        return 200, "ok",book_list

    def global_search_tag(self, user_id: str, store_id: str, search_info: str, page: int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 判断是否存在用户 id
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id_when_search(user_id)
            # 进行查询
            cursor = self.conn.cursor()
            # query =
            cursor.execute("SELECT book_id FROM \"store\" ", (store_id,))
            book_id = []
            for row in cursor:
                book_id.append(row[0])
            title_search = search.Search(search_info, page, book_id)
            # 考虑到用户会输入多个 tag 的情况，选出覆盖全部 tag 的 bookid
            tag_search = search_info.split(" ")  # 获得用户输入的多个 tag
            book_list = title_search.search_bookid_tag(tag_search)
            if len(book_list) == 0:
                return error.error_page_out_of_range(user_id)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e))," "
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e))," "
        return 200, "ok" ,book_list
