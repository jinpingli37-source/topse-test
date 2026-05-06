from pages.base_page import BasePage


class DevopsPage(BasePage):

    # ==================== 资产管理 ====================

    def nav_to_asset(self):
        return self.navigate("/devops_asset")

    def click_new(self):
        return self.click_button("新建")

    def select_department(self):
        self.page.get_by_role("textbox", name="请选择部门，不选则为当前登录用户所在部门中最高部门").click()
        return self.select_tree_first_node()

    def fill_asset_form(self, name, category, asset_type, ip):
        self.fill_by_id("name", name)
        self.select_by_id("category", category)
        self.select_by_id("assetType", asset_type)
        self.fill_by_id("ip", ip)
        return self

    def click_create_asset_btn(self):
        return self.click_button("创建资产")

    # ==================== 账号配置 ====================

    def switch_to_account_tab(self):
        return self.click_text("账号配置")

    def click_new_account(self):
        self.page.locator("#accForm").get_by_title("新建").click()
        return self

    def fill_account_form(self, protocol, name, password):
        self.select_by_id("accountProtocol", protocol)
        self.fill_by_id("accountName", name)
        self.fill_by_id("accPassword", password)
        self.fill_by_id("accPassword2", password)
        return self

    def click_create_account_btn(self):
        return self.click_text("创建账号")

    def click_save(self):
        return self.click_text("保存")

    # ==================== 授权管理 ====================

    def nav_to_authorize(self):
        return self.navigate("/devops_authorize")

    def fill_auth_name(self, name):
        self.page.get_by_role("textbox", name="名称").fill(name)
        return self

    def select_user_from_tree(self, username):
        self.page.get_by_role("textbox", name="请选择用户").click()
        self.page.wait_for_timeout(3000)
        self.page.locator(f"span.tree-name[title='{username}']").click()
        return self

    def click_create_auth(self):
        return self.click_text("新建运维授权")

    def select_account_in_tree(self, account_name, account_user):
        self.page.get_by_role("textbox", name="请选择账号").click()
        self.page.wait_for_timeout(3000)
        self.page.get_by_text(account_name).nth(1).click()
        self.page.wait_for_timeout(3000)
        self.page.get_by_text(account_user).nth(1).click()
        return self

    def click_confirm(self):
        return self.click_button("确定")

    # ==================== 运维资产 ====================

    def nav_to_hosts(self):
        return self.navigate("/devops_hosts")

    def click_ssh(self):
        return self.click_text("SSH")

    def click_web_icon(self):
        self.page.get_by_title("WEB").get_by_role("img").click()
        return self
