# 接口自动化测试平台雏形说明

当前仓库已经从 Web/UI 自动化主线调整为接口自动化主线。现阶段重点不是做完整平台，而是先沉淀可复用的接口测试核心。

## 1. 主执行链路

```text
cases/*.yaml -> pytest -> core.loader -> core.runner -> core.client -> core.assertor -> Allure
```

默认执行：

```bash
pytest
```

pytest 只扫描：

```text
testcases/api
```

不会默认执行 `pages/` 或 `testcases/road/` 下的 UI 自动化内容。

## 2. 核心目录

```text
core/
├── client.py        HTTP 请求封装
├── loader.py        YAML/JSON 用例加载
├── runner.py        用例执行器
├── assertor.py      状态码和 JSONPath 断言
├── extractor.py     响应字段提取
├── context.py       上下文变量管理
└── reporter.py      Allure 附件和结果整理
```

新增接口用例时，优先改：

```text
cases/
```

不要再按 UI 自动化方式新增 Page Object。

## 3. YAML 用例格式

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

字段说明：

- `name`：用例名称。
- `enabled`：是否启用；不写时默认为启用。
- `request.method`：请求方法，支持 `GET`、`POST`、`PUT`、`DELETE`。
- `request.url`：接口路径或完整 URL。
- `request.headers`：请求头。
- `request.params`：query 参数。
- `request.json`：JSON 请求体。
- `request.data`：表单或原始请求体。
- `extract`：从响应中提取变量。
- `assert.status_code`：状态码断言。
- `assert.jsonpath`：JSONPath 等值断言。

## 4. 变量引用

前一个接口提取：

```yaml
extract:
  token: $.data.token
```

后续接口引用：

```yaml
request:
  method: GET
  url: /api/user/profile
  headers:
    Authorization: Bearer ${token}
```

`${token}` 会优先读取接口上下文变量；如果上下文里没有，再读取系统环境变量。

## 5. 环境配置

主要配置文件：

```text
config/env.yaml
config/settings.yaml
```

接口基础地址优先级：

1. `API_BASE_URL`
2. `env.yaml` 中当前环境的 `api.base_url`
3. `env.yaml` 中当前环境的 `base_url`

示例：

```bash
API_BASE_URL="http://127.0.0.1:8000" pytest
```

## 6. 指定用例

默认加载：

```text
cases/
```

指定文件或目录：

```bash
API_CASE_PATH="cases/demo/login.yaml" pytest
API_CASE_PATH="cases/demo" pytest
```

## 7. Playwright 的位置

Playwright 不属于当前接口测试核心依赖。

它后续只用于：

1. 页面接口捕获。
2. 辅助 AI 根据页面流量生成 YAML 用例。
3. 临时执行保留下来的旧 UI 用例。

说明见：

```text
future_ai/README.md
```

可选依赖：

```bash
pip install -r requirements-capture.txt
playwright install chromium
```

## 8. 平台化方向

`web_platform/` 目前是接口测试平台雏形。下一步可以继续做：

1. YAML 用例在线编辑。
2. 环境管理。
3. 用例集选择和执行。
4. 异步任务和执行历史。
5. Allure 报告链接归档。
6. 页面接口捕获后由 AI 生成 YAML 草稿。
