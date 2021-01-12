from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from be.model.tool import cancel_order_tool,auto_admmit_return

# def delete_order(conn,order_id):
#     database = "bookstore"
#     host = "localhost"
#     user = "postgres"
#     password = "shypostgredql"
#     conn=psycopg2.connect(host=host, database=database, user=user, password=password)
#     cancel_order_tool(conn,order_id)
#     conn.close()

class GlobalAutoCancelOrder():
    def __init__(self,scheduler):
        self.scheduler=scheduler
        self.database = "bookstore"
        self.host = "localhost"
        self.user = "postgres"
        self.password = "shypostgredql"
        self.conn = psycopg2.connect(host=self.host, database=self.database, user=self.user, password=self.password)
    def delete_order(self,order_id):
        cancel_order_tool(self.conn, order_id)

class GlobalAutoAdmmitReturn():
    def __init__(self,scheduler):
        self.scheduler=scheduler
        self.database = "bookstore"
        self.host = "localhost"
        self.user = "postgres"
        self.password = "shypostgredql"
        self.conn = psycopg2.connect(host=self.host, database=self.database, user=self.user, password=self.password)
    def AutoAdmmitReturn(self, order_id,buyer_id):
            auto_admmit_return(self.conn, order_id,buyer_id)

global instance_GlobalAutoCancelOrder
global instance_AutoAdmmitReturn

# scheduler = BackgroundScheduler()
# instance_GlobalAutoCancelOrder=GlobalAutoCancelOrder(scheduler)
# scheduler.start()


