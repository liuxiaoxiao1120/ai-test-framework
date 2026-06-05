# Future AI / Capture

当前项目主线是接口自动化测试框架，核心执行链路不依赖 Playwright。

Playwright 后续只作为辅助能力使用：

1. 打开业务页面。
2. 监听页面中的 XHR/fetch 请求。
3. 提取接口 method、url、headers、params、body。
4. 交给 AI 生成 `cases/` 目录下的 YAML 接口用例。
5. 人工审阅断言和鉴权后，再交给 pytest 执行。

可选安装：

```bash
pip install -r requirements-capture.txt
playwright install chromium
```

现有抓取草稿工具：

```text
tools/capture_api_to_yaml.py
```

示例：

```bash
python tools/capture_api_to_yaml.py \
  "http://10.6.20.233:8891/#/about/homepage" \
  --output cases/captured/from_page.yaml \
  --wait-seconds 20
```

生成的 YAML 默认应先保持 `enabled: false`，等接口路径、参数、鉴权和断言确认后再启用。
