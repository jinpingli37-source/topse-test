from playwright.sync_api import sync_playwright
import time

"""
============================================================
运维资产
============================================================
"""


def launch():
    """复用：启动浏览器并打开页面"""
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto("https://192.168.3.56", timeout=30000)
    return p, browser, context, page




p, browser, context, page = launch()
try:
#1. 登录
    page.get_by_placeholder("请输入用户名").fill("admin")
    page.get_by_placeholder("请输入密码").fill("1")
    page.get_by_role("button", name="登录").click()
    page.wait_for_load_state("networkidle")
    print("→ 登录成功")
    time.sleep(2)

    
# 新建资产
    page.goto("https://192.168.3.56/devops_asset")
    page.wait_for_load_state("networkidle")

    #12 点击新建按钮
    page.get_by_role("button", name="新建").click()
    page.get_by_role("textbox", name="请选择部门，不选则为当前登录用户所在部门中最高部门").click()
    page.locator("div:nth-child(3) > .tree-center > .tree-centerHood > div > .tree-name").first.click()
    page.get_by_text("基本信息").first.click()
    #输入资产名称
    # page.get_by_placeholder("请输入中英文、数字、或英文.:_-()符号  最大50字符").fill("test")
    page.locator("#name").fill("test")
    page.locator("#category").select_option("Linux")
    page.locator("#assetType").select_option("CentOS")
    page.locator("#ip").fill("192.168.3.56")
    page.get_by_role("button", name="创建资产").click()
    time.sleep(5)
    
    page.get_by_text("账号配置").click()
    page.locator("#accForm").get_by_title("新建").click()
    time.sleep(1)
    page.locator('#accountProtocol').select_option('SSH')
    
    page.locator("#accountName").fill("1")
    page.locator("#accPassword").fill("1")
    page.locator("#accPassword2").fill("1")
    page.get_by_text("创建账号").click()
    time.sleep(5)
    page.get_by_text("保存").click()
    time.sleep(5)
 #添加授权
    page.goto("https://192.168.3.56/devops_authorize")
    page.get_by_text("新建").click()
    page.get_by_role("textbox", name="名称").fill("test")
    page.get_by_role("textbox", name="请选择用户").click()
    page.locator("span.tree-name[title='admin']").click()
    # page.locator('div').filter(has_text="admin").click
    # getByRole('textbox', { name: '请选择用户' }).click()
    time.sleep(3)
    page.get_by_text("新建运维授权").click()
    time.sleep(3)

    page.get_by_role("textbox", name="请选择账号").click()
    time.sleep(3)
    
    page.get_by_text("test").nth(1).click();
    time.sleep(3)
    page.get_by_text("1").nth(1).click();
    page.get_by_text("新建运维授权").click()
    time.sleep(3)
   
    page.get_by_role("button", name="确定").click()
   

#运维资产
    time.sleep(3)
    page.goto("https://192.168.3.56/devops_hosts")
    # page.get_by_title("SSH").click
    page.get_by_text("SSH").click()
    # page.getByText('SSH').click()
    page.get_by_title("WEB").get_by_role("img").click()

    time.sleep(50)
    
    

   
    time.sleep(577)



except Exception as e:
    print(f"→ 失败: {e}")
finally:
    browser.close()
    p.stop()
