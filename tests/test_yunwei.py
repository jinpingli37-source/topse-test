import pytest
from data.test_data import AssetData, AccountData, AuthorizeData, LoginData
from flows.login_flow import LoginFlow
from flows.yunwei_flow import YunweiFlow
from flows.cleanup import CleanupFlow
from utils.compare import compare_images
from utils.logger import get_logger

logger = get_logger(__name__)

SCREENSHOT_PATH = "reports/screenshots/web_ssh_actual.png"
BASELINE_PATH = "reports/screenshots/web_ssh_baseline.png"


class TestYunwei:

    @pytest.mark.yunwei
    def test_full_flow(self, page, base_url):
        """完整运维资产测试：清理 → 登录 → 创建资产 → 添加授权 → 运维资产 → 截图对比 → 清理"""
        login = LoginFlow(page, base_url)
        yunwei = YunweiFlow(page, base_url)
        cleanup = CleanupFlow(page, base_url)

        logger.info("========== 前置清理残留数据 ==========")
        cleanup.cleanup_all()

        logger.info("========== 开始运维资产完整流程 ==========")

        logger.info("1/4 登录")
        login.do_login(LoginData.USERNAME, LoginData.PASSWORD)

        logger.info("2/4 创建资产 + 配置账号")
        yunwei.create_asset_with_account(AssetData(), AccountData())

        logger.info("3/4 添加授权")
        yunwei.add_authorization(AuthorizeData())

        logger.info("4/4 运维资产 + 截图")
        yunwei.access_host(SCREENSHOT_PATH)

        logger.info("========== 截图对比 ==========")
        matched, similarity, diff_path = compare_images(SCREENSHOT_PATH, BASELINE_PATH)
        logger.info(f"对比结果: matched={matched}, similarity={similarity:.2%}")
        assert matched, f"截图对比不匹配: similarity={similarity:.2%}, diff={diff_path}"

        logger.info("========== 后置清理本次数据 ==========")
        cleanup.cleanup_all()

        logger.info("========== 流程全部通过 ==========")
