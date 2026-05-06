import pytest
from data.test_data import AssetData, AccountData, AuthorizeData, LoginData
from flows.login_flow import LoginFlow
from flows.yunwei_flow import YunweiFlow


class TestYunwei:

    @pytest.mark.yunwei
    def test_full_flow(self, page, base_url):
        """完整运维资产测试：登录 → 创建资产 → 添加授权 → 运维资产"""
        login = LoginFlow(page, base_url)
        yunwei = YunweiFlow(page, base_url)

        login.do_login(LoginData.USERNAME, LoginData.PASSWORD)
        yunwei.run_full_flow(AssetData(), AccountData(), AuthorizeData())
