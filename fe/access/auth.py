import requests
from urllib.parse import urljoin


class Auth:
    def __init__(self, url_prefix):
        self.url_prefix = urljoin(url_prefix, "auth/")

    def login(self, user_id: str, password: str, terminal: str) -> (int, str):
        json = {"user_id": user_id, "password": password, "terminal": terminal}
        url = urljoin(self.url_prefix, "login")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("token")

    def register(
            self,
            user_id: str,
            password: str
    ) -> int:
        json = {
            "user_id": user_id,
            "password": password
        }
        url = urljoin(self.url_prefix, "register")
        r = requests.post(url, json=json)
        return r.status_code

    def password(self, user_id: str, old_password: str, new_password: str) -> int:
        json = {
            "user_id": user_id,
            "oldPassword": old_password,
            "newPassword": new_password,
        }
        url = urljoin(self.url_prefix, "password")
        r = requests.post(url, json=json)
        return r.status_code

    def logout(self, user_id: str, token: str) -> int:
        json = {"user_id": user_id}
        headers = {"token": token}
        url = urljoin(self.url_prefix, "logout")
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def unregister(self, user_id: str, password: str) -> int:
        json = {"user_id": user_id, "password": password}
        url = urljoin(self.url_prefix, "unregister")
        r = requests.post(url, json=json)
        return r.status_code

    def store_search_title(self, user_id: str, store_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "store_id": store_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "store_search_title")
        r = requests.post(url, json=json)
        return r.status_code

    def store_search_book_intro(self, user_id: str, store_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "store_id": store_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "store_search_book_intro")
        r = requests.post(url, json=json)
        return r.status_code

    def store_search_content(self, user_id: str, store_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "store_id": store_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "store_search_content")
        r = requests.post(url, json=json)
        return r.status_code

    def global_search_title(self, user_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "global_search_title")
        r = requests.post(url, json=json)
        return r.status_code

    def global_search_book_intro(self, user_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "global_search_book_intro")
        r = requests.post(url, json=json)
        return r.status_code

    def global_search_content(self, user_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "global_search_content")
        r = requests.post(url, json=json)
        return r.status_code


    def global_search_tag(self, user_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "search_info": search_info,
                "page": page}
        url = urljoin(self.url_prefix, "global_search_tag")
        r = requests.post(url, json=json)
        return r.status_code

    def store_search_tag(self, user_id: str, store_id: str, search_info: str, page: int) -> int:
        json = {"user_id": user_id,
                "search_info": search_info,
                "store_id": store_id,
                "page": page}
        url = urljoin(self.url_prefix, "store_search_tag")
        r = requests.post(url, json=json)
        return r.status_code

    def get_store_id(self, user_id: str,book_id: str) -> int:
        json = {"user_id": user_id,
                "book_id": book_id}
        url = urljoin(self.url_prefix, "get_store_id")
        r = requests.post(url, json=json)
        return r.status_code
