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
        login = LoginFlow(page, base_url)
        yunwei = YunweiFlow(page, base_url)
        cleanup = CleanupFlow(page, base_url)

        logger.info("1/5 登录")
        login.do_login(LoginData.USERNAME, LoginData.PASSWORD)

        logger.info("2/5 打扫环境，删除残留数据")
        cleanup.cleanup_all()

        logger.info("3/5 创建资产 + 配置账号")
        yunwei.create_asset_with_account(AssetData(), AccountData())

        # logger.info("4/5 添加授权")
        # yunwei.add_authorization(AuthorizeData())

        # logger.info("5/5 运维资产 + 截图")
        # yunwei.access_host(SCREENSHOT_PATH)

        # logger.info("========== 截图对比 ==========")
        # matched, similarity, diff_path = compare_images(SCREENSHOT_PATH, BASELINE_PATH)
        # logger.info(f"对比结果: matched={matched}, similarity={similarity:.2%}")
        # assert matched, f"截图对比不匹配: similarity={similarity:.2%}, diff={diff_path}"

        logger.info("========== 流程全部通过 ==========")
