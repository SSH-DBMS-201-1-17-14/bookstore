import logging
import psycopg2

def cancel_order_tool(conn,order_id):
    cursor=conn.cursor()
    cursor.execute("select store_id from \"new_order\" where order_id=(%s)", (order_id,))
    row=cursor.fetchone()
    if row is None:
        return
    # logging.log(logging.CRITICAL, "*****"+order_id+"*******")
    store_id = row[0]
    cursor.execute("select book_id,count from \"new_order_detail\" where order_id=(%s)", (order_id,))
    rows = cursor.fetchall()
    for row in rows:
        book_id = row[0]
        count = row[1]
        cursor.execute("UPDATE \"store\" SET stock_level = stock_level + (%s) "
                       "WHERE store_id = (%s) AND book_id = (%s)",
                       (count, store_id, book_id,))
    cursor.execute("DELETE FROM \"new_order\" WHERE order_id =(%s)", (order_id,))
    cursor.execute("DELETE FROM \"new_order_detail\" where order_id = (%s)", (order_id,))
    conn.commit()

def auto_admmit_return(conn,order_id,buyer_id):
    cursor = conn.cursor()
    cursor.execute("select store_id from \"new_order\" where order_id=(%s)", (order_id,))
    row = cursor.fetchone()
    if row is None:
        return
    store_id=row[0]
    cursor.execute("SELECT book_id, count, price FROM \"new_order_detail\" WHERE order_id = (%s)", (order_id,))
    total_price = 0
    rows = cursor.fetchall()
    for row in rows:
        count = row[1]
        price = row[2]
        total_price = total_price + price * count

    cursor.execute("SELECT user_id from \"user_store\" where store_id= (%s)", (store_id,))
    seller_id = cursor.fetchone()[0]

    cursor.execute("UPDATE \"user\" SET balance = balance - (%s)"
                   "WHERE user_id = (%s) AND balance >= (%s)",
                   (total_price, seller_id, total_price))

    cursor.execute("UPDATE \"user\" SET balance = balance + (%s)"
                   "WHERE user_id = (%s)",
                   (total_price, buyer_id,))

    cancel_order_tool(conn, order_id)
    cursor.execute("UPDATE \"new_order\" SET refund=1"
                   "WHERE order_id = (%s)",
                   (order_id,))
    conn.commit()
