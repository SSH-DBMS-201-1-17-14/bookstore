import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
from initial_database import intial_search
import psycopg2
import jieba
import re

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
            cursor=self.conn.cursor()
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
        cursor=self.conn.cursor()
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
                return error.error_authorization_fail() + ("", )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> bool:
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

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
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
    def split_user_input(self,string):
        new_string = re.sub(r'[^\w\s]', '', string)
        terms = jieba.lcut(new_string)
        while ' ' in terms:
            terms.remove(' ')
        while '\n' in terms:
            terms.remove('\n')
        return terms

    # 根据关键词列表获得 book_id 对应 其包含关键词个数 的字典
    def find_ids(self,terms, index_dic):   # ['三毛','的','三毛']
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
    def sort_id_importance(self,term_in_id, freqdic,page):
        importance_score = {}
        for id_num in term_in_id.keys():
            word_num = freqdic[id_num]
            score = term_in_id[id_num] / word_num * 1.0
            importance_score[id_num] = score
        importance_score = sorted(importance_score.items(), key=lambda d: d[1], reverse=True)
        return importance_score

    def store_search_title(self,store_id: str,search_info: str,page:int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 对用户的搜索进行分词，获得关键词列表
            keyword_term = self.split_user_input(search_info)
            # 获得 book_id 对应的包含关键词个数以及其分词后的长度
            bookdb = intial_search.BookSplit(False, store_id)
            dict_split_title, dict_split_book_intro, dict_split_content, freq_split_title, freq_split_book_intro, freq_split_content = bookdb.inverted_index()
            # 获得 book_id 对应 其包含关键词个数 的字典
            book_id_keyword_count = self.find_ids(keyword_term,dict_split_title)
            # 获得对应页数的 book_id
            book_id = self.sort_id_importance(book_id_keyword_count,freq_split_title,page)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""
        return 200, "ok", book_id

    def store_book_intro(self,store_id: str,search_info: str,page:int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 对用户的搜索进行分词，获得关键词列表
            keyword_term = self.split_user_input(search_info)
            # 获得 book_id 对应的包含关键词个数以及其分词后的长度
            bookdb = intial_search.BookSplit(False, store_id)
            dict_split_title, dict_split_book_intro, dict_split_content, freq_split_title, freq_split_book_intro, freq_split_content = bookdb.inverted_index()
            # 获得 book_id 对应 其包含关键词个数 的字典
            book_id_keyword_count = self.find_ids(keyword_term, dict_split_book_intro)
            # 获得对应页数的 book_id
            book_id = self.sort_id_importance(book_id_keyword_count, freq_split_book_intro, page)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""
        return 200, "ok", book_id

    def store_search_content(self,store_id: str,search_info: str,page:int):
        try:
            # 首先，判断 store 表中是否存在 store_id，可能存在用户建店铺但未上架新书的情况
            if not self.store_book_empty(store_id):
                return error.error_store_book_empty(store_id)
            # 对用户的搜索进行分词，获得关键词列表
            keyword_term = self.split_user_input(search_info)
            # 获得 book_id 对应的包含关键词个数以及其分词后的长度
            bookdb = intial_search.BookSplit(False, store_id)
            dict_split_title, dict_split_book_intro, dict_split_content, freq_split_title, freq_split_book_intro, freq_split_content = bookdb.inverted_index()
            # 获得 book_id 对应 其包含关键词个数 的字典
            book_id_keyword_count = self.find_ids(keyword_term, dict_split_content)
            # 获得对应页数的 book_id
            book_id = self.sort_id_importance(book_id_keyword_count, freq_split_content, page)
        except (Exception, psycopg2.DatabaseError) as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""
        return 200, "ok", book_id

    def global_search_title(self,search_info:str):
        # 先对搜索内容进行分词，获得关键词
        keyword_list =
        book_id_count = {}    # 每一个 book_id 包含关键字个数
        book_id_length = {}   # 每一个 book_id 本身拥有的单词个数
        try:
            for key_word in keyword_list:
                # 获得每个关键词对应的 book_id
                cursor = self.conn.cursor()
                cursor.execute("SELECT book_id FROM book_split_title WHERE keyword = %s",(key_word,))
                row = cursor.fetchone()
                if row is not None:
                    # 表中存储的 book_id 为字符串的形式，类似于 "{1000134,1009273}"
                    print(row[0])
