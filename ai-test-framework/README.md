# Web 自动化测试框架

第一版框架使用 Python、Pytest、Playwright 和 Allure，按业务模块组织 Page Object 与测试数据。当前覆盖：

- 农村公路 -> 科学决策
- 页面进入
- 查询
- 导出按钮可用性

## 项目结构

```text
ai-test-framework/
├── common/                 # 公共工具：YAML、日志、断言
├── config/                 # 环境和菜单配置
├── data/road/              # 农村公路测试数据
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

## 设置令牌

框架不会在代码中保存访问令牌。执行测试前设置环境变量：

```bash
export ACCESS_TOKEN="你的访问令牌"
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
