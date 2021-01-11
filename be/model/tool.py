import logging
import psycopg2

def cancel_order_tool(conn,order_id):
    cursor=conn.cursor()
    cursor.execute("select store_id from \"new_order\" where order_id=(%s)", (order_id,))

    logging.log(logging.CRITICAL, "*****"+order_id+"*******")
    store_id = cursor.fetchone()[0]
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
