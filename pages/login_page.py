from pages.base_page import BasePage


class LoginPage(BasePage):
    def login(self, username, password):
        self.navigate("/")
        self.fill_by_placeholder("请输入用户名", username)
        self.fill_by_placeholder("请输入密码", password)
        self.click_button("登录")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)
        return self
