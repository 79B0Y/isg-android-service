# Android TV Box Integration - Installation and Troubleshooting

## 🚨 500 Internal Server Error 解决方案

如果在添加集成时遇到 "500 Internal Server Error" 或 "无法加载配置向导"，这通常是因为缺少必需的 ADB 依赖库。

### 问题原因

Home Assistant 需要以下 Python 库来连接 Android 设备：
- `adb-shell>=0.4.4`
- `pure-python-adb>=0.3.0`

### 解决方案

#### 方法1: Home Assistant Container/Docker (推荐)

如果你使用 Docker 版本的 Home Assistant：

1. **进入 Home Assistant 容器**：
   ```bash
   docker exec -it homeassistant bash
   ```

2. **安装依赖**：
   ```bash
   pip install adb-shell>=0.4.4 pure-python-adb>=0.3.0
   ```

3. **重启 Home Assistant**：
   ```bash
   exit
   docker restart homeassistant
   ```

#### 方法2: Home Assistant OS (HAOS)

如果你使用 Home Assistant OS：

1. **通过 SSH 连接到 HAOS**
2. **进入 Home Assistant Core 容器**：
   ```bash
   docker exec -it homeassistant bash
   ```

3. **安装依赖**：
   ```bash
   pip install adb-shell>=0.4.4 pure-python-adb>=0.3.0
   ```

4. **重启 Home Assistant**

#### 方法3: Home Assistant Core (手动安装)

如果你手动安装了 Home Assistant Core：

1. **激活 Home Assistant 虚拟环境**：
   ```bash
   source /srv/homeassistant/bin/activate
   ```

2. **安装依赖**：
   ```bash
   pip install adb-shell>=0.4.4 pure-python-adb>=0.3.0
   ```

3. **重启 Home Assistant 服务**：
   ```bash
   sudo systemctl restart home-assistant@homeassistant
   ```

#### 方法4: Home Assistant Supervised

1. **通过 SSH 连接**
2. **进入 homeassistant 容器**：
   ```bash
   docker exec -it homeassistant bash
   ```

3. **安装依赖并重启**

### 验证安装

在安装依赖后，你可以通过以下方式验证：

1. **检查 Home Assistant 日志**：
   - 去 Settings → System → Logs
   - 查看是否还有 "No module named 'adb_shell'" 错误

2. **重新尝试添加集成**：
   - Settings → Devices & Services → Add Integration
   - 搜索 "Android TV Box"

### 调试工具

项目包含调试脚本来帮助诊断问题：

```bash
# 在项目目录中运行
python3 test_integration_import.py

# 测试 ADB 连接
python3 debug_adb_connection.py <IP地址> <端口>
```

### 常见错误和解决方案

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| 500 Internal Server Error | 缺少 ADB 依赖 | 安装 `adb-shell` 和 `pure-python-adb` |
| "No module named 'adb_shell'" | 依赖未安装 | 在 HA 环境中安装依赖 |
| Connection timeout | 设备不可达 | 检查 IP 地址和网络连接 |
| Connection refused | ADB 未启用 | 启用开发者选项和 ADB 调试 |

### 依赖安装成功后的步骤

1. **重启 Home Assistant**
2. **清除浏览器缓存**
3. **重新尝试添加集成**：
   - IP 地址：你的 Android TV Box IP
   - 端口：5555 (默认)
   - 设备名称：任意友好名称

### 日志调试

如果仍然有问题，启用调试日志：

```yaml
# configuration.yaml
logger:
  logs:
    custom_components.android_tv_box: debug
```

重启后查看详细日志信息。

### 联系支持

如果按照上述步骤仍无法解决问题：

1. 提供完整的错误日志
2. 说明你的 Home Assistant 安装类型
3. 确认是否已正确安装依赖库

---

## 快速安装检查清单

- [ ] 确认 ADB 依赖已安装在 Home Assistant 环境中
- [ ] 重启 Home Assistant
- [ ] Android TV Box 已启用 ADB 调试
- [ ] 网络连接正常
- [ ] 使用正确的 IP 地址和端口
- [ ] 浏览器缓存已清除