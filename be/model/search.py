import psycopg2
import logging
from be.model import db_conn
from fe.access import book
from fe import conf
import jieba
import re
from math import ceil

# 对题目、目录、内容进行分词，构建倒排索引表
class Search(db_conn.DBConn):
    def __init__(self,search_info:str,page:int, book_id:list):
        db_conn.DBConn.__init__(self)
        # 创建类 BookDB
        self.book_db = book.BookDB(conf.Use_Large_DB)
        self.search_info = search_info
        self.page = page
        self.book_id = book_id

    # 对一个字符串进行分词，获得词项对应的列表
    def split_user_input(self, string):
        new_string = re.sub(r'[^\w\s]', '', string)  # 只保留中文和英文字符，去掉符号
        terms = jieba.lcut(new_string)  # 分词 得到分词列表
        # 去除为空的
        while ' ' in terms:
            terms.remove(' ')
        while '\n' in terms:
            terms.remove('\n')
        return terms

    # 封装为一个函数 返回两个字典：倒排索引表（字典）和每个文档的词频（字典）
    def inverted_index_dics(self, dic):
        idx = list(dic.keys())
        new_dic = {}
        freq_dic = {}
        for x in idx:
            string = dic[x]
            terms = self.split_user_input(string)
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

    # 根据关键词列表获得 book_id 对应 其包含关键词个数 的字典
    def find_ids(self, terms, index_dic):  # ['三毛','的','三毛']
        term_in_id = {}
        for term in terms:
            if term in index_dic.keys():
                value_ids = index_dic[term]
                for id in value_ids:
                    if id in term_in_id.keys():
                        term_in_id[id] = term_in_id[id] + 1
                    else:
                        term_in_id[id] = 1
        return term_in_id

    # 传入 book_id 对应 其包含关键词个数 的字典以及 book_id 对应 分词后词项长度 的字典
    # 对每个 book_id 的重要程度打分并且降序排序，返回对应页数的 book_id 列表
    def sort_id_importance_pagek(self, term_in_id, freqdic, pagek):
        importance_score = {}
        # 对id
        for id_num in term_in_id.keys():
            word_num = freqdic[id_num]  # 得到id对应字符串本身分词个数
            score = term_in_id[id_num] / word_num * 1.0  # 得分
            importance_score[id_num] = score  # 得到所有排序
        importance_score = sorted(importance_score.items(), key=lambda d: d[1], reverse=True)  # 由分数的从高到低进行排序
        # 因为最后一页不一定能显10个，判断一下能分几页
        id_n = len(importance_score)
        # print('.........id_n......... = %d'%id_n)
        pages_num = ceil(id_n / 10 * 1.0)  # 共有pages_num
        # print('.........pages_num......... = %d'%pages_num)
        # 输入页码超过最大页数,输出空列表
        if pagek > pages_num:
            return []
        # 输入页码小于等于最大页数
        # 分页 第k页：下标（从0开始）  ： 10*(k-1) 到 k*10-1
        start = 10 * (pagek - 1)
        end = pagek * 10 - 1
        # 如果是最后一页,不一定能输10个，只能输出到最后一个
        if pagek == pages_num:
            end = id_n - 1
        id_l = []  # 最后输出的id
        for i in range(start, end + 1):
            id_l.append(importance_score[i][0])
        return id_l


    # 返回按 title 搜索后打分的 bookid
    def search_bookid_title(self):
        dict_title = {}  # 创建分词输入的 title 字典
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM {} WHERE id IN {} ".format(self.book_db.table, tuple(self.book_id))
            cursor.execute(query)
            for row in cursor:
                id = row[0]
                dict_title[id] = row[1]
            # 构建倒排索引表
            dict_split_title, freq_split_title = self.inverted_index_dics(dict_title)
            # 对用户的搜索进行分词，获得关键词列表
            keyword_term = self.split_user_input(self.search_info)
            # 获得 book_id 对应 其包含关键词个数 的字典
            book_id_keyword_count = self.find_ids(keyword_term, dict_split_title)
            # 获得对应页数的 book_id
            book_list = self.sort_id_importance_pagek(book_id_keyword_count, freq_split_title, self.page)
            return book_list
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            self.conn.rollback()

    # 返回按 book_into 搜索后打分的 bookid
    def search_bookid_book_intro(self):
        dict_book_intro = {}  # 创建分词输入的 book_intro 字典
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM {} WHERE id IN {} ".format(self.book_db.table, tuple(self.book_id))
            cursor.execute(query)
            for row in cursor:
                id = row[0]
                dict_book_intro[id] = row[1]
            # 构建倒排索引表
            dict_split_title, freq_split_title = self.inverted_index_dics(dict_book_intro)
            # 对用户的搜索进行分词，获得关键词列表
            keyword_term = self.split_user_input(self.search_info)
            # 获得 book_id 对应 其包含关键词个数 的字典
            book_id_keyword_count = self.find_ids(keyword_term, dict_split_title)
            # 获得对应页数的 book_id
            book_list = self.sort_id_importance_pagek(book_id_keyword_count, freq_split_title, self.page)
            return book_list
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            self.conn.rollback()

    # 返回按 content 搜索后打分的 bookid
    def search_bookid_content(self):
        dict_content = {}  # 创建分词输入的 title 字典
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM {} WHERE id IN {} ".format(self.book_db.table, tuple(self.book_id))
            cursor.execute(query)
            for row in cursor:
                id = row[0]
                dict_content[id] = row[1]
            # 构建倒排索引表
            dict_split_title, freq_split_title = self.inverted_index_dics(dict_content)
            # 对用户的搜索进行分词，获得关键词列表
            keyword_term = self.split_user_input(self.search_info)
            # 获得 book_id 对应 其包含关键词个数 的字典
            book_id_keyword_count = self.find_ids(keyword_term, dict_split_title)
            # 获得对应页数的 book_id
            book_list = self.sort_id_importance_pagek(book_id_keyword_count, freq_split_title, self.page)
            return book_list
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            self.conn.rollback()

    # 返回包含所有 tag 的 bookid

    def search_bookid_tag(self, tag_search):
        dict_tag = {}
        book_list = []
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM {} WHERE id IN {} ".format(self.book_db.table, tuple(self.book_id))
            cursor.execute(query)
            for row in cursor:
                id = row[0]
                tag = row[15]
                for search_tag in tag_search:
                    if search_tag in tag:
                        if id in dict_tag.keys():
                            dict_tag[id] = dict_tag[id] + 1
                        else:
                            dict_tag[id] = 1
            for the_book_id in dict_tag.keys():
                if dict_tag[the_book_id] == len(tag_search):
                    book_list.append(the_book_id)
            id_n = len(book_list)
            # print('.........id_n......... = %d'%id_n)
            pages_num = ceil(id_n / 10 * 1.0)  # 共有pages_num
            # print('.........pages_num......... = %d'%pages_num)
            # 输入页码超过最大页数,输出空列表
            if self.page > pages_num:
                return []
            # 输入页码小于等于最大页数
            # 分页 第k页：下标（从0开始）  ： 10*(k-1) 到 k*10-1
            start = 10 * (self.page - 1)
            end = self.page * 10 - 1
            # 如果是最后一页,不一定能输10个，只能输出到最后一个
            if self.page == pages_num:
                end = id_n - 1
            id_l = []  # 最后输出的id
            for i in range(start, end + 1):
                id_l.append(book_list[i][0])
            return id_l
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            self.conn.rollback()


