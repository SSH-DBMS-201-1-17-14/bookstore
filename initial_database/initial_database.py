import os
import sqlite3 as sqlite
import random
import base64
import psycopg2
import logging

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit:str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: [str]
    pictures: [bytes]

    def __init__(self):
        self.tags = []
        self.pictures = []

class BookPostgresql:
    def __init__(self, large: bool = False):
        parent_path = os.path.dirname(os.path.dirname(__file__))
        self.db_s = os.path.join(parent_path, "fe/data/book.db")
        self.db_l = os.path.join(parent_path, "fe/data/book_lx.db")
        if large:     # 选择导入大的还是小的数据数据库内容
            self.book_db = self.db_l
        else:
            self.book_db = self.db_s

    def get_book_count(self):
        # 连接数据库，获得书籍数目
        conn = sqlite.connect(self.book_db)
        cursor = conn.execute(
            "SELECT count(id) FROM book")
        row = cursor.fetchone()
        return row[0]

    def get_book_info(self, start, size) -> [Book]:
        books = []
        # 连接数据库，获得书籍信息
        conn = sqlite.connect(self.book_db)
        cursor = conn.execute(
            "SELECT id, title, author, "
            "publisher, original_title, "
            "translator, pub_year, pages, "
            "price, currency_unit, binding, "
            "isbn, author_intro, book_intro, "
            "content, tags, picture FROM book ORDER BY id "
            "LIMIT ? OFFSET ?", (size, start))
        for row in cursor:
            # 对于每本书创建一个类book存储信息
            book = Book()
            book.id = row[0]
            book.title = row[1]
            book.author = row[2]
            book.publisher = row[3]
            book.original_title = row[4]
            book.translator = row[5]
            book.pub_year = row[6]
            book.pages = row[7]
            book.price = row[8]

            book.currency_unit = row[9]
            book.binding = row[10]
            book.isbn = row[11]
            book.author_intro = row[12]
            book.book_intro = row[13]
            book.content = row[14]
            tags = row[15]

            picture = row[16]
            # 处理数据信息
            for tag in tags.split("\n"):
                if tag.strip() != "":
                    book.tags.append(tag)
            for i in range(0, random.randint(0, 9)):
                if picture is not None:
                    encode_str = base64.b64encode(picture).decode('utf-8')
                    book.pictures.append(encode_str)
            books.append(book)
            # print(tags.decode('utf-8'))

            # print(book.tags, len(book.picture))
            # print(book)
            # print(tags)

        return books

    def postgresql_book_info(self):
        # 获得book.db中书本的信息
        start = 0
        book_count = self.get_book_count()
        whole_book_info = self.get_book_info(start,book_count)
        # 连接数据库并创建表格存放数据
        conn = psycopg2.connect(database="book", user="postgres", password="1234", host="localhost", port="5432")
        try:
            print ("Opened database successfully")
            cur = conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS "book_info"
                   (id TEXT PRIMARY KEY,
                   title  TEXT,
                   author TEXT,
                   publisher TEXT,
                   original_title TEXT,
                   translator TEXT,
                   pub_year TEXT,
                   pages INTEGER,
                   price INTEGER,
                   currency_unit TEXT,
                   binding TEXT,
                   isbn TEXT,
                   author_intro TEXT,
                   book_intro TEXT,
                   content TEXT,
                   tags TEXT,
                   picture BYTEA)''')
            conn.commit()
            print("Table created successfully")
            # 导入数据
            for one_book_info in whole_book_info:
                cur.execute(
                    "INSERT INTO book_info(id,title,author,publisher,original_title,translator,pub_year,pages,price,currency_unit,binding,isbn,author_intro,book_intro,content,tags) "
                    "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (one_book_info.id, one_book_info.title, one_book_info.author, one_book_info.publisher,
                     one_book_info.original_title,
                     one_book_info.translator, str(one_book_info.pub_year), one_book_info.pages, one_book_info.price,
                     one_book_info.currency_unit,
                     one_book_info.binding, one_book_info.isbn, one_book_info.author_intro, one_book_info.book_intro,
                     one_book_info.content,
                     one_book_info.tags))
                conn.commit()
            cur.close()
            return "ok"
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            conn.rollback()
        finally:
            if conn is not None:
                conn.close()


if __name__ == '__main__':
    bookdb=BookPostgresql(False)
    print(bookdb.get_book_count())
    bookdb.postgresql_book_info()

