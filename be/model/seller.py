import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import psycopg2
import traceback

class Seller(db_conn.DBConn):

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_store_exist(user_id,store_id):
                if not self.user_id_exist(user_id):
                    return error.error_non_exist_user_id(user_id)
                if not self.store_id_exist(store_id):
                    return error.error_non_exist_store_id(store_id)
                return error.error_and_message(520,error.error_code[520].format(user_id,store_id))
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)
            cur=self.conn.cursor()
            cur.execute("INSERT into \"store\"(store_id, book_id, book_info, stock_level)"
                              "VALUES (%s, %s, %s, %s)", (store_id, book_id, book_json_str, stock_level))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError) as e:
            print(self.conn)
            print(type(self.conn))
            print(e)
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_store_exist(user_id, store_id):
                if not self.user_id_exist(user_id):
                    return error.error_non_exist_user_id(user_id)
                if not self.store_id_exist(store_id):
                    return error.error_non_exist_store_id(store_id)
                return error.error_and_message(520,error.error_code[520].format(user_id,store_id))

            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)
            cursor=self.conn.cursor()
            cursor.execute("UPDATE \"store\" SET stock_level = stock_level + (%s) "
                              "WHERE store_id = (%s) AND book_id = (%s)", (add_stock_level, store_id, book_id))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError)  as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            cursor=self.conn.cursor()
            cursor.execute("INSERT into \"user_store\"(store_id, user_id)"
                              "VALUES (%s, %s)", (store_id, user_id))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError)  as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def deliver(self,user_id:str,order_id:str)->(int,str):
        try:
            if not self.order_id_exist(order_id):
                if not self.user_id_exist(user_id):
                    return error.error_non_exist_user_id(user_id)
                else:
                    return error.error_and_message(522,error.error_code[522].format(order_id))
            cursor=self.conn.cursor()
            cursor.execute("select store_id,pay from \"new_order\" where order_id=(%s)",(order_id,))
            row=cursor.fetchone()
            store_id=row[0]
            pay=row[1]
            if not self.user_store_exist(user_id,store_id):
                return error.error_and_message(521,error.error_code[521].format(user_id,store_id))
            if not pay==1:
                return error.error_and_message(523,error.error_code[523])

            cursor.execute("UPDATE \"new_order\" SET deliver=1 WHERE order_id=(%s)", (order_id,))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError)  as e:
            traceback.print_exc()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
