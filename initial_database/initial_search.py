import random
import base64
import psycopg2
import logging
from bookstore.be.model import db_conn
from bookstore.fe.access import book
from bookstore.fe import conf
import bookstore.be.model.store as store
import jieba
import re

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

# 对题目、目录、内容进行分词，构建倒排索引表
class BookSplit(db_conn.DBConn):
    def __init__(self,global_store: bool = True,store_id:int = -1):
        # 创建实例init_database
        store.init_database("aaa")
        db_conn.DBConn.__init__(self)
        # 创建类 BookDB
        self.book_db = book.BookDB(conf.Use_Large_DB)
        # 创建类 Book
        self.book = book.Book()
        # 判断是否进行全局搜索
        self.global_store = global_store
        # 若进行全局搜索，store_id设置为 -1
        self.store_id = store_id

    def get_book_info(self):
        global book_id
        try:
            dict_title = {}    # 创建分词输入的 title 字典
            dict_book_intro = {}  # 创建分词输入的 book_intro 字典
            dict_content = {}  # 创建分词输入的 content 字典
            cursor = self.conn.cursor()
            start = 0
            size = self.book_db.get_book_count()
            if self.global_store:
                # 读取全部的表 book_info 信息
                query = "SELECT id, title, author, publisher, original_title, " + "translator, pub_year, pages, price, currency_unit, binding, " + "isbn, author_intro, book_intro, content, tags FROM " + self.book_db.table + " ORDER BY id LIMIT " + str(
                    size) + " OFFSET " + str(start)
                cursor.execute(query)
            else:
                # 获得店铺 id 对应的 book_id
                query_bookid = "SELECT store_id, book_id FROM \"store\" WHERE id = %s",(self.store_id,)
                cursor.execute(query_bookid)
                book_id = []
                for row in cursor:
                    book_id.append(row[1])
                query = "SELECT id, title, author, publisher, original_title, " + "translator, pub_year, pages, price, currency_unit, binding, " + "isbn, author_intro, book_intro, content, tags FROM " + self.book_db.table + " WHERE id IN %(book_id)s ORDER BY id LIMIT " + str(
                    size) + " OFFSET " + str(start)
                cursor.execute(query,{'book_id':tuple(book_id),})
            # cursor.execute(
            #     "SELECT id, title, author, "
            #     "publisher, original_title, "
            #     "translator, pub_year, pages, "
            #     "price, currency_unit, binding, "
            #     "isbn, author_intro, book_intro, "
            #     "content, tags, picture FROM "
            #     " ORDER BY id LIMIT(%s) OFFSET  (%s)", (size, start))
            for row in cursor:
                id = row[0]
                dict_title[id] = row[1]
                dict_book_intro[id] = row[13]
                dict_content[id] = row[14]
            return dict_title,dict_book_intro,dict_content
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            self.conn.rollback()

    # 封装为一个函数 返回两个字典：倒排索引表（字典）和每个文档的词频（字典）
    def inverted_index_dics(self,dic):
        idx = list(dic.keys())
        new_dic = {}
        freq_dic = {}
        for x in idx:
            string = dic[x]
            new_string = re.sub(r'[^\w\s]', '', string)
            terms = jieba.lcut(new_string)
            while ' ' in terms:
                terms.remove(' ')
            while '\n' in terms:
                terms.remove('\n')
            new_dic[x] = terms
            freq_dic[x] = len(terms)
        idx = list(new_dic.keys())
        term_id_list = []  # map
        for x in idx:
            term_list = new_dic[x]
            for term in term_list:
                term_id_list.append([term, x])
        index_dic = {}  # reduce
        for x in term_id_list:
            # x[0]:词          x[1]:出现的文档id
            if x[0] not in index_dic:
                index_dic[x[0]] = [x[1]]
            else:
                if x[1] not in index_dic[x[0]]:
                    index_dic[x[0]].append(x[1])
        return index_dic, freq_dic


    def inverted_index(self):
        dict_title, dict_book_intro, dict_content = self.get_book_info()
        #print(dict_content)
        # 构建倒排索引表
        dict_split_title,freq_split_title = self.inverted_index_dics(dict_title)
        dict_split_book_intro,freq_split_book_intro = self.inverted_index_dics(dict_book_intro)
        dict_split_content,freq_split_content = self.inverted_index_dics(dict_content)
        try:
            if self.global_store:
                # 由于全局搜索的倒排索引表不会改变，为了避免每次搜索重新构建倒排索引表，决定将其存入数据库中
                cursor = self.conn.cursor()
                # 存储 title 的倒排索引
                cursor.execute('''CREATE TABLE IF NOT EXISTS "book_split_title"
                                   (keyword TEXT PRIMARY KEY,
                                    book_id TEXT)''')
                # 存储 book_intro 的倒排索引
                cursor.execute('''CREATE TABLE IF NOT EXISTS "book_split_book_intro"
                                   (keyword TEXT PRIMARY KEY,
                                    book_id TEXT)''')
                # 存储 content 的倒排索引
                cursor.execute('''CREATE TABLE IF NOT EXISTS "book_split_content"
                                    (keyword TEXT PRIMARY KEY,
                                    book_id TEXT)''')
                # 存储 title、book_intro、content 的包含关键词个数
                cursor.execute('''CREATE TABLE IF NOT EXISTS "keyword_count"
                                   (book_id TEXT PRIMARY KEY,
                                    title_count INTEGER,
                                    book_intro_count INTEGER,
                                    content_count INTEGER)''')
                self.conn.commit()
                print("Table created successfully")
                # 导入数据
                # title 分词
                for items in dict_split_title.items():
                    cursor.execute(
                        "INSERT INTO book_split_title(keyword,book_id) "
                        "VALUES(%s,%s)",
                        (items[0],items[1]))
                    self.conn.commit()
                # book_intro 分词
                for items in dict_split_book_intro.items():
                    cursor.execute(
                        "INSERT INTO book_split_book_intro(keyword,book_id) "
                        "VALUES(%s,%s)",
                        (items[0], items[1]))
                    self.conn.commit()
                # content 分词
                for items in dict_split_content.items():
                    cursor.execute(
                        "INSERT INTO book_split_content(keyword,book_id) "
                        "VALUES(%s,%s)",
                        (items[0],items[1]))
                    self.conn.commit()
                for items in freq_split_title.items():
                    book_id = items[0]
                    cursor.execute(
                        "INSERT INTO keyword_count(book_id,title_count,book_intro_count,content_count) "
                        "VALUES(%s,%s,%s,%s)",
                        (book_id,freq_split_title[book_id],freq_split_book_intro[book_id],freq_split_content[book_id]))
                    self.conn.commit()
                return "ok"
            else:
                # 若根据店铺进行搜索，由于每个店铺构建一个倒排索引表数量过多，选择每次检索，根据店铺 id 构建一次倒排索引表
                return dict_split_title, dict_split_book_intro, dict_split_content
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            logging.error(error)
            self.conn.rollback()
        finally:
            if self.conn is not None:
                self.conn.close()


if __name__ == '__main__':
    bookdb = BookSplit()
    # 对于全局索引进行初始表格构建以及数据插入
    bookdb.inverted_index()
