"""清理流程：先删授权，再删资产"""
from utils.logger import get_logger

logger = get_logger(__name__)


class CleanupFlow:
    def __init__(self, page, base_url):
        self.page = page
        self.base_url = base_url

    def _navigate(self, path):
        self.page.goto(f"{self.base_url}{path}")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def delete_authorization(self, auth_name="test"):
        """删除指定授权，不存在则跳过"""
        logger.info(f"删除授权: {auth_name}")
        self._navigate("/devops_authorize")
        self.page.wait_for_timeout(2000)

        delete_btn = self.page.get_by_role("table").get_by_title("删除")
        if delete_btn.count() == 0:
            logger.info(f"授权 {auth_name} 不存在，跳过")
            return

        delete_btn.click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("button", name="确定").click()
        self.page.wait_for_timeout(2000)
        logger.info(f"授权 {auth_name} 已删除")

    def delete_asset(self, asset_name="test"):
        """删除指定资产，不存在则跳过"""
        logger.info(f"删除资产: {asset_name}")
        self._navigate("/devops_asset")
        self.page.wait_for_timeout(2000)

        delete_btn = self.page.get_by_role("table").get_by_title("删除")
        if delete_btn.count() == 0:
            logger.info(f"资产 {asset_name} 不存在，跳过")
            return

        delete_btn.click()
        self.page.wait_for_timeout(1000)
        self.page.get_by_role("button", name="确定").click()
        self.page.wait_for_timeout(2000)
        logger.info(f"资产 {asset_name} 已删除")

    def cleanup_all(self, auth_name="test", asset_name="test"):
        """先删授权再删资产"""
        logger.info("========== 开始清理 ==========")
        self.delete_authorization(auth_name)
        self.delete_asset(asset_name)
        logger.info("========== 清理完成 ==========")
