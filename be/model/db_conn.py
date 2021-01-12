from be.model import store

class DBConn:
    def __init__(self):
        self.conn = store.get_db_conn()

    # 是否存在某用户
    def user_id_exist(self, user_id):
        cur=self.conn.cursor()
        cur.execute("SELECT user_id FROM \"user\" WHERE user_id =  (%s)", (user_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 是否存在某本书
    def book_id_exist(self, store_id, book_id):
        cur=self.conn.cursor()
        cur.execute("SELECT book_id FROM \"store\" WHERE store_id = (%s) AND book_id = (%s)", (store_id, book_id))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 是否存在某家店铺
    def store_id_exist(self, store_id):
        cur=self.conn.cursor()
        cur.execute("SELECT store_id FROM \"user_store\" WHERE store_id =  (%s) ", (store_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 检查店铺和用户的所属关系
    def user_store_exist(self, user_id, store_id):
        cur=self.conn.cursor()
        cur.execute("SELECT * FROM \"user_store\" WHERE store_id =  (%s) AND user_id= (%s) ", (store_id, user_id))
        row =cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 是否存在某个订单
    def order_id_exist(self,order_id):
        cur=self.conn.cursor()
        cur.execute("select * from \"new_order\" where order_id=(%s)",(order_id,))
        row=cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 某订单付款位是否已经置为1
    def pay_flag_set(self,order_id):
        cur=self.conn.cursor()
        cur.execute("select * from \"new_order\" where order_id=(%s) and pay=1",(order_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 某家店铺是否未上架过新书
    def store_book_empty(self, store_id):
        cur = self.conn.cursor()
        cur.execute("SELECT store_id FROM \"store\" WHERE store_id =  (%s) ", (store_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    # 检查此订单是否由此用户下单
    def buyer_order_exist(self,user_id,order_id):
        cur=self.conn.cursor()
        cur.execute("select * from \"new_order\" where order_id=(%s) and user_id=(%s)",(order_id,user_id,))
        row=cur.fetchone()
        if row is None:
            return False
        else:
            return True

    def deliver_flag_set(self,order_id):
        cur=self.conn.cursor()
        cur.execute("select * from \"new_order\" where order_id=(%s) and deliver=1",(order_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

    def return_flag_set(self,order_id):
        cur = self.conn.cursor()
        cur.execute("select * from \"new_order\" where order_id=(%s) and return=1", (order_id,))
        row = cur.fetchone()
        cur.close()
        if row is None:
            return False
        else:
            return True

