import jwt
import time
import logging
from be.model import error
from be.model import db_conn
import psycopg2

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }

def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    # return encoded.decode("utf-8")
    return encoded

# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }

def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded


class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except (Exception, psycopg2.DatabaseError) as error:
            logging.error(error)
            return False

        # try:
        #     if db_token != token:
        #         return False
        #     jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
        #     ts = jwt_text["timestamp"]
        #     if ts is not None:
        #         now = time.time()
        #         if self.token_lifetime > now - ts >= 0:
        #             return True
        # except jwt.exceptions.InvalidSignatureError as e:
        #     logging.error(str(e))
        #     return False

    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            cursor=self.conn.cursor()
            cursor.execute(
                "INSERT into \"user\"(user_id, password, balance, token, terminal) "
                "VALUES (%s, %s, %s, %s, %s)",
                (user_id, password, 0, token, terminal))
            self.conn.commit()
        except (Exception, psycopg2.DatabaseError):
            return error.error_exist_user_id(user_id)
        cursor.close()
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        cursor=self.conn.cursor()
        cursor.execute("SELECT token from \"user\" where user_id=%s", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return error.error_authorization_fail()
        db_token = row[0]
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        cursor.close()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT password from \"user\" where user_id=%s", (user_id,))
        row = cursor.fetchone()
        if row is None:
            return error.error_authorization_fail()

        if password != row[0]:
            return error.error_authorization_fail()
        cursor.close()
        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" set token= %s , terminal = %s where user_id = %s",
                (token, terminal, user_id), )
            if cursor.rowcount == 0:
                return error.error_authorization_fail() + ("", )
            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" SET token = %s, terminal = %s WHERE user_id=%s",
                (dummy_token, terminal, user_id), )
            if cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message
            cursor = self.conn.cursor()
            cursor.execute("DELETE from \"user\" where user_id=%s", (user_id,))
            if cursor.rowcount == 1:
                self.conn.commit()
            else:
                return error.error_authorization_fail()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE \"user\" set password = %s, token= %s , terminal = %s where user_id = %s",
                (new_password, token, terminal, user_id), )
            if cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

