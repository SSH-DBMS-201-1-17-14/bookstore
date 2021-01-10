import logging
import os
import sqlite3 as sqlite
import psycopg2

class Store:
    database: str
    host:str
    user:str
    password:str

    def __init__(self,path):
        self.database="bookstore"
        self.host="localhost"
        self.user="postgres"
        self.password="shypostgredql"
        # self.database = os.path.join(db_path, "be.db")
        self.init_tables()

    def init_tables(self):
        """ create tables in the PostgreSQL database"""
        commands = (
            """ CREATE TABLE IF NOT EXISTS "user" (
                    user_id TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    balance INTEGER NOT NULL,
                    token TEXT, 
                    terminal TEXT
                    )
            """,
            """
            CREATE TABLE IF NOT EXISTS "user_store" (
                    user_id TEXT,
                    store_id TEXT,
                    PRIMARY KEY(user_id, store_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "store" (
                    store_id TEXT,
                    book_id TEXT,
                    book_info TEXT,
                    stock_level INTEGER,
                    PRIMARY KEY(store_id, book_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "new_order" (
                    order_id TEXT PRIMARY KEY, 
                    user_id TEXT, 
                    store_id TEXT,
                    pay INTEGER,
                    deliver INTEGER ,
                    receive INTEGER,
                    order_time FLOAT 
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS "new_order_detail"(
                    order_id TEXT, 
                    book_id TEXT,
                    count INTEGER,
                    price INTEGER,  
                    PRIMARY KEY(order_id, book_id)
            )
            """)
        conn = None
        try:
            # connect to the PostgreSQL server
            conn = psycopg2.connect(host=self.host,database=self.database,user=self.user,password=self.password)
            cursor = conn.cursor()
            # create table one by one
            for command in commands:
                cursor.execute(command)
            # close communication with the PostgreSQL database server
            cursor.close()
            # commit the changes
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            conn.rollback()
        finally:
            if conn is not None:
                conn.close()

    def get_db_conn(self):
        return psycopg2.connect(host=self.host,database=self.database,user=self.user,password=self.password)
        # return sqlite.connect(self.database)


database_instance: Store = None


def init_database(path):
    global database_instance
    database_instance = Store(path)


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn()

