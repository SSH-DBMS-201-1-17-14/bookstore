import os
import sqlite3 as sqlite
import random
import base64
import simplejson as json
from be.model import db_conn

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


class BookDB(db_conn.DBConn):
    table:str
    def __init__(self, large: bool = False):
        db_conn.DBConn.__init__(self)
        if large:
            self.table="book_lx"
        else:
            self.table="book_info"
        # parent_path = os.path.dirname(os.path.dirname(__file__))
        # self.db_s = os.path.join(parent_path, "data/book.db")
        # self.db_l = os.path.join(parent_path, "data/book_lx.db")
        # if large:
        #     self.book_db = self.db_l
        # else:
        #     self.book_db = self.db_s

    def get_book_count(self):
        # conn = sqlite.connect(self.book_db)
        cursor=self.conn.cursor()
        query="SELECT count(id) FROM "+self.table
        cursor.execute(query)
        # cursor.execute(
        #     "SELECT count(id) FROM \"(%s)\"",(self.table))
        row = cursor.fetchone()
        return row[0]

    def get_book_info(self, start, size) -> [Book]:
        books = []
        # conn = sqlite.connect(self.book_db)
        cursor = self.conn.cursor()
        query="SELECT id, title, author, publisher, original_title, " +"translator, pub_year, pages, price, currency_unit, binding, " +"isbn, author_intro, book_intro, content, tags FROM "+self.table+" ORDER BY id LIMIT "+str(size)+" OFFSET " + str(start)
        cursor.execute(query)
        # cursor.execute(
        #     "SELECT id, title, author, "
        #     "publisher, original_title, "
        #     "translator, pub_year, pages, "
        #     "price, currency_unit, binding, "
        #     "isbn, author_intro, book_intro, "
        #     "content, tags, picture FROM "
        #     " ORDER BY id LIMIT(%s) OFFSET  (%s)", (size, start))
        for row in cursor:
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

            # picture = row[16]
            picture=None
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


