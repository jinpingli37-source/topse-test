# Jenkins CI/CD 集成改造说明

## 改造目的

将硬编码的凭据（密码、base_url）外部化为环境变量，方便 Jenkins 注入不同环境的配置，同时不影响本地开发体验（环境变量未设置时使用默认值）。

## 改动的文件

### 1. 新建 `data/config.py`

```python
import os

# 从环境变量读取配置，未设置时使用默认值
# Jenkins 通过 pipeline environment 注入这些变量
# 本地开发不需要设置，直接用默认值
BASE_URL = os.getenv("TOPSEC_BASE_URL", "https://192.168.3.56")
LOGIN_USERNAME = os.getenv("TOPSEC_USERNAME", "admin")
LOGIN_PASSWORD = os.getenv("TOPSEC_PASSWORD", "1")
```

**设计意图**：单一配置入口，所有凭据和 URL 集中管理。环境变量名加 `TOPSEC_` 前缀避免与系统变量冲突。

### 2. 改造 `conftest.py`

```python
# 改动前：硬编码
# @pytest.fixture(scope="session")
# def base_url():
#     return "https://192.168.3.56"

# 改动后：从 config 读取
import pytest
from data.config import BASE_URL  # ← 新增 import


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL  # ← 由环境变量控制
```

**设计意图**：conftest 的 `base_url` fixture 是 `pytest-playwright` 的集成点，这个值决定了浏览器启动后自动导航到哪个 URL。改为从 config 读取后，Jenkins 可以通过环境变量指向不同的测试服务器。

### 3. 改造 `data/test_data.py`

```python
# 改动前：硬编码
# class LoginData:
#     USERNAME = "admin"
#     PASSWORD = "1"

# 改动后：从 config 读取
from data.config import LOGIN_PASSWORD, LOGIN_USERNAME  # ← 新增 import


class LoginData:
    USERNAME = LOGIN_USERNAME  # ← 由环境变量控制
    PASSWORD = LOGIN_PASSWORD  # ← 由环境变量控制
```

**设计意图**：登录凭据不再写死在代码里。Jenkins 可以在 pipeline 中注入不同的用户名密码，也方便切换测试账号。

### 4. 改造 `pytest.ini`

```ini
# 改动前：
# addopts = -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --base-url https://192.168.3.56

# 改动后：
# — 去掉 --base-url（改为 Jenkinsfile 中通过环境变量注入）
# — 新增 --junitxml（生成 JUnit 格式报告，供 Jenkins 解析测试趋势）
addopts = -v --html=reports/report.html --self-contained-html --alluredir=reports/allure-results --junitxml=reports/junit.xml
```

**设计意图**：
- `--base-url` 从 `pytest.ini` 移除，因为它带环境属性（不同环境不同地址），不适合写死在配置文件中。改为 Jenkinsfile 中通过 `%TOPSEC_BASE_URL%` 动态注入。
- `--junitxml` 是 Jenkins 标准测试报告格式，用于生成测试趋势图（JUnit plugin 解析）。

### 5. 新建 `Jenkinsfile`

```groovy
pipeline {
    agent any                     // 在本机执行

    environment {                 // 通过环境变量注入配置
        TOPSEC_BASE_URL = 'https://192.168.3.56'
        TOPSEC_USERNAME = 'admin'
        TOPSEC_PASSWORD = '1'
    }

    stages {
        stage('Setup') {          // 第一步：装依赖 + 浏览器
            steps {
                bat 'pip install -r requirements.txt'
                bat 'playwright install chromium'
            }
        }

        stage('Test') {           // 第二步：运行测试
            steps {
                bat '''
                    python -m pytest tests/test_yunwei.py -v ^
                        --html=reports/report.html --self-contained-html ^
                        --alluredir=reports/allure-results ^
                        --junitxml=reports/junit.xml ^
                        --base-url %TOPSEC_BASE_URL%
                '''
            }
            post {
                always {          // 无论测试通过还是失败，都归档报告
                    junit 'reports/junit.xml'                    // JUnit 测试趋势
                    publishHTML([...])                            // HTML 报告
                    allure(results: [[path: 'reports/allure-results']])  // Allure 报告
                    archiveArtifacts 'reports/screenshots/**,logs/**.log' // 截图+日志
                }
            }
        }
    }
}
```

## 数据流

```
Jenkins environment {} 块
    ↓ 设置环境变量
TOPSEC_BASE_URL  TOPSEC_USERNAME  TOPSEC_PASSWORD
    ↓ os.getenv() 读取
data/config.py
    ↓ import
conftest.py（base_url fixture）
data/test_data.py（LoginData 类）
    ↓ 注入
pytest 测试用例
    ↓ 生成
reports/（HTML报告、Allure数据、JUnit XML、截图）
```

## 本地开发 vs Jenkins 运行

| 场景 | 环境变量来源 | 效果 |
|------|-------------|------|
| 本地 `pytest` | 未设置 → 使用默认值 | `admin/1` 登录 `192.168.3.56` |
| Jenkins 构建 | `environment {}` 注入 | 同上，但可以随时改值 |
| 本地模拟 Jenkins | `set TOPSEC_USERNAME=xxx` | 手动覆盖默认值 |

## 验证

```bash
# 1. 本地默认运行（使用默认值）
pytest tests/test_yunwei.py -v

# 2. 本地模拟 Jenkins 环境变量
set TOPSEC_BASE_URL=https://192.168.3.56
set TOPSEC_USERNAME=admin
set TOPSEC_PASSWORD=1
pytest tests/test_yunwei.py -v --html=reports/report.html --alluredir=reports/allure-results --junitxml=reports/junit.xml --base-url %TOPSEC_BASE_URL%

# 3. Jenkins 上验证
# http://localhost:8080 → Job → Build Now
```
