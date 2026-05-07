# 自动化测试框架知识文档

## 一、项目架构

```
f:\topse_test\
├── conftest.py           # pytest 全局 fixture（浏览器、base_url）
├── pytest.ini            # pytest 配置（插件、参数、标记）
├── requirements.txt      # Python 依赖
├── .gitignore            # Git 忽略规则
├── Jenkinsfile           # CI 流水线（待写）
├── data/                 # 测试数据层
│   └── test_data.py      #   数据类，存放账号/资产/授权参数
├── pages/                # 页面对象层（Page Object Model）
│   ├── base_page.py      #   基类，封装通用操作
│   ├── login_page.py     #   登录页
│   └── devops_page.py    #   运维模块（资产+授权+运维资产）
├── flows/                # 业务流程层
│   ├── login_flow.py     #   登录流程
│   ├── yunwei_flow.py    #   运维完整流程
│   └── cleanup.py        #   清理流程
├── utils/                # 工具层
│   ├── logger.py         #   日志工具
│   └── compare.py        #   截图像素对比
├── tests/                # 测试用例
│   └── test_yunwei.py    #   主测试
├── logs/                 # 日志输出（git 忽略）
└── reports/              # 报告 + 截图（git 忽略）
    ├── screenshots/      #   运维截图 + 对比差异图
    ├── allure-results/   #   Allure 报告源数据
    └── report.html       #   HTML 报告
```

### 分层职责

| 层 | 职责 | 不做什么 |
|----|------|----------|
| **pages** | 封装页面元素的 locator 和单步操作 | 不含业务流程逻辑 |
| **flows** | 编排多步骤业务，调用 pages | 不直接操作 page |
| **data** | 存放测试数据 | 不含任何逻辑 |
| **utils** | 工具函数（日志、截图对比） | 不含业务逻辑 |
| **tests** | pytest 用例，调用 flows | 不直接操作 pages |

### 调用关系

```
tests → flows → pages → page (Playwright)
  ↓       ↓
data    utils
```

---

## 二、Playwright 定位方法（重点）

本项目使用的 Playwright 定位策略，按推荐优先级排列：

### 2.1 通过 placeholder 定位

```python
page.get_by_placeholder("请输入用户名").fill("admin")
```

适用场景：input 元素有 placeholder 属性时优先使用，最稳定。

### 2.2 通过 role + name 定位

```python
page.get_by_role("button", name="登录").click()
page.get_by_role("textbox", name="名称").fill("test")
page.get_by_role("textbox", name="请选择用户").click()
page.get_by_role("table").get_by_title("删除").click()
```

适用场景：按钮、文本框、表格等语义化元素，Playwright 推荐的首要方式。

### 2.3 通过 CSS ID 定位

```python
page.locator("#name").fill("test")
page.locator("#category").select_option("Linux")
page.locator("#assetType").select_option("CentOS")
page.locator("#ip").fill("192.168.3.56")
page.locator("#accForm").get_by_title("新建").click()
```

适用场景：元素有唯一 ID 时，精确高效。

### 2.4 通过文本定位

```python
page.get_by_text("账号配置").click()
page.get_by_text("新建运维授权").click()
page.get_by_text("SSH").click()
```

适用场景：按钮、链接、标签等文字唯一的情况。注意若同一页面多次出现同文本，需加 `.nth()`。

### 2.5 通过 nth() 处理重复文本

```python
page.get_by_text("test").nth(1).click()   # 点第二个"test"
page.get_by_text("1").nth(1).click()      # 点第二个"1"
```

注意：`.nth(0)` 是第一个，`.nth(1)` 是第二个。这种方式不够稳定，若页面结构变化可能点到错误元素。

### 2.6 通过属性选择器定位

```python
page.locator("span.tree-name[title='admin']").click()
page.locator("div:nth-child(3) > .tree-center > .tree-centerHood > div > .tree-name").first.click()
```

适用场景：树节点、特定结构的元素。

### 2.7 通过 title + role 组合

```python
page.get_by_title("WEB").get_by_role("img").click()
page.locator("#accForm").get_by_title("新建").click()
```

适用场景：嵌套结构中精确定位。

### 2.8 popup 弹窗处理

```python
with self.page.expect_popup() as popup_info:
    self.page.get_by_title("WEB").get_by_role("img").click()
popup = popup_info.value
popup.wait_for_load_state("networkidle")
```

适用场景：点击按钮打开新窗口（如运维终端弹窗）。

### 2.9 截图

```python
# 全页面截图
page.screenshot(path="reports/screenshot.png")

# 指定区域截图（clip 参数：x, y, width, height）
popup.screenshot(path="path.png", clip={"x": 0, "y": 0, "width": 960, "height": 540})
```

### 2.10 表单操作

```python
# fill — 输入文本
page.locator("#name").fill("test")

# select_option — 下拉选择
page.locator("#category").select_option("Linux")
```

---

## 三、等待策略

### 3.1 wait_for_load_state

```python
page.wait_for_load_state("networkidle")
```

最常用，等待网络请求完成。在 navigate 后自动调用。

### 3.2 wait_for_timeout

```python
page.wait_for_timeout(3000)   # 等待 3 秒
```

仅在动画、树节点展开、弹窗渲染等必须等待的场景使用。已封装为 `BasePage.wait()`。

### 3.3 wait_for（显式等待元素状态）

```python
btn = page.locator("#accForm").get_by_title("新建")
btn.wait_for(state="visible", timeout=10000)
btn.click()
```

比硬等更好，等待特定元素达到可见/可点击状态。

---

## 四、Pytest 用法

### 4.1 fixture（核心概念）

fixture 是 pytest 的依赖注入机制。用 `@pytest.fixture` 定义，用例通过参数名声明即可获取：

```python
# conftest.py
@pytest.fixture(scope="session")
def base_url():
    return "https://192.168.3.56"

# test_yunwei.py
def test_full_flow(self, page, base_url):
    # page 来自 pytest-playwright
    # base_url 来自 conftest.py
    ...
```

scope 说明：
| scope | 含义 |
|-------|------|
| function | 每个用例独立（默认） |
| class | 每个类共享 |
| module | 每个文件共享 |
| session | 整个测试会话共享 |

### 4.2 pytest.ini 配置

```ini
[pytest]
testpaths = tests              # 用例目录
python_files = test_*.py       # 文件匹配规则
addopts = -v                   # 默认命令行参数
    --html=reports/report.html
    --self-contained-html
    --alluredir=reports/allure-results
    --base-url https://192.168.3.56
markers =
    smoke: 冒烟测试
    yunwei: 运维资产相关测试
```

### 4.3 mark 标记

```python
@pytest.mark.yunwei
def test_full_flow(self, page, base_url):
    ...
```

运行时按标记筛选：
```bash
pytest -m yunwei          # 只跑 yunwei 标记的用例
pytest -m "not slow"      # 跳过 slow 标记的用例
```

### 4.4 运行方式

```bash
# 基础运行
pytest tests/test_yunwei.py -v

# 有头模式（看到浏览器）
pytest tests/test_yunwei.py -v --headed

# 生成 HTML 报告
pytest tests/test_yunwei.py -v --html=reports/report.html --self-contained-html

# 生成 Allure 报告
pytest tests/test_yunwei.py -v --alluredir=reports/allure-results
allure serve reports/allure-results

# 单个文件调试
pytest tests/test_yunwei.py -v -s   # -s 显示 print 输出
```

---

## 五、所用插件

| 插件 | 用途 | 关键能力 |
|------|------|----------|
| **pytest-playwright** | 浏览器自动化 | 自动提供 `page`/`browser`/`context` fixture，无需手动 launch/close |
| **pytest-html** | HTML 报告 | `--html` 生成可视化报告，`--self-contained-html` 离线可看 |
| **allure-pytest** | Allure 报告 | `--alluredir` 生成 Allure 数据，`allure serve` 查看精美报告 |
| **pytest-base-url** | 基础 URL | `--base-url` 设置全局基础地址（pytest-playwright 的依赖） |

---

## 六、Git 用法

### 6.1 常用命令

```bash
# 查看状态（改了什么）
git status

# 暂存所有改动
git add -A

# 暂存特定文件
git add pages/devops_page.py

# 查看暂存区内容
git diff --cached --stat

# 提交
git commit -m "类型: 描述"

# 推送
git push

# 查看提交历史
git log --oneline
```

### 6.2 提交信息规范

```bash
feat: 新功能
fix: 修复 bug
refactor: 重构（不改变功能）
chore: 杂项（配置、依赖等）
docs: 文档
```

### 6.3 .gitignore 规则

```
reports/       # 报告和截图不提交
logs/          # 日志不提交
.pytest_cache/ # pytest 缓存不提交
__pycache__/   # Python 编译缓存不提交
.claude/       # Claude 本地配置不提交
```

### 6.4 首次配置

```bash
git init
git config user.name "xxx"
git config user.email "xxx@xxx.com"
git remote add origin https://github.com/xxx/xxx.git
git push -u origin master
```

---

## 七、封装逻辑

### 7.1 BasePage Fluent API

所有 action 方法返回 `self`，支持链式调用：

```python
def click_button(self, name):
    self.page.get_by_role("button", name=name).click()
    return self   # 返回 self 实现链式
```

调用时：
```python
(self.devops
    .nav_to_asset()
    .click_new()
    .fill_asset_form(...)
    .click_create_asset_btn())
```

### 7.2 Page → Flow → Test 三层分离

```
Test                  Flow                  Page
配置数据 + 断言   →   编排步骤   →   定位元素 + 单步操作
不操作浏览器          不操作 locator         不含业务逻辑
```

示例：
```python
# Page 层：封装单个操作
class DevopsPage(BasePage):
    def click_new(self):
        return self.click_button("新建")

# Flow 层：编排多步操作
class YunweiFlow:
    def create_asset_with_account(self, asset, account):
        self.devops.nav_to_asset().click_new().fill_asset_form(...)

# Test 层：配置数据 + 断言
class TestYunwei:
    def test_full_flow(self, page, base_url):
        yunwei.create_asset_with_account(AssetData(), AccountData())
        assert matched, "截图对比失败"
```

### 7.3 清理模式

- **前置清理**：用例开始前清掉残留数据（避免上次失败遗留数据影响本次）
- **后置清理**：用例结束后清掉本次产生的数据（保持环境干净）
- **容错**：`count() == 0` 时跳过，不因"数据不存在"而报错

### 7.4 日志模式

```python
from utils.logger import get_logger
logger = get_logger(__name__)

logger.info("1/4 登录")
logger.info("删除授权: test")
logger.warning("授权不存在，跳过")
```

日志自动输出到控制台 + `logs/test_YYYYMMDD.log` 文件。每个模块独立 logger，通过 `__name__` 标识来源。

### 7.5 截图对比模式

```python
# 1. 截取实际画面
yunwei.access_host("reports/screenshots/web_ssh_actual.png")

# 2. 与基准图对比（像素级，阈值 80%）
matched, similarity, diff_path = compare_images(
    actual_path="reports/screenshots/web_ssh_actual.png",
    expected_path="data/baselines/web_ssh_baseline.png"
)

# 3. 断言
assert matched, f"截图对比不匹配: similarity={similarity:.2%}"
```

首次运行后，将 `actual.png` 复制为 `baseline.png` 即建立基准。

---

## 八、常见问题

### Q1: 元素找到了但不可见？

Playwright 的 `click()` 要求元素 visible + enabled + stable。若元素在 DOM 中但被遮挡/隐藏，会报 Timeout。

解决方法：
1. 加大等待时间
2. `scroll_into_view_if_needed()` 滚动到可见区域
3. 检查上层是否有遮罩（dialog、loading 等）

### Q2: pytest.ini 的 addopts 和命令行参数冲突？

命令行参数优先级更高。`addopts` 适合放默认参数，偶尔需要改的（如 `--headed`）放命令行。

### Q3: conftest.py 的 fixture 被覆盖了？

pytest 的 fixture 覆盖规则：就近原则。conftest.py 层级越靠近测试文件优先级越高。

### Q4: git 提交时忘记 .gitignore 导致生过大文件？

在 `.gitignore` 加规则后，已追踪的文件需先 `git rm --cached` 移除：

```bash
git rm --cached -r reports/
git add .gitignore
git commit -m "chore: ignore reports"
```
