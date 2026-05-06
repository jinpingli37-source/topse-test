from pages.devops_page import DevopsPage


class YunweiFlow:
    def __init__(self, page, base_url):
        self.devops = DevopsPage(page, base_url)

    def create_asset_with_account(self, asset, account):
        (self.devops
            .nav_to_asset()
            .click_new()
            .select_department()
            .fill_asset_form(asset.NAME, asset.CATEGORY, asset.ASSET_TYPE, asset.IP)
            .click_create_asset_btn())
        self.devops.page.wait_for_timeout(5000)

        self.devops.switch_to_account_tab()
        self.devops.page.wait_for_timeout(2000)
        self.devops.click_new_account()
        self.devops.page.wait_for_timeout(1000)

        (self.devops
            .fill_account_form(account.PROTOCOL, account.NAME, account.PASSWORD)
            .click_create_account_btn())
        self.devops.page.wait_for_timeout(5000)

        self.devops.click_save()
        self.devops.page.wait_for_timeout(5000)

    def add_authorization(self, auth):
        (self.devops
            .nav_to_authorize()
            .click_new()
            .fill_auth_name(auth.NAME)
            .select_user_from_tree(auth.USER))
        self.devops.page.wait_for_timeout(3000)

        self.devops.click_create_auth()
        self.devops.page.wait_for_timeout(3000)

        (self.devops
            .select_account_in_tree(auth.ACCOUNT_NAME, auth.ACCOUNT_USER))
        self.devops.page.wait_for_timeout(3000)

        self.devops.click_create_auth()
        self.devops.page.wait_for_timeout(3000)

        self.devops.click_confirm()

    def access_host(self, screenshot_path=None):
        self.devops.nav_to_hosts()
        self.devops.page.wait_for_timeout(3000)
        self.devops.click_ssh()
        self.devops.open_web_ssh(screenshot_path)
        self.devops.page.wait_for_timeout(50000)

    def run_full_flow(self, asset, account, auth, screenshot_path=None):
        self.create_asset_with_account(asset, account)
        self.add_authorization(auth)
        self.access_host(screenshot_path)
