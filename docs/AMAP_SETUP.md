# 高德地图接入配置指南

本项目已集成高德地图服务，包括：
- **前端**：高德地图 JS API（地图展示、路线绘制）
- **后端**：高德地图 Web Service API（路线规划、距离计算）

## 获取高德地图 Key

1. 访问 [高德地图开放平台](https://console.amap.com/dev/key/app)
2. 注册/登录账号
3. 创建应用
4. 添加 Key：
   - **Web端(JS API)**：用于前端地图展示
   - **Web服务**：用于后端路线规划

## 配置方式

### 方式一：环境变量文件（推荐）

在项目根目录创建 `.env.local` 文件：

```bash
# 后端使用的高德地图 Web Service API Key
AMAP_WEB_API_KEY=你的Web服务Key

# 前端使用的高德地图 JS API Key
VITE_AMAP_WEB_JS_KEY=你的JS API Key
```

注意：`.env.local` 文件不会被提交到 Git。

### 方式二：运行时配置（临时测试）

启动应用后，访问前端页面，通过设置面板动态配置 Key。

## 验证接入

### 后端验证

```bash
# 启动后端后，测试路线规划接口
curl "http://localhost:8000/api/routes/1/2"
```

成功响应应包含：
- `path_nodes`: 路径点数组
- `distance`: 距离（公里）
- `estimated_time_hours`: 预计时间（小时）
- `source`: 路线来源（`amap` 或 `dijkstra`）

### 前端验证

1. 访问 `http://localhost:5173`
2. 生成行程后进入结果页
3. 切换到"地图"标签
4. 应显示：
   - 地图容器正常加载
   - 景点标记点
   - 路线折线（如果配置了 Key）

## 降级机制

如果高德地图 API 未配置或调用失败，系统会自动降级到本地算法：

- **后端**：使用手写 Dijkstra 算法 + 手写 Heap 计算最短路径
- **前端**：使用直线连接各景点

## 常见问题

### Q: 地图显示空白？
A: 检查浏览器控制台是否有 JS Key 相关的错误，确认 `VITE_AMAP_WEB_JS_KEY` 已正确配置。

### Q: 路线规划返回的是直线？
A: 后端可能没有配置 `AMAP_WEB_API_KEY`，或 API 调用失败降级到了 Dijkstra 算法。

### Q: 高德 API 调用报错 "USERKEY_PLAT_NOMATCH"？
A: Key 的类型不匹配，确保：
- JS API Key 用于前端（浏览器环境）
- Web Service Key 用于后端（服务器环境）

### Q: 免费额度够用吗？
A: 高德地图提供每日 5000 次免费调用额度，足够开发和测试使用。
