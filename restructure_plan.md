# yunwei.py 改造为 pytest 分层架构 实施方案

## 一、改造前现状

`yunwei.py` 是一个线性 Playwright 脚本，问题包括：

- 没有测试框架（无 pytest/unittest）
- 没有分层设计，所有逻辑混在一个文件里
- 手动管理浏览器生命周期（`launch()` / `close()` / `stop()`）
- 大量 `time.sleep()` 硬等待，例如 `time.sleep(577)`
- 所有测试数据硬编码在脚本中

## 二、改造后目录结构

```
f:\topse_test\
├── Jenkinsfile               ← CI 流水线（后写）
├── conftest.py              ← pytest 全局 fixture
├── pytest.ini               ← pytest 配置
├── requirements.txt         ← 项目依赖
├── pages/                   ← 页面对象层 (Page Object Model)
│   ├── __init__.py
│   ├── base_page.py         ← 基类：公共行为
│   ├── login_page.py        ← 登录页
│   └── devops_page.py       ← 运维模块页（资产 + 授权 + 运维资产）
├── flows/                   ← 业务流程层
│   ├── __init__.py
│   ├── login_flow.py        ← 登录流程
│   ├── yunwei_flow.py       ← 运维完整流程（创建资产 + 添加授权 + 运维资产）
│   └── cleanup.py           ← 清理流程（删除资产/授权等，后写）
├── data/                    ← 测试数据层
│   ├── __init__.py
│   └── test_data.py         ← 测试数据
├── utils/                   ← 工具层
│   ├── __init__.py
│   └── helpers.py           ← 等待工具
├── log/                     ← 日志输出目录（运行后生成）
├── tests/                   ← 测试用例层
│   ├── __init__.py
│   └── test_yunwei.py       ← 主测试
└── reports/                 ← 报告输出目录（运行后生成）
    ├── picture/             ← 截图对比目录
    └── allure-results/      ← Allure 报告源数据
```

## 三、各层职责说明

| 层 | 职责 | 不做什么 |
|----|------|----------|
| **pages** | 封装页面元素的 locator 和单步操作（fill、click） | 不包含业务流程逻辑 |
| **flows** | 编排多步骤业务流程，调用 pages 完成复杂操作 | 不直接操作 page 元素 |
| **data** | 存放测试数据（账号、资产名、IP等） | 不包含任何逻辑 |
| **utils** | 提供工具函数（等待、截图等） | 不包含业务相关逻辑 |
| **tests** | 编写 pytest 测试用例，调用 flows 组装场景 | 不直接操作 pages |
| **conftest** | 全局 fixture：浏览器、page、data | — |

### 调用关系

```
tests  →  flows  →  pages  →  page (Playwright)
  ↓         ↓
 data     utils
```

- `tests` 调用 `flows`，可以自己调用 `data` 和 `utils`
- `flows` 调用 `pages`，可以自己调用 `data` 和 `utils`
- `pages` 只操作 Playwright page 对象，可以用 `utils`

## 四、各文件内容说明

### 1. `requirements.txt`

```
playwright
pytest
pytest-playwright
pytest-html
allure-pytest
```

### 2. `pytest.ini`

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results
markers =
    smoke: 冒烟测试
    yunwei: 运维资产相关测试
```

- `--self-contained-html` 让 HTML 报告单文件可离线查看
- `--alluredir` 指定 Allure 结果输出目录
- 查看 Allure 报告：`allure serve reports/allure-results`

### 3. `conftest.py`

利用 `pytest-playwright` 提供的 fixture，不再手动管理浏览器。

关键 fixture：

```
base_url           → "https://192.168.3.56"
browser_context_args → {"ignore_https_errors": True}  （忽略自签名证书）
page               → pytest-playwright 内置，自动创建/销毁
```

这样 tests 里直接用 `page` 参数即可，无需自己 `launch()` / `close()`。

### 4. `data/test_data.py`

```python
class LoginData:
    USERNAME = "admin"
    PASSWORD = "1"

class AssetData:
    NAME = "test"
    CATEGORY = "Linux"       # 对应下拉选项
    ASSET_TYPE = "CentOS"    # 对应下拉选项
    IP = "192.168.3.56"

class AccountData:
    PROTOCOL = "SSH"
    NAME = "1"
    PASSWORD = "1"

class AuthorizeData:
    NAME = "test"
    USER = "admin"
    ACCOUNT_NAME = "test"
    ACCOUNT_USER = "1"
```

### 5. `utils/helpers.py`

两个简单工具：

```
wait_network_idle(page, timeout)   → page.wait_for_load_state("networkidle")
short_wait(page, ms)               → page.wait_for_timeout(ms)，仅在必要时用
```

### 6. `pages/base_page.py` — 页面基类

```python
class BasePage:
    def __init__(self, page):
        self.page = page

    def navigate(self, path):           # 导航到页面 + 等待加载
        url = BASE_URL + path
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        return self

    def click_button(self, name):       # 按文本点击按钮
        self.page.get_by_role("button", name=name).click()
        return self

    def fill_by_placeholder(self, placeholder, value):  # 按 placeholder 填输入框
        self.page.get_by_placeholder(placeholder).fill(value)
        return self

    def fill_by_id(self, id_, value):   # 按 CSS id 填输入框
        self.page.locator(f"#{id_}").fill(value)
        return self

    def select_by_id(self, id_, option):  # 按 CSS id 选下拉
        self.page.locator(f"#{id_}").select_option(option)
        return self

    def click_text(self, text):         # 按可见文本点击
        self.page.get_by_text(text).click()
        return self
```

设计原则：
- 所有方法 `return self`，支持链式调用
- 封装常用 Playwright 操作，子类无需重复写

### 7. `pages/login_page.py`

```python
class LoginPage(BasePage):
    def login(self, username, password):
        self.fill_by_placeholder("请输入用户名", username)
        self.fill_by_placeholder("请输入密码", password)
        self.click_button("登录")
        self.page.wait_for_load_state("networkidle")
        return self
```

就一个方法，作为通用入口，后续其他用例也可复用。

### 8. `pages/devops_page.py` — 运维模块页（合并 3 个页面）

将资产管理、授权管理、运维资产三个模块的操作集中在同一个 page 对象中，因为它们是同一系统内连续关联的操作。

**A. 资产管理**
- `nav_to_asset()` → `/devops_asset`
- `click_new()` → 点"新建"
- `select_department_first()` → 打开部门树，选第一个节点，关闭下拉
- `fill_asset_form(name, category, asset_type, ip)` → 填名称、选类别/类型、填IP
- `click_create_asset_btn()` → 点"创建资产"

**B. 账号配置**
- `switch_to_account_tab()` → 点"账号配置"
- `click_new_account()` → 点 `#accForm` 里的新建
- `fill_account_form(protocol, name, password)` → 选协议、填名称密码
- `click_create_account_btn()` → 点"创建账号"
- `click_save()` → 点"保存"

**C. 授权管理**
- `nav_to_authorize()` → `/devops_authorize`
- `fill_auth_name(name)` → 填授权名称
- `select_user_from_tree(user)` → 展开用户树选 admin
- `click_create_auth()` → 点"新建运维授权"
- `select_account_in_tree(name, user)` → 选 test → 1
- `click_confirm()` → 点"确定"

**D. 运维资产**
- `nav_to_hosts()` → `/devops_hosts`
- `click_ssh()` → 点 SSH
- `click_web_icon()` → 点 WEB 图标

### 9. `flows/login_flow.py`

```python
class LoginFlow:
    def __init__(self, page):
        self.login_page = LoginPage(page)

    def do_login(self, username, password):
        self.login_page.login(username, password)
```

### 10. `flows/yunwei_flow.py` — 运维完整流程（合并 3 个流程）

```python
class YunweiFlow:
    def __init__(self, page):
        self.devops = DevopsPage(page)

    def create_asset_with_account(self, asset, account):
        """创建资产 + 配置账号"""
        (self.devops.nav_to_asset()
            .click_new()
            .select_department_first()
            .fill_asset_form(asset.NAME, asset.CATEGORY, asset.ASSET_TYPE, asset.IP)
            .click_create_asset_btn()
            .switch_to_account_tab()
            .click_new_account()
            .fill_account_form(account.PROTOCOL, account.NAME, account.PASSWORD)
            .click_create_account_btn()
            .click_save())

    def add_authorization(self, auth):
        """添加运维授权"""
        (self.devops.nav_to_authorize()
            .click_new()
            .fill_auth_name(auth.NAME)
            .select_user_from_tree(auth.USER)
            .click_create_auth()
            .select_account_in_tree(auth.ACCOUNT_NAME, auth.ACCOUNT_USER)
            .click_create_auth_btn()
            .click_confirm())

    def access_host(self):
        """运维资产操作 + 截图对比"""
        self.devops.nav_to_hosts().click_ssh().click_web_icon()
        # 截图对比（具体逻辑后续完善）
        self.devops.page.screenshot(path="reports/picture/host_access.png")

    def run_full_flow(self, asset, account, auth):
        """一键执行完整运维流程"""
        self.create_asset_with_account(asset, account)
        self.add_authorization(auth)
        self.access_host()
```

`run_full_flow()` 是给用例调用的顶层入口，也保留了分步方法方便单独测试。

### 11. `flows/cleanup.py` — 清理流程（后写）

```python
class CleanupFlow:
    def __init__(self, page):
        self.devops = DevopsPage(page)

    def delete_authorization(self, name): ...   # 删除指定授权
    def delete_asset(self, name): ...           # 删除指定资产
    def cleanup_all(self, asset_name, auth_name): ...  # 一键清理
```

具体实现和定位器待后续补充。"

### 12. `tests/test_yunwei.py`

```python
import pytest
from data.test_data import AssetData, AccountData, AuthorizeData, LoginData
from flows.login_flow import LoginFlow
from flows.yunwei_flow import YunweiFlow

class TestYunwei:

    def test_full_flow(self, page):
        """完整运维资产测试：登录 → 创建资产 → 添加授权 → 运维资产"""
        yunwei = YunweiFlow(page)

        LoginFlow(page).do_login(LoginData.USERNAME, LoginData.PASSWORD)
        yunwei.run_full_flow(AssetData(), AccountData(), AuthorizeData())
```

最简写法 — login 复用通用 flow，其余全部走 `YunweiFlow.run_full_flow()`。

## 五、改造前后对比

| 方面 | 改造前 | 改造后 |
|------|--------|--------|
| 浏览器管理 | 手动 launch / close | pytest-playwright 自动管理 |
| 等待方式 | `time.sleep(577)` | `wait_for_load_state`, `wait_for_timeout` |
| 测试数据 | 硬编码在脚本中 | 集中在 `data/test_data.py` |
| 代码复用 | 无，3个文件各自复制 `launch()` | Page Object 和 Flow 可复用 |
| 测试报告 | 无 | `reports/report.html` HTML 报告 |
| 可维护性 | 差，一处改动影响整个脚本 | 好，每个页面/流程独立文件 |

## 六、实施步骤

1. 创建目录结构 (`pages/`, `flows/`, `data/`, `utils/`, `tests/`, `log/`, `reports/picture/`)
2. 写 `requirements.txt` → 安装依赖
3. 写 `pytest.ini`
4. 写 `conftest.py`
5. 写 `utils/helpers.py`
6. 写 `data/test_data.py`
7. 写 `pages/`：`__init__.py` → `base_page.py` → `login_page.py` → `devops_page.py`
8. 写 `flows/`：`__init__.py` → `login_flow.py` → `yunwei_flow.py` → `cleanup.py`（后写）
9. 写 `tests/test_yunwei.py`
10. 运行 `pytest tests/test_yunwei.py -v --html=reports/report.html --self-contained-html` 验证

## 七、验证方法

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保 Playwright 浏览器已安装
playwright install chromium

# 3. 运行测试（有头模式，方便观察）
pytest tests/test_yunwei.py -v --headed

# 4. 运行测试（无头模式 + 生成报告）
pytest tests/test_yunwei.py -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results

# 5. 查看 HTML 报告
# 浏览器打开 f:\topse_test\reports\report.html

# 6. 查看 Allure 报告
allure serve reports/allure-results
```
