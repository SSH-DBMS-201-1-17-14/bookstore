from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
from be.model.tool import cancel_order_tool

def delete_order(order_id):
    database = "bookstore"
    host = "localhost"
    user = "postgres"
    password = "shypostgredql"
    conn=psycopg2.connect(host=host, database=database, user=user, password=password)
    cancel_order_tool(conn,order_id)
    conn.close()

class GlobalScheduler():
    def __init__(self,scheduler):
        self.scheduler=scheduler

scheduler = BackgroundScheduler()
instance_GlobalScheduler=GlobalScheduler(scheduler)
scheduler.start()


