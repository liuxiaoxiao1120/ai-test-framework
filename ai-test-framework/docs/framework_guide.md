# 自动化测试框架说明文档

这份文档是给不熟悉 Python 和自动化测试框架的人看的。你可以先把它当成“项目地图”：知道每个目录做什么、页面按钮点下去之后发生了什么、以后新增测试要改哪些文件。

## 1. 这个项目现在能做什么

当前项目有两部分：

1. 自动化测试框架
   - 使用 Python 编写。
   - 使用 pytest 管理和执行测试用例。
   - 使用 Playwright 打开浏览器、登录系统、点击页面、查询数据。
   - 使用 Allure 保存测试报告数据。

2. 本地测试平台页面
   - 地址是 `http://127.0.0.1:8765`。
   - 页面里可以填写被测系统地址、登录地址、账号、密码、用例路径。
   - 点击“测试登录”可以验证登录配置。
   - 点击“执行用例”可以调用 pytest 执行测试。

你现在重点可以先关注两条线：

- 页面上怎么配置和执行。
- 测试用例文件怎么组织。

## 2. 项目目录说明

项目根目录是：

```text
/Users/liuxiaoxiao/Documents/framework/ai-test-framework
```

主要目录如下：

```text
ai-test-framework/
├── common/                 公共工具
├── config/                 环境、菜单等配置
├── data/                   测试数据
├── pages/                  页面操作封装
├── testcases/              pytest 测试用例
├── web_platform/           本地测试平台页面
├── reports/                Allure 测试结果
├── screenshots/            失败截图
├── logs/                   日志
├── conftest.py             pytest 全局配置和公共 fixture
├── pytest.ini              pytest 默认运行配置
├── requirements.txt        Python 依赖清单
└── README.md               项目快速说明
```

你可以这样理解：

- `config/`：告诉框架“测哪个系统、从哪个菜单进页面”。
- `data/`：告诉框架“用什么查询条件测”。
- `pages/`：告诉框架“页面上的按钮、输入框怎么操作”。
- `testcases/`：告诉框架“要验证哪些场景”。
- `web_platform/`：你看到的测试平台页面。

## 3. Python 文件大概怎么看

你不需要一开始就学完整 Python。先记住几个常见结构：

```python
def search(...):
    ...
```

这是一个函数，表示一段可重复使用的动作。

```python
class RouteInfoPage(BasePage):
    ...
```

这是一个类。这里可以理解为“路线信息页面的操作说明书”。

```python
@pytest.fixture()
def route_info_page(...):
    ...
```

这是 pytest 的 fixture。可以理解为“测试执行前先准备好页面”。

```python
def test_search(...):
    ...
```

以 `test_` 开头的函数就是测试用例，pytest 会自动识别并执行它。

## 4. 测试平台页面说明

测试平台相关文件在：

```text
web_platform/
├── app.py                  平台后端服务
├── static/index.html       页面结构
├── static/styles.css       页面样式
├── static/app.js           页面按钮逻辑
└── runtime/config.json     页面保存的本地配置
```

### 4.1 启动平台

在终端执行：

```bash
cd /Users/liuxiaoxiao/Documents/framework/ai-test-framework
.venv/bin/python web_platform/app.py
```

然后打开：

```text
http://127.0.0.1:8765
```

### 4.2 页面字段是什么意思

页面字段说明：

```text
被测系统地址     例如 http://10.6.20.233:8891
登录地址         例如 /#/Login
账号字段名       当前是 userName
密码字段名       当前是 password
账号             当前是 刘晓潇
密码             当前可以为空
token 存储       localStorage 或 sessionStorage
token key        当前是 access_token
用例路径         例如 testcases/road/test_route_info.py
```

### 4.3 页面按钮是什么意思

```text
保存配置
```

把页面上的配置保存到 `web_platform/runtime/config.json`。

```text
测试登录
```

平台后端会用 Playwright 打开登录页，输入账号和密码，然后点击登录。

```text
执行用例
```

平台后端会调用 pytest，执行页面上填写的用例路径。

## 5. 登录流程说明

当前登录信息是：

```text
登录地址：http://10.6.20.233:8891/#/Login
账号：刘晓潇
密码：空
提交参数：userName=刘晓潇&password=
```

框架支持两种登录方式。

### 5.1 使用 token

如果你已经有 `access_token`，可以在终端这样传：

```bash
export ACCESS_TOKEN="你的token"
```

框架会在打开页面前，把 token 写入浏览器的 `localStorage`。

### 5.2 使用登录页自动登录

如果没有 token，就使用账号自动登录：

```bash
export LOGIN_USERNAME="刘晓潇"
export LOGIN_PASSWORD=""
```

平台页面点击“执行用例”时，也会把页面里的账号密码传给 pytest。

对应逻辑在：

```text
conftest.py
```

里面的 `_login_by_account` 函数负责打开登录页、填账号、填密码、点击登录。

## 6. pytest 用例执行流程

以路线信息用例为例：

```text
testcases/road/test_route_info.py
```

执行过程大概是：

1. pytest 读取 `pytest.ini`。
2. pytest 加载 `conftest.py`。
3. `conftest.py` 启动 Playwright 浏览器。
4. 如果有 `ACCESS_TOKEN`，就注入 token。
5. 如果没有 `ACCESS_TOKEN`，就打开登录页自动登录。
6. 打开系统首页。
7. 按菜单进入“农村公路 -> 科学决策 -> 数据管理 -> 静态数据 -> 路线信息”。
8. 执行查询。
9. 检查页面表格或结果区域是否加载出来。
10. 失败时保存截图到 `screenshots/`。
11. 测试结果写入 `reports/allure-results/`。

## 7. 路线信息测试用例说明

路线信息相关文件有三个：

```text
data/road/route_info.yaml
pages/road/route_info_page.py
testcases/road/test_route_info.py
```

### 7.1 测试数据

文件：

```text
data/road/route_info.yaml
```

里面写查询条件：

```yaml
search_cases:
  - name: "默认条件查询"
    year: ""
    keyword: ""
  - name: "路线编号查询"
    year: ""
    keyword: "C001330111"
```

你以后想多测一个条件，就在这里加一组：

```yaml
  - name: "路线名称查询"
    year: ""
    keyword: "青玉线"
```

### 7.2 页面操作

文件：

```text
pages/road/route_info_page.py
```

这个文件负责页面怎么操作，比如：

- 找“年份”输入框。
- 找“路线名称或编码”输入框。
- 找“查询”按钮。
- 判断表格是否出现。
- 捕获接口响应。

一般来说，页面按钮、输入框、表格结构变了，主要改这里。

### 7.3 测试用例

文件：

```text
testcases/road/test_route_info.py
```

这个文件负责定义要测什么，比如：

- 能否进入路线信息页面。
- 默认查询是否正常。
- 输入路线编号查询是否正常。

一般来说，新增一个测试场景，主要改这里。

## 8. 菜单配置说明

文件：

```text
config/modules.yaml
```

当前路线信息菜单路径是：

```yaml
road:
  name: "农村公路"
  menus:
    route_info:
      - "农村公路"
      - "科学决策"
      - "数据管理"
      - "静态数据"
      - "路线信息"
```

框架会按这个顺序点击菜单。

如果页面菜单名称变了，比如“路线信息”改成“路线基础信息”，这里也要改。

## 9. 环境配置说明

文件：

```text
config/env.yaml
```

里面配置不同环境：

```yaml
environments:
  test:
    base_url: "http://10.6.20.233:8891"
    entry_path: "/#/about/homepage"
```

这里的意思是：

- `base_url` 是系统域名。
- `entry_path` 是登录后首页地址。
- `auth.login.path` 是登录页地址。
- `auth.storage_key` 是 token 的 key。

如果以后换测试环境，只要改这里，或者在运行时用 `BASE_URL` 覆盖。

## 10. 常用命令

进入项目目录：

```bash
cd /Users/liuxiaoxiao/Documents/framework/ai-test-framework
```

启动测试平台：

```bash
.venv/bin/python web_platform/app.py
```

命令行执行路线信息用例：

```bash
LOGIN_USERNAME="刘晓潇" LOGIN_PASSWORD="" .venv/bin/python -m pytest testcases/road/test_route_info.py
```

执行全部用例：

```bash
LOGIN_USERNAME="刘晓潇" LOGIN_PASSWORD="" .venv/bin/python -m pytest
```

检查 pytest 是否安装成功：

```bash
.venv/bin/python -m pytest --version
```

检查 Playwright 是否安装成功：

```bash
.venv/bin/python -m playwright --version
```

## 11. 新增一个页面测试时怎么做

假设以后要测“构造物信息”，一般按这四步：

### 第一步：加菜单路径

修改：

```text
config/modules.yaml
```

新增类似：

```yaml
    structure_info:
      - "农村公路"
      - "科学决策"
      - "数据管理"
      - "静态数据"
      - "构造物信息"
```

### 第二步：加测试数据

新增：

```text
data/road/structure_info.yaml
```

写查询条件。

### 第三步：加页面对象

新增：

```text
pages/road/structure_info_page.py
```

写页面怎么输入、怎么点击、怎么判断结果。

### 第四步：加测试用例

新增：

```text
testcases/road/test_structure_info.py
```

写具体要测哪些场景。

## 12. 常见问题

### 12.1 平台页面打不开

先确认服务有没有启动：

```bash
.venv/bin/python web_platform/app.py
```

如果提示端口被占用，可以换端口：

```bash
PLATFORM_PORT=8766 .venv/bin/python web_platform/app.py
```

然后打开：

```text
http://127.0.0.1:8766
```

### 12.2 点击执行用例提示找不到 pytest

说明没有用虚拟环境启动平台。要用：

```bash
.venv/bin/python web_platform/app.py
```

不要用：

```bash
python3 web_platform/app.py
```

### 12.3 执行用例时登录失败

先检查页面配置：

```text
被测系统地址是否正确
登录地址是否正确
账号是否正确
密码是否为空
账号字段名是否是 userName
密码字段名是否是 password
```

如果登录页有验证码、短信验证、滑块验证，自动登录可能需要改造。

### 12.4 菜单点不进去

主要检查：

```text
config/modules.yaml
```

里面的菜单文字必须和页面上看到的文字一致。

### 12.5 查询没有结果

先确认手工在页面上用同样条件能不能查到。

如果手工可以，自动化不行，通常要检查：

- 输入框定位是否正确。
- 查询按钮定位是否正确。
- 页面是否还在加载。
- 接口是否报错。

## 13. 你后续最常改的文件

如果你只是改测试条件：

```text
data/road/route_info.yaml
```

如果你要新增页面操作：

```text
pages/road/route_info_page.py
```

如果你要新增测试场景：

```text
testcases/road/test_route_info.py
```

如果你要改环境地址或登录方式：

```text
config/env.yaml
web_platform 页面配置
```

如果你要改平台页面长什么样：

```text
web_platform/static/index.html
web_platform/static/styles.css
web_platform/static/app.js
```

## 14. 推荐学习顺序

你不用一次看完所有代码。推荐顺序是：

1. 先会启动平台页面。
2. 再会点“测试登录”和“执行用例”。
3. 再看 `data/road/route_info.yaml`，学会改查询条件。
4. 再看 `testcases/road/test_route_info.py`，知道测试用例怎么写。
5. 最后看 `pages/road/route_info_page.py`，理解页面元素怎么定位。

这样会比直接从 Python 语法开始学更快。
