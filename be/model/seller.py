import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import psycopg2
import traceback
import be.model.tool as tool
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

    def admmit_return(self,user_id,password,order_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT password  from \"user\" where user_id= (%s)", (user_id,))
            row = cursor.fetchone()
            if row is None:
                return error.error_non_exist_user_id(user_id)

            if row[0] != password:
                return error.error_authorization_fail()

            if not self.order_id_exist(order_id):
                return error.error_and_message(522, error.error_code[522].format(order_id))

            if not self.return_flag_set(order_id):
                return error.error_and_message(544, error.error_code[544].format(order_id))

            cursor.execute("SELECT book_id, count, price FROM \"new_order_detail\" WHERE order_id = (%s)", (order_id,))
            total_price = 0
            rows=cursor.fetchall()
            for row in rows:
                count = row[1]
                price = row[2]
                total_price = total_price + price * count

            cursor.execute("SELECT user_id from \"new_order\" where order_id= (%s)", (order_id,))
            buyer_id=cursor.fetchone()[0]

            cursor.execute("UPDATE \"user\" SET balance = balance - (%s)"
                           "WHERE user_id = (%s) AND balance >= (%s)",
                           (total_price, user_id, total_price))


            cursor.execute("UPDATE \"user\" SET balance = balance + (%s)"
                           "WHERE user_id = (%s)",
                           (total_price, buyer_id,))

            tool.cancel_order_tool(self.conn,order_id)
            cursor.execute("UPDATE \"new_order\" SET refund=1"
                           "WHERE order_id = (%s)",
                           (order_id,))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError)  as e:
            traceback.print_exc()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

