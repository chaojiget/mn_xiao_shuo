# Web 服务快速启动

## 🚀 一键启动（推荐）

```bash
cd /Users/lijianyong/mn_xiao_shuo
./web/start-web.sh
```

这将自动启动：
- ✅ FastAPI 后端 (http://localhost:8000)
- ✅ Next.js 前端 (http://localhost:3000)

---

## 📖 手动启动

### 1. 启动后端

```bash
# 激活虚拟环境
source .venv/bin/activate

# 进入后端目录
cd web/backend

# 启动 FastAPI
uvicorn main:app --reload --port 8000
```

后端将运行在 http://localhost:8000

### 2. 启动前端

打开新终端：

```bash
# 进入前端目录
cd web/frontend

# 首次运行：安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将运行在 http://localhost:3000

---

## 🎨 功能特性

### 主界面

访问 http://localhost:3000，你会看到：

1. **开始创作** 标签页
   - 选择小说类型（科幻/玄幻）
   - 点击"开始创作"生成第一章
   - 输入选择影响后续剧情
   - 实时查看生成内容

2. **我的小说** 标签页
   - 查看所有已创建的小说
   - 管理章节
   - 导出为 Markdown

### API 端点

后端提供以下 API：

- `GET /` - 健康检查
- `GET /api/novels` - 获取所有小说
- `POST /api/novels` - 创建新小说
- `GET /api/novels/{id}` - 获取小说详情
- `GET /api/novels/{id}/chapters/{num}` - 获取章节
- `GET /api/novels/{id}/export` - 导出小说
- `WS /ws/generate/{id}` - WebSocket 实时生成

**API 文档**: http://localhost:8000/docs

---

## 🛠️ 技术栈

### 前端
- **Next.js 14** - React 框架
- **shadcn/ui** - 现代 UI 组件
- **Tailwind CSS** - 样式
- **TypeScript** - 类型安全

### 后端
- **FastAPI** - Python Web 框架
- **WebSocket** - 实时通信
- **SQLite** - 数据存储
- **DeepSeek V3** - AI 模型

---

## 📝 使用流程

1. **访问主页**: http://localhost:3000

2. **开始创作**
   - 选择小说类型（科幻或玄幻）
   - 点击"开始创作"
   - 等待 AI 生成第一章

3. **交互选择**
   - 在文本框输入你的选择
   - 点击"继续生成"
   - AI 会基于你的选择生成后续内容

4. **保存与导出**
   - 点击"保存"保存当前进度
   - 切换到"我的小说"查看已创建作品
   - 点击"导出"下载 Markdown 格式

---

## 🔧 故障排除

### 前端启动失败

```bash
# 清理并重新安装
cd web/frontend
rm -rf node_modules package-lock.json
npm install
```

### 后端启动失败

检查虚拟环境是否激活：
```bash
source .venv/bin/activate
pip install -r web/backend/requirements.txt
```

### 端口占用

如果端口被占用，修改端口：

**后端** (web/backend/main.py 最后一行):
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为 8001
```

**前端** (web/frontend/package.json):
```json
"dev": "next dev -p 3001"  // 改为 3001
```

---

## 📸 界面预览

访问 http://localhost:3000 查看现代化的 UI 界面：

- 🎨 优雅的渐变背景
- 📱 响应式设计
- 🌙 支持暗黑模式（未来版本）
- ⚡ 流畅的动画效果

---

## 🎯 下一步

- [ ] 添加用户认证
- [ ] 支持多语言
- [ ] 导出 EPUB 格式
- [ ] 添加编辑功能
- [ ] 集成更多 AI 模型

---

## 💡 提示

- 首次生成可能需要 10-20 秒（AI 模型处理时间）
- 建议使用 Chrome/Edge/Safari 最新版本
- 生成的内容会自动保存到数据库

---

享受 AI 创作之旅！📚✨
