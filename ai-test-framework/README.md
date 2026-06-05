# Web 自动化测试框架

第一版框架使用 Python、Pytest、Playwright 和 Allure，按业务模块组织 Page Object 与测试数据。当前覆盖：

- 农村公路 -> 科学决策
- 页面进入
- 查询
- 导出按钮可用性

如果你不熟悉 Python 或这个框架，建议先看这份入门说明：

```text
docs/framework_guide.md
```

## 项目结构

```text
ai-test-framework/
├── common/                 # 公共工具：YAML、日志、断言
├── config/                 # 环境和菜单配置
├── data/road/              # 农村公路测试数据
├── testcases/api/          # 接口测试入口示例
├── pages/road/             # 农村公路 Page Object
├── testcases/road/         # 农村公路测试用例
├── reports/                # Allure 原始结果和报告
├── screenshots/            # 失败截图
├── logs/                   # 运行日志
├── conftest.py             # 全局 fixture 与失败截图钩子
├── pytest.ini              # Pytest 配置
└── requirements.txt        # Python 依赖
```

## 环境准备

建议使用 Python 3.9 或更高版本，并在项目目录中创建虚拟环境：

```bash
cd ai-test-framework
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

安装 Playwright Chromium 浏览器：

```bash
playwright install chromium
```

## 设置登录信息

框架不会在代码中保存访问令牌或密码。若已有访问令牌，执行测试前设置环境变量：

```bash
export ACCESS_TOKEN="你的访问令牌"
```

若需要通过登录页自动登录，设置账号即可；密码为空时可以不设置 `LOGIN_PASSWORD`：

```bash
export LOGIN_USERNAME="刘晓潇"
```

默认使用 `config/env.yaml` 中的 `test` 环境：

```text
http://10.6.20.233:8891/#/about/homepage
```

可以通过参数切换环境，也可以临时覆盖基础地址：

```bash
pytest --env=uat
BASE_URL="https://your-host.example.com" pytest --env=uat
```

## 执行测试

执行全部用例：

```bash
pytest
```

仅执行科学决策模块：

```bash
pytest testcases/road/test_science_decision.py
```

## 从代码层执行接口测试

如果暂时不使用页面平台，可以直接写 pytest 接口用例。公共入口已经放在：

```text
common/api_client.py
conftest.py
testcases/api/test_smoke.py
```

已有 token 时：

```bash
export ACCESS_TOKEN="你的访问令牌"
pytest testcases/api
```

如果没有 token，可以在 `config/env.yaml` 的 `api.auth.login` 中填写真实登录接口路径和 token 返回字段。框架会优先读 `ACCESS_TOKEN`，没有时再调用登录接口获取 token。

用例中可以这样写：

```python
def test_query(auth_api_client):
    response = auth_api_client.get("/你的接口路径")
    assert response.status_code == 200
```

也可以先用环境变量验证一个接口路径：

```bash
API_SMOKE_PATH="/你的无需登录接口" pytest testcases/api/test_smoke.py
AUTH_API_SMOKE_PATH="/你的需登录接口" pytest testcases/api/test_smoke.py
```

## 启动测试平台页面

第一版测试平台页面使用 Python 标准库提供本地服务：

```bash
.venv/bin/python web_platform/app.py
```

打开：

```text
http://127.0.0.1:8765
```

页面可配置被测系统地址、登录地址、账号、空密码、token key 和用例路径，并触发登录检查或执行用例。

失败截图会自动保存到 `screenshots/`，日志会写入 `logs/`，Allure 原始结果会写入 `reports/allure-results/`。

## 生成 Allure 报告

请先确保本机已安装 Allure 命令行工具。生成并打开静态报告：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

也可以直接启动临时报告服务：

```bash
allure serve reports/allure-results
```

## 扩展业务模块

新增业务模块时，按以下方式扩展：

1. 在 `config/modules.yaml` 增加菜单配置。
2. 在 `pages/` 下按业务域增加 Page Object。
3. 在 `data/` 下增加对应测试数据。
4. 在 `testcases/` 下增加测试用例。

后续接入更多能力时，可以继续复用 `BasePage`、全局 fixture、日志、断言和失败截图机制，无需改动现有业务用例结构。
