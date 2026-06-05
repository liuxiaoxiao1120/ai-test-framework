# 接口自动化测试平台雏形

这个仓库会在现有代码基础上逐步发展成接口自动化测试平台。当前阶段先把核心能力打稳：用 YAML/JSON 管理接口用例，用 pytest 执行，用 requests 发请求，用 Allure 输出报告。

Playwright 不是当前核心依赖。它后续只用于页面接口捕获、辅助 AI 从页面流量生成 YAML 用例，相关说明放在 `future_ai/`。

## 当前目标

- 以接口自动化为主线，不再以 Web/UI 自动化为主线。
- 保留 pytest、Allure、config、logs、reports 和本地 web_platform。
- 把 HTTP 请求、用例加载、执行、断言、提取、上下文和报告整理拆到 `core/`。
- 后续在 `web_platform/` 上扩展成可视化接口测试平台。

## 目录结构

```text
ai-test-framework/
├── core/
│   ├── client.py        # HTTP 请求封装
│   ├── loader.py        # YAML/JSON 用例加载
│   ├── runner.py        # 用例执行器
│   ├── assertor.py      # 状态码和 JSONPath 断言
│   ├── extractor.py     # 响应字段提取
│   ├── context.py       # 上下文变量管理
│   └── reporter.py      # Allure 附件和结果整理
├── cases/
│   └── demo/login.yaml  # YAML 用例示例
├── testcases/api/
│   └── test_yaml_cases.py
├── config/
│   ├── env.yaml
│   └── settings.yaml
├── common/              # 兼容旧工具入口，api_client 保留
├── web_platform/        # 后续接口测试平台雏形
├── future_ai/           # 未来页面接口捕获和 AI 生成用例说明
├── logs/
├── reports/
├── pages/               # 旧 UI 自动化内容，已不作为主线
├── testcases/road/      # 旧 UI 示例，默认不执行
└── screenshots/         # 旧 UI 截图目录，默认不使用
```

## 安装依赖

```bash
cd ai-test-framework
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

核心接口测试不需要安装 Playwright。

未来如需页面接口捕获，再安装可选依赖：

```bash
pip install -r requirements-capture.txt
playwright install chromium
```

## 配置环境

环境配置在 `config/env.yaml`。

接口基础地址优先级：

1. `API_BASE_URL` 环境变量。
2. `config/env.yaml` 里的 `environments.<env>.api.base_url`。
3. `config/env.yaml` 里的 `environments.<env>.base_url`。

示例：

```bash
API_BASE_URL="http://127.0.0.1:8000" pytest
```

切换环境：

```bash
pytest --env=uat
APP_ENV=uat pytest
```

## YAML 用例格式

用例默认放在 `cases/` 目录，支持 `.yaml`、`.yml`、`.json`。

单接口用例示例：

```yaml
name: 登录接口成功
request:
  method: POST
  url: /api/login
  headers:
    Content-Type: application/json
  json:
    username: test
    password: "123456"
extract:
  token: $.data.token
assert:
  status_code: 200
  jsonpath:
    $.code: 0
    $.message: success
```

支持能力：

- 请求方法：`GET`、`POST`、`PUT`、`DELETE`
- 请求字段：`headers`、`params`、`json`、`data`
- 状态码断言：`assert.status_code`
- JSONPath 断言：`assert.jsonpath`
- 字段提取：`extract`
- 上下文变量引用：`${token}`

变量引用示例：

```yaml
name: 查询用户信息
request:
  method: GET
  url: /api/user/profile
  headers:
    Authorization: Bearer ${token}
assert:
  status_code: 200
```

`cases/demo/login.yaml` 是示例文件，默认 `enabled: false`，避免没有真实接口时误执行。

## 执行测试

执行全部接口用例：

```bash
pytest
```

执行指定用例文件或目录：

```bash
API_CASE_PATH="cases/demo/login.yaml" pytest
API_CASE_PATH="cases/demo" pytest
```

执行接口冒烟示例：

```bash
API_SMOKE_PATH="/health" pytest testcases/api/test_smoke.py
```

## Allure 报告

pytest 执行后，Allure 原始结果会写入：

```text
reports/allure-results/
```

生成静态报告：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

## CI/CD

已新增 GitHub Actions：

```text
.github/workflows/api-tests.yml
```

触发方式：

- push 到 `main` 或 `master`
- pull request
- 手动 workflow_dispatch

CI 会安装 `requirements.txt` 并执行：

```bash
pytest
```

Allure 原始结果会作为 artifact 上传。

## 本地平台雏形

`web_platform/` 会保留并继续演进成接口测试平台。当前它可以配置接口地址、用例路径，并触发 pytest 执行。

启动：

```bash
.venv/bin/python web_platform/app.py
```

打开：

```text
http://127.0.0.1:8765
```

## 关于旧 UI 自动化

以下内容保留，但不作为当前主线：

- `pages/`
- `testcases/road/`
- `screenshots/`
- Playwright 相关 UI fixture

默认 `pytest` 只扫描 `testcases/api`，不会执行 UI 用例。需要临时执行旧 UI 用例时再显式指定路径，并安装 `requirements-capture.txt`。

## 下一步平台化方向

后续可以继续做：

1. 在 `web_platform/` 增加用例管理页面。
2. 支持在线编辑和保存 YAML。
3. 支持选择环境、选择用例集并异步执行。
4. 保存历史执行记录和报告链接。
5. 接入登录态、项目、模块、标签、定时任务。
6. 用 Playwright 抓取页面接口，再让 AI 生成 YAML 草稿。
