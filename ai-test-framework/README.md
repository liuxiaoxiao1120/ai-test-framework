# 接口自动化测试框架

当前框架已调整为以接口自动化为主，核心链路是：

```text
YAML 测试用例 -> Pytest 参数化执行 -> Requests 发送接口 -> 统一断言 -> Allure 报告
```

Playwright 仍然保留，但只作为可选能力使用：

- 抓取页面中的 XHR/fetch 接口信息。
- 生成 YAML 接口用例草稿。
- 必要时复用旧的 UI 辅助用例。

默认执行 `pytest` 时只运行 `testcases/api`，不会启动浏览器。

## 项目结构

```text
ai-test-framework/
├── common/                 # 接口客户端、YAML 执行器、断言、日志、JSON 路径工具
├── config/                 # 多环境、接口地址、鉴权配置
├── data/api/               # YAML 接口测试用例
├── testcases/api/          # Pytest 接口测试入口
├── tools/                  # 可选工具：Playwright 接口抓取转 YAML
├── pages/                  # 保留的 Page Object，仅用于可选 UI/抓取辅助
├── testcases/road/         # 保留的旧 UI 示例，需显式指定才会执行
├── web_platform/           # 本地接口测试平台页面
├── reports/                # Allure 原始结果和报告
├── logs/                   # 日志
├── conftest.py             # Pytest fixture
├── pytest.ini              # 默认只跑接口用例
└── requirements.txt        # Python 依赖
```

## 环境准备

```bash
cd ai-test-framework
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果只跑接口测试，不需要安装浏览器。只有使用 Playwright 抓取接口或执行旧 UI 用例时，才需要：

```bash
playwright install chromium
```

## 配置接口地址和鉴权

默认环境在 `config/env.yaml` 中配置。接口基础地址优先级如下：

1. `API_BASE_URL` 环境变量。
2. `config/env.yaml` 中的 `api.base_url`。
3. 当前环境的 `base_url`。

已有 token 时：

```bash
export ACCESS_TOKEN="你的访问令牌"
```

没有 token 时，可以在 `config/env.yaml` 的 `api.auth.login` 中填写接口登录路径和 token 返回字段，框架会自动用 Requests 调登录接口获取 token。

## YAML 用例格式

接口用例放在 `data/api/*.yaml`。示例：

```yaml
suite: "农村公路路线信息接口"

defaults:
  auth: true
  request:
    headers:
      Accept: "application/json"

cases:
  - id: "route_info_query"
    name: "路线信息查询"
    enabled: true
    request:
      method: "GET"
      path: "/api/road/route-info"
      params:
        keyword: "C001330111"
    extract:
      first_id: "json:data.list.0.id"
    assertions:
      - type: "status_code"
        expected: 200
        message: "路线信息查询接口应返回 200"
      - type: "json_path_exists"
        path: "data"
        message: "响应中应包含 data 字段"
```

支持的常用断言类型：

- `status_code`
- `response_time_less_than`
- `body_contains`
- `body_not_contains`
- `header_equal`
- `header_contains`
- `json_path_equal`
- `json_path_exists`
- `json_path_not_empty`
- `json_path_contains`
- `json_path_length`

变量写法：

```yaml
params:
  id: "{{ first_id }}"
headers:
  X-Trace-Id: "${TRACE_ID}"
```

`{{ first_id }}` 读取前面用例 `extract` 提取出的变量；`${TRACE_ID}` 读取系统环境变量。

## 执行测试

执行全部接口用例：

```bash
pytest
```

执行指定 YAML 文件：

```bash
API_CASE_PATH="data/api/road_route_info.yaml" pytest testcases/api/test_yaml_cases.py
```

执行接口基础冒烟示例：

```bash
API_SMOKE_PATH="/你的无需登录接口" pytest testcases/api/test_smoke.py
AUTH_API_SMOKE_PATH="/你的需登录接口" pytest testcases/api/test_smoke.py
```

## 页面接口抓取生成 YAML 草稿

Playwright 抓取工具位于：

```text
tools/capture_api_to_yaml.py
```

示例：

```bash
python tools/capture_api_to_yaml.py \
  "http://10.6.20.233:8891/#/about/homepage" \
  --output data/api/captured_api_cases.yaml \
  --suite "页面抓取接口" \
  --wait-seconds 20 \
  -k road
```

生成的用例默认 `enabled: false`，需要审阅接口路径、参数、鉴权和断言后再改为 `true`。

## 本地测试平台

启动：

```bash
.venv/bin/python web_platform/app.py
```

打开：

```text
http://127.0.0.1:8765
```

平台可配置基础地址、接口基础地址、接口登录路径、账号、用例路径，并调用 pytest 执行接口用例。页面登录获取 token 是可选项，不是默认执行方式。

## Allure 报告

测试结果默认写入：

```text
reports/allure-results/
```

生成并打开报告：

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```
