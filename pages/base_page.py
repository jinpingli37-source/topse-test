class BasePage:
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def navigate(self, path):
        self.page.goto(f"{self.base_url}{path}")
        self.page.wait_for_load_state("networkidle")
        return self

    def click_button(self, name):
        self.page.get_by_role("button", name=name).click()
        return self

    def click_text(self, text):
        self.page.get_by_text(text).click()
        return self

    def fill_by_placeholder(self, placeholder, value):
        self.page.get_by_placeholder(placeholder).fill(value)
        return self

    def fill_by_id(self, id_, value):
        self.page.locator(f"#{id_}").fill(value)
        return self

    def select_by_id(self, id_, option):
        self.page.locator(f"#{id_}").select_option(option)
        return self

    def select_tree_first_node(self):
        """打开部门/用户树下拉后，选第一个节点并关闭下拉"""
        self.page.locator(
            "div:nth-child(3) > .tree-center > .tree-centerHood > div > .tree-name"
        ).first.click()
        self.click_text("基本信息")
        return self
