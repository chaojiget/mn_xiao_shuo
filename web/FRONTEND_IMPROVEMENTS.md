# 前端界面改进总结
Frontend Improvements Summary

> 更新时间: 2025-01-31

---

## 新增组件

### 1. 设定编辑器 (`components/setting/setting-editor.tsx`)

**功能**: 可视化编辑小说设定

**特性**:
- ✅ 四个Tab页面: 世界观、主角、地点、势力
- ✅ 动态添加/删除地点和势力
- ✅ 主角属性和资源滑块配置
- ✅ 科幻/玄幻类型自适应(属性名称、示例文本等)
- ✅ 自动保存功能

**界面结构**:
```tsx
<SettingEditor novelType="scifi" onSave={(setting) => {...}}>
  <Tabs>
    <世界观> // 标题、背景、时间线
    <主角>   // 姓名、职业、属性、资源
    <地点>   // 动态列表，可增删
    <势力>   // 动态列表，可增删
  </Tabs>
</SettingEditor>
```

**亮点**:
- 主角对地点/势力的了解程度由系统管理(知识分层)
- 用户只需编辑"真实层"设定
- 生成时系统自动过滤未发现的内容

---

### 2. 会话历史查看器 (`components/conversation/history-viewer.tsx`)

**功能**: 查看完整对话历史，支持分支和导出

**特性**:
- ✅ 分支管理: 主分支 + 支线分支
- ✅ 搜索功能: 全文搜索消息内容
- ✅ 消息类型标签: 对话/选择/章节/设定修改
- ✅ 角色图标: 用户/助手/系统区分
- ✅ 元数据展开: 查看附加信息
- ✅ Markdown导出

**界面结构**:
```tsx
<HistoryViewer novelId="xxx" onExport={() => {...}}>
  <分支选择按钮组>
  <搜索框>
  <ScrollArea>
    {messages.map(msg => (
      <消息卡片>
        <角色图标> + <消息类型标签> + <时间戳>
        <消息内容>
        <元数据(可折叠)>
      </消息卡片>
    ))}
  </ScrollArea>
</HistoryViewer>
```

**亮点**:
- 支持分支切换,探索不同路径
- 智能上下文窗口(按token截取)
- 一键导出Markdown完整历史

---

### 3. NPC管理面板 (`components/npc/npc-manager.tsx`)

**功能**: 管理NPC种子池和活跃NPC

**特性**:
- ✅ 双视图切换: 种子池 vs 活跃NPC
- ✅ 种子状态标识: 休眠/就绪/已生成
- ✅ 触发条件展示
- ✅ 关系值进度条(-100 to +100)
- ✅ 生命周期阶段标签
- ✅ 互动次数统计
- ✅ 位置和势力信息

**界面结构**:
```tsx
<NPCManager novelId="xxx">
  <视图切换按钮>

  {/* 种子池视图 */}
  <种子卡片>
    <原型标识> + <状态徽章> + <优先级>
    <触发条件列表>
    {就绪时显示"立即生成"按钮}
  </种子卡片>

  {/* 活跃NPC视图 */}
  <NPC卡片>
    <名字> + <职业> + <生命周期阶段>
    <关系值进度条> + <互动次数>
    <位置> + <势力>
    <操作按钮>
  </NPC卡片>
</NPCManager>
```

**亮点**:
- 种子就绪时红色边框高亮
- 关系值颜色渐变(绿→蓝→灰→橙→红)
- 原型图标颜色编码(导师蓝/伙伴绿/对手红)

---

### 4. 小说工作台页面 (`app/novel/[id]/page.tsx`)

**功能**: 集成所有管理功能的工作台

**特性**:
- ✅ 四个Tab: 设定编辑、对话历史、NPC管理、探索进度
- ✅ 统一导航
- ✅ 响应式布局

---

### 5. 主页更新 (`app/page.tsx`)

**改进**:
- ✅ 新增副标题: "全局导演架构 · 智能叙事引擎 · 探索式世界观"
- ✅ 特性展示卡片: 可编辑设定、NPC按需生成、一致性审计
- ✅ 更现代化的设计

---

## 新增UI组件

为了实现上述功能，创建了以下shadcn/ui组件:

1. **Input** (`components/ui/input.tsx`) - 文本输入框
2. **ScrollArea** (`components/ui/scroll-area.tsx`) - 滚动区域
3. **Badge** (`components/ui/badge.tsx`) - 徽章标签
4. **Progress** (`components/ui/progress.tsx`) - 进度条

所有组件基于 `@radix-ui` 构建，样式统一。

---

## 依赖更新

更新 `package.json`:

```json
"@radix-ui/react-scroll-area": "^1.0.5"
```

---

## 目录结构

```
web/frontend/
├── app/
│   ├── page.tsx                    # 主页(已更新)
│   ├── novel/
│   │   └── [id]/
│   │       └── page.tsx            # 小说工作台(新增)
│   └── chat/
│       └── page.tsx                # 聊天页面(已有)
│
├── components/
│   ├── setting/
│   │   └── setting-editor.tsx     # 设定编辑器(新增)
│   │
│   ├── conversation/
│   │   └── history-viewer.tsx     # 历史查看器(新增)
│   │
│   ├── npc/
│   │   └── npc-manager.tsx        # NPC管理(新增)
│   │
│   ├── novel/
│   │   ├── novel-generator.tsx    # 小说生成器(已有)
│   │   └── novel-list.tsx         # 小说列表(已有)
│   │
│   └── ui/
│       ├── input.tsx              # 新增
│       ├── scroll-area.tsx        # 新增
│       ├── badge.tsx              # 新增
│       ├── progress.tsx           # 新增
│       ├── button.tsx             # 已有
│       ├── card.tsx               # 已有
│       ├── tabs.tsx               # 已有
│       └── ...                    # 其他已有组件
```

---

## 使用示例

### 启动前端开发服务器

```bash
cd web/frontend

# 安装新依赖
npm install

# 启动开发服务器
npm run dev
```

访问: `http://localhost:3000`

### 访问工作台

1. 从主页创建/选择小说
2. 点击进入小说工作台: `/novel/{novel_id}`
3. 在工作台中:
   - **设定编辑**: 修改世界观、主角、地点、势力
   - **对话历史**: 查看完整创作记录
   - **NPC管理**: 查看种子池和活跃NPC
   - **探索进度**: (即将推出)

---

## 待集成API

### 1. 设定编辑API

```typescript
// 保存设定
POST /api/novels/{id}/setting
Body: {
  worldSetting: {...},
  protagonist: {...},
  locations: [...],
  factions: [...]
}

// 获取设定
GET /api/novels/{id}/setting
```

### 2. 会话历史API

```typescript
// 获取历史
GET /api/novels/{id}/conversation/history?branch_id=xxx&limit=50

// 导出Markdown
GET /api/novels/{id}/conversation/export?format=markdown
```

### 3. NPC管理API

```typescript
// 获取NPC池状态
GET /api/novels/{id}/npcs/pool

// 生成NPC
POST /api/novels/{id}/npcs/instantiate
Body: { seed_id: "xxx" }

// 更新NPC
PATCH /api/novels/{id}/npcs/{npc_id}
Body: { relationship: 50, ... }
```

---

## 特性对比

### 之前的界面

- 简单的生成器表单
- 只能选择类型和开始创作
- 无法编辑设定
- 无历史查看
- 无NPC管理

### 现在的界面

- ✅ 完整的设定编辑器(4个Tab)
- ✅ 会话历史查看器(支持分支)
- ✅ NPC管理面板(种子池+活跃NPC)
- ✅ 特性卡片展示
- ✅ 现代化设计
- ✅ 响应式布局
- ✅ 更好的用户体验

---

## 设计亮点

### 1. 知识分层可视化

设定编辑器清晰说明:"主角将通过探索逐步发现世界真相"

用户只需编辑完整设定,系统自动管理主角视角。

### 2. NPC生命周期展示

种子池中清晰显示:
- 休眠种子(灰色)
- 就绪种子(红色边框,可立即生成)
- 已生成NPC(显示详细信息)

### 3. 关系值可视化

NPC关系值用进度条+颜色编码:
- 70-100: 绿色(盟友)
- 30-70: 蓝色(友好)
- -30-30: 灰色(中立)
- -70--30: 橙色(不满)
- -100--70: 红色(敌对)

### 4. 消息类型标签

历史查看器中每条消息都有标签:
- 对话(默认)
- 选择(用户操作)
- 章节(生成内容)
- 设定修改(系统操作)

---

## 下一步工作

### 短期(优先)

1. **后端API实现** - 为新组件提供数据接口
2. **状态管理** - 使用React Context或Zustand
3. **实时更新** - WebSocket连接NPC状态变化

### 中期

1. **探索进度页面** - 可视化主角的世界发现进度
2. **线索看板** - 展示已发现线索、证据链、伏笔债务
3. **健康度仪表盘** - 线索经济健康度、审计通过率

### 长期

1. **可视化编辑器** - 拖拽式事件线编辑
2. **关系网图谱** - NPC关系网络可视化
3. **多语言支持** - i18n国际化

---

## 总结

本次前端改进完整实现了:

- ✅ **可编辑设定系统** - 动态管理世界观、主角、地点、势力
- ✅ **会话历史管理** - 查看完整对话，支持分支，导出Markdown
- ✅ **NPC生命周期管理** - 种子池、活跃NPC、关系值、互动统计

界面从"简单生成器"升级为"完整创作工作台"! 🎉

用户现在可以:
1. 编辑和管理小说设定
2. 查看完整创作历史
3. 管理NPC种子和活跃角色
4. 一目了然地了解故事状态

配合后端的全局导演架构，形成完整的智能叙事引擎！
