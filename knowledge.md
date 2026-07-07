# 自动化测试框架知识文档

## 一、项目架构

```
f:\topse_test\
├── conftest.py           # pytest 全局 fixture（浏览器、base_url）
├── pytest.ini            # pytest 配置（插件、参数、标记）
├── requirements.txt      # Python 依赖
├── .gitignore            # Git 忽略规则
├── Jenkinsfile           # CI 流水线（Pipeline as Code）
├── data/                 # 测试数据层
│   ├── config.py         #   环境配置（凭据从环境变量读取，默认值兜底）
│   └── test_data.py      #   数据类，存放账号/资产/授权参数
├── pages/                # 页面对象层（Page Object Model）
│   ├── base_page.py      #   基类，封装通用操作（Fluent API）
│   ├── login_page.py     #   登录页
│   └── devops_page.py    #   运维模块（资产+授权+运维资产）
├── flows/                # 业务流程层
│   ├── login_flow.py     #   登录流程
│   ├── yunwei_flow.py    #   运维完整流程
│   └── cleanup.py        #   清理流程（删除资产/授权）
├── utils/                # 工具层
│   ├── logger.py         #   日志工具（控制台 + 文件双写）
│   ├── compare.py        #   截图像素对比
│   └── helper.py         #   等待工具函数
├── tests/                # 测试用例
│   └── test_yunwei.py    #   主测试（当前：登录→清理→创建资产）
├── logs/                 # 日志输出（git 忽略）
└── reports/              # 报告 + 截图（git 忽略）
    ├── screenshots/      #   运维截图 + 对比差异图
    ├── allure-results/   #   Allure JSON 数据
    ├── allure-report/    #   Allure 静态 HTML 报告
    └── report.html       #   pytest-html 报告
```

### 分层职责

| 层 | 职责 | 不做什么 |
|----|------|----------|
| **pages** | 封装页面元素的 locator 和单步操作 | 不含业务流程逻辑 |
| **flows** | 编排多步骤业务，调用 pages | 不直接操作 page |
| **data** | 存放测试数据和环境配置 | 不含任何逻辑 |
| **utils** | 工具函数（日志、截图对比） | 不含业务逻辑 |
| **tests** | pytest 用例，调用 flows，写断言 | 不直接操作 pages |

### 调用关系

```
tests → flows → pages → page (Playwright)
  ↓       ↓
data    utils
```

---

## 二、凭据管理

### 2.1 环境配置模式（data/config.py）

```python
import os

BASE_URL = os.getenv("TOPSEC_BASE_URL", "https://192.168.3.56")
LOGIN_USERNAME = os.getenv("TOPSEC_USERNAME", "admin")
LOGIN_PASSWORD = os.getenv("TOPSEC_PASSWORD", "1")
```

设计要点：
- `os.getenv("变量名", "默认值")` → 环境变量优先，默认值兜底
- 本地开发不用设任何东西直接跑
- Jenkins 通过 `environment {}` 块注入环境变量
- 环境变量名前缀 `TOPSEC_` 避免和系统变量冲突

### 2.2 下游消费者

```
data/config.py（单一入口）
     ↙            ↘
conftest.py      test_data.py
(base_url)       (LoginData)
```

---

## 三、Playwright 定位方法

按推荐优先级排列：

### 3.1 通过 placeholder 定位

```python
page.get_by_placeholder("请输入用户名").fill("admin")
```

最稳定。input 有 placeholder 属性时优先使用。

### 3.2 通过 role + name 定位

```python
page.get_by_role("button", name="登录").click()
page.get_by_role("textbox", name="请选择用户").click()
page.get_by_role("table").get_by_title("删除").click()
```

Playwright 官方推荐的首要方式。按钮、文本框、表格等语义化元素。

### 3.3 通过 CSS ID 定位

```python
page.locator("#name").fill("test")
page.locator("#category").select_option("Linux")
```

元素有唯一 ID 时精确高效。

### 3.4 通过文本定位

```python
page.get_by_text("账号配置").click()
page.get_by_text("新建运维授权").click()
page.get_by_text("SSH").click()
```

文字唯一时用。同一页面多次出现需加 `.nth()`。

### 3.5 通过 nth() 处理重复文本

```python
page.get_by_text("test").nth(1).click()   # 点第二个"test"
page.get_by_text("1").nth(1).click()      # 点第二个"1"
```

不够稳定，页面结构变化可能点错元素。**尽量避免**。

### 3.6 通过属性选择器定位

```python
page.locator("span.tree-name[title='admin']").click()
```

树节点、特定属性的元素。

### 3.7 通过 title + role 组合

```python
page.get_by_title("WEB").get_by_role("img").click()
page.locator("#accForm").get_by_title("新建").click()
```

嵌套结构中精确定位。

### 3.8 popup 弹窗处理

```python
with self.page.expect_popup() as popup_info:
    self.page.get_by_title("WEB").get_by_role("img").click()
popup = popup_info.value
popup.wait_for_load_state("networkidle")
```

点击打开新窗口时使用。`popup_info.value` 是新窗口的 page 对象。

### 3.9 截图

```python
page.screenshot(path="path.png")                                    # 全页
popup.screenshot(path="path.png", clip={"x":0,"y":0,"w":960,"h":540}) # 区域
```

### 3.10 表单操作

```python
page.locator("#name").fill("test")              # 输入
page.locator("#category").select_option("Linux") # 下拉
```

---

## 四、等待策略

### 4.1 wait_for_load_state

```python
page.wait_for_load_state("networkidle")
```

等待网络请求完成。navigate 后自动调用，最常用。

### 4.2 wait_for_timeout

```python
page.wait_for_timeout(3000)     # 等待 3 秒
```

仅在动画、树节点展开、弹窗渲染等无法用网络判断的场景使用。已封装为 `BasePage.wait()`。

### 4.3 wait_for（显式等待元素状态）

```python
btn = page.locator("#accForm").get_by_title("新建")
btn.wait_for(state="visible", timeout=10000)
```

等待元素达到特定状态。比硬等更好，但 `state="visible"` 对天生 hidden 的元素无效。

### 4.4 隐藏元素的处理方案

部分 DOM 元素天生是 hidden 状态（如 `<i>` 图标），`wait_for("visible")` 会一直超时。解法：

```python
# 方案 1：只等 DOM 挂载，force 点击
btn.wait_for(state="attached", timeout=10000)
btn.click(force=True)

# 方案 2：JS 直接触发事件，完全绕过 Playwright 检查
btn.evaluate("el => el.click()")

# 方案 3：dispatch_event 派发原生事件
btn.dispatch_event("click")
```

---

## 五、Pytest 用法

### 5.1 fixture 依赖注入

```python
# conftest.py — 定义
@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

# test_yunwei.py — 注入
def test_full_flow(self, page, base_url):
    # page   ← 来自 pytest-playwright 插件
    # base_url ← 来自 conftest.py
    ...
```

| scope | 含义 |
|-------|------|
| function | 每个用例独立（默认） |
| class | 每个类共享 |
| module | 每个文件共享 |
| session | 整个测试会话共享 |

**就近原则**：同名 fixture 以离测试文件最近的 conftest.py 为准。

### 5.2 pytest.ini 配置（当前）

```ini
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --junitxml=reports/junit.xml --base-url https://192.168.3.56
markers =
    smoke: 冒烟测试
    yunwei: 运维资产相关测试
```

`--junitxml` 生成 JUnit 格式，Jenkins 需要它画测试趋势图。

### 5.3 mark 标记

```python
@pytest.mark.yunwei
def test_full_flow(self, page, base_url):
    ...
```

```bash
pytest -m yunwei          # 只跑 yunwei 标记
pytest -m "not slow"      # 跳过 slow 标记
```

### 5.4 运行方式

```bash
# 基础运行
pytest tests/test_yunwei.py -v

# 有头模式（看到浏览器）
pytest tests/test_yunwei.py -v --headed

# 生成 HTML + Allure + JUnit 报告
pytest tests/test_yunwei.py -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --junitxml=reports/junit.xml

# 查看 Allure 报告
allure generate reports/allure-results -o reports/allure-report --clean
# 然后浏览器打开 reports/allure-report/index.html

# 调试（显示 print 输出）
pytest tests/test_yunwei.py -v -s
```

---

## 六、插件体系

| 插件 | 用途 | 关键能力 |
|------|------|----------|
| **pytest-playwright** | 浏览器自动化 | 自动提供 `page` fixture，无需手动 launch/close |
| **pytest-html** | HTML 报告 | `--self-contained-html` 单文件离线可看 |
| **allure-pytest** | Allure 报告 | JSON 数据 → `allure generate` → 可视化报告 |
| **pytest-base-url** | 基础 URL | `--base-url`设置，pytest-playwright 的依赖 |

Allure 查看链路：
```
pytest 运行                allure generate              allure serve
  → allure-results/*.json    → allure-report/index.html   → http://localhost
```

---

## 七、Jenkins CI/CD

### 7.1 环境

| 项 | 值 |
|------|-----|
| Jenkins 版本 | 2.555.1 LTS，Windows MSI 安装 |
| 访问地址 | `http://localhost:8080` |
| 凭据 | admin / Talent@123 |
| 工作区 | `F:/topse_test`（本地目录，不走 Git 拉取） |
| 安装的插件 | Git、Allure、HTML Publisher、JUnit、Pipeline |

### 7.2 两个 Job

| Job | 类型 | 配置方式 |
|-----|------|----------|
| `topse-test` | Freestyle | UI 配置，Execute Windows batch command |
| `topse-pipeline` | Pipeline | Pipeline script 粘贴 Jenkinsfile 内容 |

### 7.3 Jenkinsfile 核心写法

```groovy
pipeline {
    agent any
    environment { ... }           // 注入凭据和 URL
    stages {
        stage('Setup') {
            steps {
                dir('F:/topse_test') {      // 关键：切换到项目目录
                    bat '... pip install ...'
                    bat '... playwright install ...'
                }
            }
        }
        stage('Test') {
            steps {
                dir('F:/topse_test') {
                    bat '... pytest --headed ...'
                }
            }
            post {
                always {
                    dir('F:/topse_test') {
                        junit 'reports/junit.xml'           // JUnit 趋势图
                        archiveArtifacts '...'               // 归档截图和日志
                    }
                }
            }
        }
    }
}
```

### 7.4 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| pip/python 找不到 | Jenkins SYSTEM 账户无用户 PATH | 使用完整绝对路径 `C:\Users\...\python.exe` |
| Git SSL 握手失败 | SYSTEM 账户网络限制 | Freestyle 和 Pipeline 都改用本地目录 `F:/topse_test` |
| 报告归档 404 | Pipeline 工作区与项目目录不同 | 所有步骤包在 `dir('F:/topse_test')` 里 |
| `\t` 被解析为 Tab | Batch 中 `\topse_test` 的 `\t` | 改用正斜杠 `F:/topse_test` |
| SYSTEM 无桌面 | Jenkins 作为 Windows 服务 | 改服务登录账户为当前用户才能看浏览器 |

### 7.5 当前测试流程

```
Jenkins Build Now
  → Setup: pip install + playwright install chromium
  → Test: pytest tests/test_yunwei.py --headed
  → Publish JUnit + Archive screenshots/logs
```

测试内容：登录 → 清理残留数据 → 创建资产 + 配置 SSH 账号

---

## 八、Git 用法

### 8.1 日常提交流程

```bash
git status                    # 看改了什么
git add -A                    # 暂存所有
git diff --cached --stat      # 确认暂存内容
git commit -m "前缀: 描述"    # 提交
git push                      # 推送
```

### 8.2 撤销操作

```bash
git checkout .                              # 全部回到最后提交状态
git checkout <commit> -- <文件路径>          # 只恢复某个文件到指定提交
git checkout <commit> -- a.py b.py          # 一次恢复多个文件
```

**区别：**
- `git checkout .` → 所有文件回到 HEAD
- `git checkout 79be3a6 -- a.py` → 只 a.py 回到 79be3a6，其他文件不动

### 8.3 初始化

```bash
git init
git config user.name "xxx"
git config user.email "xxx@xx.com"
git remote add origin <url>
git push -u origin master
```

### 8.4 提交信息前缀

```
feat:    新功能
fix:     修复 bug
refactor: 重构
chore:   配置、依赖
docs:    文档
```

### 8.5 .gitignore

```
reports/
logs/
.pytest_cache/
__pycache__/
.claude/
```

---

## 九、封装思想

### 9.1 Fluent API（链式调用）

```python
class BasePage:
    def click_button(self, name):
        self.page.get_by_role("button", name=name).click()
        return self      # 返回 self
```

调用：
```python
(self.devops
    .nav_to_asset()
    .click_new()
    .fill_asset_form(...)
    .click_create_asset_btn())
```

### 9.2 Page → Flow → Test 三层职责

| 层 | 职责 | 粒度 |
|----|------|------|
| Page | 封装页面元素定位和单步操作 | `click_new()` |
| Flow | 编排多步业务，穿插等待 | `create_asset_with_account()` |
| Test | 配置数据 + 断言 + 流程控制 | `test_full_flow()` |

### 9.3 清理模式

- **前置清理**：用例开始前清残留（避免上次失败遗留影响本次）
- **后置清理**：用例结束后清本次数据（保持环境干净）
- **容错**：`count() == 0` 跳过，不因"数据不存在"报错

### 9.4 日志模式

```python
from utils.logger import get_logger
logger = get_logger(__name__)

logger.info("1/5 登录")
logger.warning("授权 test 不存在，跳过")
```

自动输出到控制台 + `logs/test_YYYYMMDD.log`。每个模块通过 `__name__` 标识来源。

### 9.5 截图对比模式

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

首次运行后，将 `actual.png` 复制为 `baseline.png` 建立基准。

---

## 十、常见问题

### Q1: 元素找到了但不可见？

Playwright 的 `click()` 要求 visible + enabled + stable。

解决方法：加大等待 → `scroll_into_view_if_needed()` → `evaluate("el => el.click()")`

### Q2: 为什么先登录再清理？

清理操作需要登录态（session cookie），所以顺序是 登录 → 清理 → 创建。

### Q3: Freestyle vs Pipeline 怎么选？

- Freestyle：UI 配置，简单直观，适合快速实验
- Pipeline：Jenkinsfile 控制，可版本管理，适合团队协作

### Q4: SYSTEM 账户执行和本地执行有什么区别？

SYSTEM 账户没有用户 PATH、没有桌面、网络环境不同。pytest-playwright 默认无头模式，SYSTEM 帐户跑无头需要确保页面元素在无头模式下正常渲染。
