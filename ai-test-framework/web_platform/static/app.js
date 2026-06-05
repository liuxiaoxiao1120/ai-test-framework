const form = document.querySelector("#configForm");
const saveStatus = document.querySelector("#saveStatus");
const runState = document.querySelector("#runState");
const lastAction = document.querySelector("#lastAction");
const returnCode = document.querySelector("#returnCode");
const resultText = document.querySelector("#resultText");
const output = document.querySelector("#output");

const buttons = {
  save: document.querySelector("#saveButton"),
  login: document.querySelector("#loginButton"),
  run: document.querySelector("#runButton"),
};

function getConfig() {
  const config = Object.fromEntries(new FormData(form).entries());
  config.use_page_login = Boolean(form.elements.use_page_login?.checked);
  return config;
}

function setConfig(config) {
  for (const [key, value] of Object.entries(config)) {
    const field = form.elements[key];
    if (field) {
      if (field.type === "checkbox") {
        field.checked = Boolean(value);
      } else {
        field.value = value ?? "";
      }
    }
  }
}

function setBusy(isBusy) {
  Object.values(buttons).forEach((button) => {
    button.disabled = isBusy;
  });
}

function setResult({ action, state, ok, code, text }) {
  lastAction.textContent = action ?? "-";
  runState.textContent = state ?? "空闲";
  returnCode.textContent = code ?? "-";
  resultText.textContent = ok === undefined ? "-" : ok ? "通过" : "失败";
  if (text !== undefined) {
    output.textContent = text || "(无输出)";
  }
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

async function loadConfig() {
  const data = await requestJson("/api/config");
  setConfig(data.config);
  saveStatus.textContent = "已加载";
}

async function saveConfig() {
  setBusy(true);
  saveStatus.textContent = "保存中";
  try {
    const data = await requestJson("/api/config", {
      method: "POST",
      body: JSON.stringify(getConfig()),
    });
    setConfig(data.config);
    saveStatus.textContent = "已保存";
    setResult({ action: "保存配置", state: "完成", text: "配置已保存。" });
  } catch (error) {
    saveStatus.textContent = "保存失败";
    setResult({ action: "保存配置", state: "失败", ok: false, text: error.message });
  } finally {
    setBusy(false);
  }
}

async function checkLogin() {
  setBusy(true);
  setResult({ action: "测试页面登录", state: "执行中", text: "正在登录..." });
  try {
    const data = await requestJson("/api/login/check", {
      method: "POST",
      body: JSON.stringify(getConfig()),
    });
    setResult({
      action: "测试页面登录",
      state: "完成",
      ok: data.ok,
      code: "-",
      text: JSON.stringify(data, null, 2),
    });
  } catch (error) {
    setResult({ action: "测试页面登录", state: "失败", ok: false, text: error.message });
  } finally {
    setBusy(false);
  }
}

async function runCase() {
  setBusy(true);
  setResult({ action: "执行用例", state: "执行中", text: "pytest 正在执行..." });
  try {
    const data = await requestJson("/api/run", {
      method: "POST",
      body: JSON.stringify(getConfig()),
    });
    setResult({
      action: "执行用例",
      state: "完成",
      ok: data.ok,
      code: data.return_code,
      text: data.output,
    });
  } catch (error) {
    setResult({ action: "执行用例", state: "失败", ok: false, text: error.message });
  } finally {
    setBusy(false);
  }
}

buttons.save.addEventListener("click", saveConfig);
buttons.login.addEventListener("click", checkLogin);
buttons.run.addEventListener("click", runCase);

loadConfig().catch((error) => {
  saveStatus.textContent = "加载失败";
  output.textContent = error.message;
});
