from pages.login_page import LoginPage


class LoginFlow:
    def __init__(self, page, base_url):
        self.login_page = LoginPage(page, base_url)

    def do_login(self, username, password):
        self.login_page.login(username, password)
