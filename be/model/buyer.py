import sqlite3 as sqlite
import uuid
import json
import logging
from be.model import db_conn
from be.model import error

import jwt
import time
import logging
import sqlite3 as sqlite
from be.model import error
from be.model import db_conn
import psycopg2


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            cursor = self.conn.cursor()
            for book_id, count in id_and_count:
                cursor.execute("SELECT book_id, stock_level, book_info FROM store WHERE store_id = '%s' AND book_id = '%s'" % (
                    store_id,book_id))
                row = cursor.fetchone()
                if row is None:
                    return error.error_non_exist_book_id(book_id) + (order_id,)

                stock_level = row[1]
                book_info = row[2]
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                res = cursor.execute.execute(
                    "UPDATE store set stock_level = stock_level - %d WHERE store_id = '%s' and book_id = %d  and stock_level >=%d" % (
                        count, store_id, book_id, count))
                if res.rowcount == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )

                cursor.execute(
                    "INSERT INTO new_order_detail(order_id, book_id, count, price) VALUES('%s',%d, %d, %d);" % (
                        order_id, book_id, count, price))

            cursor.execute(
                "INSERT INTO new_order(order_id, store_id, user_id) VALUES('%s','%s','%s');" % (
                    order_id, store_id, user_id))

            self.conn.commit()
            order_id = uid

        except sqlite.Error as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        conn = self.conn
        try:
            cursor = self.conn.cursor()
            cursor = conn.execute("SELECT order_id, user_id, store_id FROM new_order WHERE order_id = '%s'"%(order_id,))
            row = cursor.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row[0]
            buyer_id = row[1]
            store_id = row[2]

            if buyer_id != user_id:
                return error.error_authorization_fail()

            cursor = conn.execute("SELECT balance, password FROM user WHERE user_id = '%s'"%(buyer_id,))
            row = cursor.fetchone()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0]
            if password != row[1]:
                return error.error_authorization_fail()

            cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = '%s'"% (store_id,))
            row = cursor.fetchone()
            if row is None:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[1]

            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            cursor = conn.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = '%s'"% (order_id,))
            total_price = 0
            for row in cursor:
                count = row[1]
                price = row[2]
                total_price = total_price + price * count

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            cursor = conn.execute("UPDATE user set balance = balance - '%d'"
                                  "WHERE user_id = '%s' AND balance >= '%s'"%
                                  (total_price, buyer_id, total_price))
            if cursor.rowcount == 0:
                return error.error_not_sufficient_funds(order_id)

            cursor = conn.execute("UPDATE user set balance = balance + '%d'"
                                  "WHERE user_id = '%s'"%
                                  (total_price,  seller_id ))

            if cursor.rowcount == 0:
                return error.error_non_exist_user_id( seller_id )

            cursor = conn.execute("DELETE FROM new_order WHERE order_id = '%s'"%(order_id, ))
            if cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)

            cursor = conn.execute("DELETE FROM new_order_detail where order_id = '%s'"% (order_id, ))
            if cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)

            self.conn.commit()

        except sqlite.Error as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            cursor = self.conn.cursor()
            cursor = self.conn.execute("SELECT password  from user where user_id= '%s'"% (user_id,))
            row = cursor.fetchone()
            if row is None:
                return error.error_authorization_fail()

            if row[0] != password:
                return error.error_authorization_fail()

            cursor = self.conn.execute(
                "UPDATE user SET balance = balance + '%d' WHERE user_id = '%s'"%
                (add_value, user_id))
            if cursor.rowcount == 0:
                return error.error_non_exist_user_id(user_id)

            self.conn.commit()
        except sqlite.Error as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"




# # 买家
# class Buyer(db_conn.DBConn):
#     def __init__(self):  #初始化Buyer
#         db_conn.DBConn.__init__(self) # 连接数据库:self.conn = store.get_db_conn() -->  sqlite.connect(self.database)
#     # 买家 --> 下订单(用户id/店铺id/所购书id和数量)    返回类型：int, str, str（下订单成功返回： 200, "ok", order_id ）
#     def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
#         order_id = ""  #注意order_id是字符串类型，不是int类型
#         try:
#             if not self.user_id_exist(user_id):  # 用户ID不存在 error:511 error具体返回见be.model.error
#                 return error.error_non_exist_user_id(user_id) + (order_id, ) #"non exist user id {user_id}"
#             if not self.store_id_exist(store_id):   # 店铺ID不存在 error:513
#                 return error.error_non_exist_store_id(store_id) + (order_id, )
#             uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))    # 用户id 订单id  uuid.uuid1()：使用uuid生成唯一id(uuid1:基于时间戳)
#             #新订单 书的ID&数量
#             for book_id, count in id_and_count:
#                 cursor = self.conn.execute(
#                     "SELECT book_id, stock_level, book_info FROM store "    #从store表选出满足where条件的：book_id,stock_level（库存水平，即库存数量）,book_info
#                     "WHERE store_id = ? AND book_id = ?;",     #选出某店铺的某书的 书本ID、库存水平（数量）、书本信息
#                     (store_id, book_id)) #Python中内置了SQLite3，连接到数据库后，需要打开游标Cursor，通过Cursor执行SQL语句
#                 row = cursor.fetchone() #只取最上面的第一条结果，返回单个元组，(多次使用cursor.fetchone()，依次取得下一条结果，直到为空。)
#                 if row is None:
#                     return error.error_non_exist_book_id(book_id) + (order_id, ) #若此店铺无这本书 error：515
#
#                 stock_level = row[1]    #库存数量
#                 book_info = row[2]  #书本信息
#                 book_info_json = json.loads(book_info)  #将json格式数据转换为字典
#                 price = book_info_json.get("price") # 字典(Dictionary)get()函数返回指定键"price"的值。
#
#                 if stock_level < count:     #库存数量不够  （小于订单欲购数量）
#                     return error.error_stock_level_low(book_id) + (order_id,)    #返回error：517
#
#                 cursor = self.conn.execute(   #库存数量足够 更新store表：此店铺此书 库存数量 = 原库存数量 - 订单购此书数量
#                     "UPDATE store set stock_level = stock_level - ? "
#                     "WHERE store_id = ? and book_id = ? and stock_level >= ?; ",
#                     (count, store_id, book_id, count))
#                 if cursor.rowcount == 0:    # cursor.rowcount 表示由一种execute*()方法生成的最后结果中的行数
#                     return error.error_stock_level_low(book_id) + (order_id, )  #行数为0 说明库存数量不够 返回error：517
#
#                 self.conn.execute(    # 向表new_order_detail中插入订单数据
#                         "INSERT INTO new_order_detail(order_id, book_id, count, price) "
#                         "VALUES(?, ?, ?, ?);",
#                         (uid, book_id, count, price))# new_order_detail(订单细节信息):order_id book_id count 订单中此书数量 price书的价格
#
#             self.conn.execute( #向表new_order中插入订单数据
#                 "INSERT INTO new_order(order_id, store_id, user_id) "
#                 "VALUES(?, ?, ?);",
#                 (uid, store_id, user_id)) #new_order 订单信息:order_id user_id store_id
#             self.conn.commit() #提交事务
#             order_id = uid  # 第20行：uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
#         except sqlite.Error as e: #sqlite异常
#             logging.info("528, {}".format(str(e)))
#             return 528, "{}".format(str(e)), ""
#         except BaseException as e:   #python异常 ：Python所有异常错误的父类--BaseException
#             logging.info("530, {}".format(str(e)))
#             return 530, "{}".format(str(e)), ""
#
#         return 200, "ok", order_id   #买家下订单成功
#     #买家付款（ user_id/password: str/订单号order_id） 成功返回：200, "ok"
#     def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
#         conn = self.conn
#         try: #根据订单号order_id从new_order找到要付款的订单信息（order_id, user_id, store_id）
#             cursor = conn.execute("SELECT order_id, user_id, store_id FROM new_order WHERE order_id = ?", (order_id,))
#             row = cursor.fetchone() #取返回结果的第一行
#             if row is None:   #没有对应订单：error518
#                 return error.error_invalid_order_id(order_id)
#
#             order_id = row[0] #订单编号
#             buyer_id = row[1] #买家id
#             store_id = row[2] #店铺id
#
#             if buyer_id != user_id: #找到的订单信息里的买家不是user本人：用户授权失败 error401
#                 return error.error_authorization_fail()
#
#             cursor = conn.execute("SELECT balance, password FROM user WHERE user_id = ?;", (buyer_id,))
#             row = cursor.fetchone()     #根据user_id从user表取出余额balance, password
#             if row is None:
#                 return error.error_non_exist_user_id(buyer_id) #报错 不存在此用户
#             balance = row[0]
#             if password != row[1]:   #user密码输入错误
#                 return error.error_authorization_fail() #用户授权失败 error401
#
#             cursor = conn.execute("SELECT store_id, user_id FROM user_store WHERE store_id = ?;", (store_id,))
#             row = cursor.fetchone()   #根据店铺id从user_store找到店铺id和店主user_id
#             if row is None:
#                 return error.error_non_exist_store_id(store_id)
#
#             seller_id = row[1]  #卖家（店主） id
#
#             if not self.user_id_exist(seller_id):    #卖家不存在 报错
#                 return error.error_non_exist_user_id(seller_id)
#             # 根据订单id从new_order_detail表找到book_id, 数量count, 价格price
#             cursor = conn.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = ?;", (order_id,))
#             total_price = 0    #累计 此订单的书价总额（一个订单可能买多本书等）
#             for row in cursor:
#                 count = row[1]
#                 price = row[2]
#                 total_price = total_price + price * count
#
#             if balance < total_price: #用户余额不够，报错
#                 return error.error_not_sufficient_funds(order_id)
#             # 更新user表中买家余额（扣钱）
#             cursor = conn.execute("UPDATE user set balance = balance - ?"
#                                   "WHERE user_id = ? AND balance >= ?",
#                                   (total_price, buyer_id, total_price))
#             if cursor.rowcount == 0:   #余额不够：扣除失败
#                 return error.error_not_sufficient_funds(order_id)
#             # 更新user表中卖家余额（增钱）
#             cursor = conn.execute("UPDATE user set balance = balance + ?"
#                                   "WHERE user_id = ?",
#                                   (total_price, buyer_id))
#
#             if cursor.rowcount == 0: #找不到用户：增钱失败
#                 return error.error_non_exist_user_id(buyer_id)
#             # 金钱转移结束，删除new_order中订单信息
#             cursor = conn.execute("DELETE FROM new_order WHERE order_id = ?", (order_id, ))
#             if cursor.rowcount == 0:   #找不到此订单：报错
#                 return error.error_invalid_order_id(order_id)
#             # 删除new_order_detail中订单信息
#             cursor = conn.execute("DELETE FROM new_order_detail where order_id = ?", (order_id, ))
#             if cursor.rowcount == 0:
#                 return error.error_invalid_order_id(order_id)
#
#             conn.commit() #提交事务
#
#         except sqlite.Error as e:
#             return 528, "{}".format(str(e))
#
#         except BaseException as e:
#             return 530, "{}".format(str(e))
#
#         return 200, "ok"
#     #买家充值 （数额：￥add_value）
#     def add_funds(self, user_id, password, add_value) -> (int, str):
#         try:
#             cursor = self.conn.execute("SELECT password  from user where user_id=?", (user_id,))
#             row = cursor.fetchone()    #根据用户id找到其正确密码
#             if row is None:   #无此用户 报错
#                 return error.error_authorization_fail()
#
#             if row[0] != password:   # 密码输入错误 报错
#                 return error.error_authorization_fail()
#
#             cursor = self.conn.execute(
#                 "UPDATE user SET balance = balance + ? WHERE user_id = ?",
#                 (add_value, user_id))  #更新用户余额：余额增加add_value元
#             if cursor.rowcount == 0:  #找不到此用户 报错
#                 return error.error_non_exist_user_id(user_id)
#
#             self.conn.commit()  #提交事务
#         except sqlite.Error as e:
#             return 528, "{}".format(str(e))
#         except BaseException as e:
#             return 530, "{}".format(str(e))
#
#         return 200, "ok"
