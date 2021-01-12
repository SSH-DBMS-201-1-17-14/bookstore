from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from be.model.tool import cancel_order_tool

# def delete_order(conn,order_id):
#     database = "bookstore"
#     host = "localhost"
#     user = "postgres"
#     password = "shypostgredql"
#     conn=psycopg2.connect(host=host, database=database, user=user, password=password)
#     cancel_order_tool(conn,order_id)
#     conn.close()

class GlobalScheduler():
    def __init__(self,scheduler):
        self.scheduler=scheduler
        self.database = "bookstore"
        self.host = "localhost"
        self.user = "postgres"
        self.password = "shypostgredql"
        self.conn = psycopg2.connect(host=self.host, database=self.database, user=self.user, password=self.password)
    def delete_order(self,order_id):
        cancel_order_tool(self.conn, order_id)

global instance_GlobalScheduler

# scheduler = BackgroundScheduler()
# instance_GlobalScheduler=GlobalScheduler(scheduler)
# scheduler.start()


