# 接口自动化测试框架说明

这份文档说明当前框架的新定位：**接口自动化为主，Playwright 只作为可选接口抓取工具**。

## 1. 当前框架做什么

当前项目主要做接口自动化测试：

1. 用 YAML 管理接口测试用例。
2. 用 pytest 发现和执行用例。
3. 用 requests 发送 HTTP 请求。
4. 用统一断言检查状态码、响应头、响应体和 JSON 字段。
5. 用 Allure 保存接口请求、响应和测试结果。

Playwright 不再是主要执行方式。它保留给两个场景：

1. 从页面操作中抓取 XHR/fetch 接口。
2. 必要时执行旧的 UI 辅助用例。

## 2. 目录怎么理解

```text
ai-test-framework/
├── common/
│   ├── api_client.py       requests 客户端
│   ├── api_case_runner.py  YAML 接口用例执行器
│   ├── json_path.py        JSON 字段读取工具
│   ├── assertion.py        统一断言
│   └── yaml_util.py        YAML 读取
├── config/env.yaml         环境、接口地址、鉴权配置
├── data/api/               YAML 接口用例
├── testcases/api/          pytest 接口入口
├── tools/                  Playwright 抓取接口转 YAML 草稿
├── pages/                  保留的页面对象
├── testcases/road/         保留的旧 UI 示例
└── web_platform/           本地接口测试平台
```

以后新增接口测试，主要改两个地方：

1. `data/api/`：新增或修改 YAML。
2. `config/env.yaml`：必要时补充接口地址、登录接口和 token 字段。

一般不需要写 Python 测试代码。

## 3. YAML 用例执行流程

执行 `pytest` 后，大致流程是：

1. pytest 默认只扫描 `testcases/api`。
2. `testcases/api/test_yaml_cases.py` 读取 `data/api/*.yaml`。
3. 每一条 YAML case 变成一条 pytest 用例。
4. `common/api_case_runner.py` 替换变量并发送接口请求。
5. 执行 YAML 里声明的断言。
6. 如果配置了 `extract`，把响应字段保存为变量，供后续用例使用。
7. Allure 附加接口请求和响应详情。

## 4. YAML 示例

```yaml
suite: "用户接口"

defaults:
  auth: true
  request:
    headers:
      Accept: "application/json"

cases:
  - id: "query_user"
    name: "查询用户"
    enabled: true
    request:
      method: "GET"
      path: "/api/user/detail"
      params:
        userId: "10001"
    extract:
      user_name: "json:data.name"
    assertions:
      - type: "status_code"
        expected: 200
        message: "查询用户接口应返回 200"
      - type: "json_path_equal"
        path: "code"
        expected: 0
        message: "业务状态码应成功"
      - type: "json_path_not_empty"
        path: "data.name"
        message: "用户名称不能为空"
```

字段说明：

- `suite`：接口套件名称，会展示在 Allure feature 中。
- `defaults.auth`：默认是否使用鉴权客户端。
- `defaults.request.headers`：所有用例默认请求头。
- `cases[].enabled`：是否启用该用例。
- `request.method`：请求方法，例如 `GET`、`POST`。
- `request.path`：接口路径。
- `request.params`：query 参数。
- `request.json`：JSON 请求体。
- `extract`：从响应中提取变量。
- `assertions`：断言列表。

## 5. 断言类型

常用断言如下：

```yaml
- type: "status_code"
  expected: 200

- type: "response_time_less_than"
  expected: 2000

- type: "header_contains"
  name: "Content-Type"
  expected: "application/json"

- type: "body_contains"
  expected: "success"

- type: "json_path_equal"
  path: "code"
  expected: 0

- type: "json_path_exists"
  path: "data.list"

- type: "json_path_not_empty"
  path: "data.list"

- type: "json_path_length"
  path: "data.list"
  expected: 10
```

JSON 路径使用点分格式，例如：

```text
data.list.0.id
```

也兼容：

```text
$.data.list.0.id
```

## 6. 变量和提取

从响应中提取：

```yaml
extract:
  token: "json:data.access_token"
  request_id: "header:X-Request-Id"
```

在后续请求中使用：

```yaml
headers:
  Authorization: "Bearer {{ token }}"
params:
  requestId: "{{ request_id }}"
```

读取环境变量：

```yaml
headers:
  X-Trace-Id: "${TRACE_ID}"
```

## 7. 鉴权怎么配置

已有 token 时：

```bash
export ACCESS_TOKEN="你的 token"
```

如果希望框架自动调用登录接口获取 token，在 `config/env.yaml` 中配置：

```yaml
api:
  base_url: "http://你的接口地址"
  auth:
    token_env: "ACCESS_TOKEN"
    header_name: "Authorization"
    header_prefix: "Bearer"
    login:
      path: "/api/login"
      method: "POST"
      username_env: "LOGIN_USERNAME"
      password_env: "LOGIN_PASSWORD"
      username_field: "userName"
      password_field: "password"
      token_json_path: "data.access_token"
```

执行前传账号密码：

```bash
export LOGIN_USERNAME="刘晓潇"
export LOGIN_PASSWORD=""
pytest
```

## 8. 怎么执行

执行默认接口用例：

```bash
pytest
```

执行指定 YAML：

```bash
API_CASE_PATH="data/api/road_route_info.yaml" pytest testcases/api/test_yaml_cases.py
```

临时覆盖接口基础地址：

```bash
API_BASE_URL="http://10.6.20.233:8891" pytest
```

## 9. 从页面抓接口并生成 YAML

如果现在还不知道真实接口路径，可以用 Playwright 抓取页面请求：

```bash
python tools/capture_api_to_yaml.py \
  "http://10.6.20.233:8891/#/about/homepage" \
  --output data/api/captured_api_cases.yaml \
  --wait-seconds 20 \
  -k road
```

生成的 YAML 默认不会执行：

```yaml
enabled: false
```

审阅接口路径、参数、鉴权和断言后，再改为：

```yaml
enabled: true
```

这个格式也适合后续 AI 使用：AI 从页面抓到接口信息后，按同样结构生成 YAML，就能被 pytest 直接执行。

## 10. 本地测试平台

启动：

```bash
.venv/bin/python web_platform/app.py
```

打开：

```text
http://127.0.0.1:8765
```

平台现在主要用于执行接口用例。页面登录获取 token 是可选项，只有勾选“执行用例前使用页面登录获取 token”时才会触发 Playwright。

## 11. 旧 UI 用例

旧 UI 用例仍保留在：

```text
testcases/road/
```

默认 `pytest` 不会执行它们。如果需要临时执行，可以显式指定：

```bash
pytest testcases/road/test_route_info.py
```

这时才会使用 Playwright 浏览器 fixture。
