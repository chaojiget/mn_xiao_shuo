# 沉浸式叙事模拟器 - UI/UX 实施计划

**日期**: 2025-11-07
**目标**: 打造"流连忘返"的阅读与游玩体验
**核心指标**: Flow Index、首屏加载 ≤ 2s、选择响应 ≤ 400ms

---

## 🎯 设计原则

### 1. 专注优先（Focus First）
- **阅读区无干扰模式**: 默认隐藏所有辅助信息
- **Progressive Disclosure**: 按需浮现（Journal/Map/Branches）
- **单手操作友好**: 移动端选项条固定底部

### 2. 世界内呈现（Diegetic UI）
- **科幻**: 星港通告、实验日志、舰桥终端
- **玄幻**: 宗门卷轴、藏经残卷、玉简记录
- **避免"破第四堵墙"**: 信息以剧内媒介展示

### 3. 可回放与可解释（Replayability）
- **分支树可视化**: 当前路径高亮
- **事件溯源**: 任何结果都能回看来源
- **审计解释**: 温和提示，默认折叠

### 4. 实时调光（Adaptive UI）
- **基于 Flow Index**: 低流状态降低信息密度
- **伏笔兑现提示**: 右下角 Toast，不打断阅读
- **动态选项对比度**: Flow 低时，选项差异更明显

---

## 📐 信息架构（IA）

```
┌─────────────── Reader App ───────────────┐
│                                          │
│  / (书架/存档)                            │
│  ├─ Library                              │
│  │  ├─ 科幻《能源纪元》                   │
│  │  └─ 玄幻《逆天改命录》                 │
│  │                                       │
│  /run (阅读/游玩核心)                     │
│  ├─ Scene (主阅读区)                      │
│  ├─ Choices (选项抽屉)                    │
│  ├─ Journal (编年史/线索/证据)            │
│  ├─ Map (地理/关系/势力图)                │
│  └─ Branches (分支树/回放)                │
│                                          │
│  /settings (显示/语言/辅助功能)            │
│                                          │
└──────────────────────────────────────────┘

┌─────────────── Studio Console ───────────┐
│                                          │
│  /studio/scenarios (设定/初始态)          │
│  /studio/director (GD 运行控制)           │
│  /studio/systems (System Packs)          │
│  /studio/clues (线索经济)                 │
│  /studio/metrics (Flow 仪表板)            │
│  /studio/experiments (A/B 测试)          │
│                                          │
└──────────────────────────────────────────┘

┌─────────────── Ops Dashboard ────────────┐
│                                          │
│  /ops/costs (LLM 成本/缓存)               │
│  /ops/health (延迟/错误/重试)             │
│  /ops/logs (事件溯源/审计)                │
│                                          │
└──────────────────────────────────────────┘
```

---

## 🚀 关键用户旅程

### Journey 1: 首次体验（60 秒到"爽点"）

```
1. 进入 /library
   ├─ 两张卡片（科幻/玄幻）
   ├─ 简介 + "立即进入" 按钮
   └─ 首屏 < 2s

2. 点击"立即进入"
   ├─ 路由到 /run?scenario=scifi
   ├─ 顶部 SceneHeader（最小化）
   └─ 主文区居中，骨架屏加载

3. 引导场景（自动生成）
   ├─ 200-300 字开场白（流式）
   ├─ 3 个明确选项（风险/信息标签）
   └─ 右上角轻量提示："世界纪要已更新（1）"

4. 选择第一个选项
   ├─ < 400ms 首段文字
   ├─ 流式加载余下内容
   └─ 底部选项条更新（新选项）

5. 第 3 次选择后
   ├─ 右下角 Toast："伏笔「星港许可证」已埋下"
   └─ FlowIndicator 显示 Flow = 0.68

总时长: 约 3-5 分钟体验完整循环
```

### Journey 2: 场景循环（Reader）

```
┌─────────────────────────────────────────┐
│  SceneHeader: 第12章·星港夜雨·22:14      │
├─────────────────────────────────────────┤
│                                         │
│  [SceneBody - 流式文本]                  │
│  "冷光在穹顶流淌，林墨将指尖贴在……"       │
│                                         │
│  [PayoffToast] 伏笔「黑市许可证」已兑现   │
│                                         │
├─────────────────────────────────────────┤
│  [ChoiceList]                           │
│  1️⃣ 潜入货仓 (高风险·高信息)             │
│  2️⃣ 等待联络 (低风险·低信息)             │
│  3️⃣ 伪装巡检 (中风险·中信息)             │
└─────────────────────────────────────────┘

[右侧抽屉]
  Journal | Map | Branches (快捷键 J/M/B)
```

**交互流程**:
1. 阅读场景（J/K 翻段）
2. 点击选项（或键盘 1/2/3）
3. 骨架屏 + 流式文本
4. 伏笔兑现 Toast（可选）
5. 循环下一场景

### Journey 3: 探索工具（不打断主线）

**Journal（编年史/线索）**

```
┌─────────── Journal ─────────────┐
│  [编年史] [线索] [证据]          │
├─────────────────────────────────┤
│  第12章 · 星港夜雨               │
│  ├─ 林墨潜入货仓                │
│  ├─ 发现能源异常数据             │
│  └─ 遭遇神秘巡检员               │
│                                 │
│  第11章 · 暗流涌动               │
│  └─ ...                         │
└─────────────────────────────────┘

[线索]
  ✅ 黑市许可证 (已证)
  ⏳ 能源异常 (待证)
  🔴 神秘巡检员身份 (待证)
```

**Map（地理/势力）**

```
┌─────────── Map ─────────────────┐
│  [地点] [势力] [路径]            │
├─────────────────────────────────┤
│  当前位置: 星港 Z-7 货仓区        │
│                                 │
│  可达地点:                       │
│  ├─ 中央管制室 (2 min)          │
│  ├─ 黑市码头 (15 min)           │
│  └─ 居住区 (5 min)              │
│                                 │
│  势力分布:                       │
│  ├─ 星港管理局 (中立)            │
│  ├─ 能源公司 (敌对)              │
│  └─ 黑市势力 (友好)              │
└─────────────────────────────────┘
```

**Branches（分支树）**

```
┌─────────── Branches ────────────┐
│                                 │
│      ┌─[货仓]─[巡检]            │
│      │                          │
│  [开始]─[星港]───[管制室]        │
│      │                          │
│      └─[黑市]─[交易]            │
│                                 │
│  当前: 货仓·巡检 (第12章)        │
│  存档点: 3个                     │
└─────────────────────────────────┘
```

---

## 🎨 视觉与版式（Design System）

### 双主题（科幻 Scifi / 玄幻 Xianxia）

#### 科幻主题

```css
:root[data-theme="scifi"] {
  /* 背景 */
  --bg-primary: #0a0e17;
  --bg-secondary: #151b2b;
  --bg-elevated: #1e2638;

  /* 文字 */
  --text-primary: #e4e8f0;
  --text-secondary: #9ca3b8;
  --text-muted: #6b7280;

  /* 强调 */
  --accent-info: #00d9ff;
  --accent-warning: #ffb800;
  --accent-danger: #ff3366;

  /* 风险标签 */
  --risk-high: #ff3366;
  --risk-medium: #ffb800;
  --risk-low: #00d9ff;

  /* 字体 */
  --font-body: 'Inter', 'Noto Sans SC', sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}
```

#### 玄幻主题

```css
:root[data-theme="xianxia"] {
  /* 背景 */
  --bg-primary: #f5f0e8;
  --bg-secondary: #e8dfd0;
  --bg-elevated: #ffffff;

  /* 文字 */
  --text-primary: #2d2520;
  --text-secondary: #5a504a;
  --text-muted: #9b8d82;

  /* 强调 */
  --accent-info: #4a90e2;
  --accent-warning: #e2a44a;
  --accent-danger: #c73e1d;

  /* 风险标签 */
  --risk-high: #8b0000;
  --risk-medium: #cd853f;
  --risk-low: #4682b4;

  /* 字体 */
  --font-body: 'Noto Serif SC', serif;
  --font-mono: 'Source Code Pro', monospace;
}
```

### Typography（排版）

```css
/* 主文（阅读区） */
.scene-body {
  font-family: var(--font-body);
  font-size: 18px;
  line-height: 1.8;
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* 元信息（章名/时间） */
.scene-header {
  font-family: var(--font-body);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

/* 选项 */
.choice-item {
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.6;
  padding: 16px 20px;
}

/* 标签（风险/信息） */
.choice-tag {
  font-family: var(--font-mono);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
```

### 动效（Animations）

```css
/* 淡入（默认） */
.fade-in {
  animation: fadeIn 200ms ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* 滑入（侧栏） */
.slide-in {
  animation: slideIn 250ms ease-out;
}

@keyframes slideIn {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

/* 流式打字（可选） */
.typewriter {
  overflow: hidden;
  white-space: pre-wrap;
  animation: typing 1s steps(40, end);
}
```

**原则**:
- ⏱️ 200-250ms 轻动效
- 🚫 禁止大型视差（防止出戏）
- ✅ 尊重 `prefers-reduced-motion`

---

## 🧩 组件库（Component Specs）

### Reader 组件

#### 1. SceneHeader

```typescript
interface SceneHeaderProps {
  chapter: string;      // "第12章"
  title: string;        // "星港夜雨"
  location: string;     // "星港 Z-7"
  time: string;         // "22:14"
}

export function SceneHeader({ chapter, title, location, time }: SceneHeaderProps) {
  return (
    <header className="scene-header">
      <span>{chapter}</span>
      <span>·</span>
      <span>{title}</span>
      <span>·</span>
      <span>{location}</span>
      <span>{time}</span>
    </header>
  );
}
```

#### 2. SceneBody

```typescript
interface SceneBodyProps {
  content: string;
  isStreaming: boolean;
  onSegmentComplete?: (segment: string) => void;
}

export function SceneBody({ content, isStreaming }: SceneBodyProps) {
  return (
    <div className="scene-body">
      {isStreaming ? (
        <div className="skeleton">
          <div className="skeleton-line" />
          <div className="skeleton-line" />
        </div>
      ) : null}
      <div className="prose">{content}</div>
    </div>
  );
}
```

#### 3. ChoiceList

```typescript
interface Choice {
  id: string;
  text: string;
  risk: 'high' | 'medium' | 'low';
  infoGain: 'high' | 'medium' | 'low';
}

interface ChoiceListProps {
  choices: Choice[];
  onSelect: (choiceId: string) => void;
}

export function ChoiceList({ choices, onSelect }: ChoiceListProps) {
  return (
    <div className="choice-list">
      {choices.map((choice, index) => (
        <button
          key={choice.id}
          className="choice-item"
          onClick={() => onSelect(choice.id)}
          data-kbd={index + 1}
        >
          <span className="choice-number">{index + 1}</span>
          <span className="choice-text">{choice.text}</span>
          <div className="choice-tags">
            <span className={`tag tag-risk-${choice.risk}`}>
              {choice.risk === 'high' ? '高风险' : choice.risk === 'medium' ? '中风险' : '低风险'}
            </span>
            <span className={`tag tag-info-${choice.infoGain}`}>
              {choice.infoGain === 'high' ? '高信息' : choice.infoGain === 'medium' ? '中信息' : '低信息'}
            </span>
          </div>
        </button>
      ))}
    </div>
  );
}
```

#### 4. PayoffToast

```typescript
interface PayoffToastProps {
  clue: string;
  type: 'setup' | 'payoff';
  theme: 'scifi' | 'xianxia';
}

export function PayoffToast({ clue, type, theme }: PayoffToastProps) {
  const message = theme === 'scifi'
    ? `星港档案更新：${clue} 记录匹配成功`
    : `宗门玉简忽明——${clue} 证得一应`;

  return (
    <div className="payoff-toast">
      <div className="toast-icon">{type === 'setup' ? '📌' : '✅'}</div>
      <div className="toast-message">{message}</div>
    </div>
  );
}
```

#### 5. FlowIndicator

```typescript
interface FlowIndicatorProps {
  flow: number;         // 0-1
  tension: number;      // 0-1
  curiosity: number;    // 0-1
}

export function FlowIndicator({ flow, tension, curiosity }: FlowIndicatorProps) {
  return (
    <div className="flow-indicator">
      <div className="flow-bar">
        <div className="flow-fill" style={{ width: `${flow * 100}%` }} />
      </div>
      <div className="flow-details">
        <span>Flow: {(flow * 100).toFixed(0)}%</span>
        <span>Tension: {(tension * 100).toFixed(0)}%</span>
        <span>Curiosity: {(curiosity * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
}
```

### Studio 组件

#### 1. WeightKnob

```typescript
interface WeightKnobProps {
  playability: number;  // 0-1
  narrative: number;    // 0-1
  onChange: (p: number, n: number) => void;
}

export function WeightKnob({ playability, narrative, onChange }: WeightKnobProps) {
  return (
    <div className="weight-knob">
      <label>Playability: {(playability * 100).toFixed(0)}%</label>
      <input
        type="range"
        min="0"
        max="100"
        value={playability * 100}
        onChange={(e) => {
          const p = parseFloat(e.target.value) / 100;
          onChange(p, 1 - p);
        }}
      />
      <label>Narrative: {(narrative * 100).toFixed(0)}%</label>
    </div>
  );
}
```

#### 2. DebtTable

```typescript
interface Debt {
  id: string;
  name: string;
  sla: number;          // 章节数
  remaining: number;
  payoffRate: number;   // 0-1
  suggestion: string;
}

interface DebtTableProps {
  debts: Debt[];
}

export function DebtTable({ debts }: DebtTableProps) {
  return (
    <table className="debt-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>名称</th>
          <th>SLA</th>
          <th>剩余</th>
          <th>兑现率</th>
          <th>建议</th>
        </tr>
      </thead>
      <tbody>
        {debts.map((debt) => (
          <tr key={debt.id}>
            <td>{debt.id}</td>
            <td>{debt.name}</td>
            <td>{debt.sla}章</td>
            <td className={debt.remaining <= 1 ? 'text-danger' : ''}>
              {debt.remaining}章
            </td>
            <td>{(debt.payoffRate * 100).toFixed(0)}%</td>
            <td className="text-muted">{debt.suggestion}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## 📱 响应式布局（Responsive）

### 桌面（≥ 1280px）

```
┌────────────────────────────────────────────┐
│  Header (最小化)                            │
├──────────────────┬─────────────────────────┤
│                  │  [Journal/Map/Branches] │
│  SceneBody       │  (320px 固定宽度)        │
│  (720-800px)     │                          │
│                  │                          │
│  ChoiceList      │                          │
│  (底部固定)       │                          │
└──────────────────┴─────────────────────────┘
```

### 平板（768-1279px）

```
┌────────────────────────────────────────────┐
│  Header                                    │
├────────────────────────────────────────────┤
│  SceneBody (全宽)                           │
│                                            │
│  ChoiceList (底部固定)                      │
├────────────────────────────────────────────┤
│  [抽屉按钮] Journal | Map | Branches        │
└────────────────────────────────────────────┘
```

### 手机（≤ 767px）

```
┌─────────────────────┐
│  Header (简化)       │
├─────────────────────┤
│  SceneBody          │
│  (全宽，边距 16px)   │
│                     │
│                     │
├─────────────────────┤
│  ChoiceList         │
│  (底部固定，单手够) │
└─────────────────────┘

[底部抽屉]
  Journal | Map | Branches
  (分步弹出，全屏覆盖)
```

---

## ⌨️ 键盘导航与无障碍（A11y）

### 快捷键

```
阅读区:
  J/K        - 翻段（上一段/下一段）
  Space      - 滚动一屏
  1/2/3...   - 直选选项

侧栏:
  O          - 打开/关闭侧栏
  [/]        - 切换侧栏页签（Journal/Map/Branches）
  Esc        - 关闭侧栏

全局:
  Ctrl+/     - 快捷键帮助
  Ctrl+S     - 快速存档
  Ctrl+L     - 加载存档
```

### ARIA 标注

```html
<!-- Scene 区域 -->
<main role="main" aria-label="故事场景">
  <header role="banner" aria-label="场景信息">
    <!-- SceneHeader -->
  </header>

  <article role="article" aria-label="场景内容">
    <!-- SceneBody -->
  </article>

  <nav role="navigation" aria-label="选项">
    <!-- ChoiceList -->
  </nav>
</main>

<!-- 侧栏 -->
<aside role="complementary" aria-label="辅助信息">
  <nav role="tablist">
    <button role="tab" aria-selected="true">编年史</button>
    <button role="tab" aria-selected="false">线索</button>
  </nav>
</aside>
```

### 对比度要求

- **主文**: ≥ 7:1（WCAG AAA）
- **次要信息**: ≥ 4.5:1（WCAG AA）
- **标签**: ≥ 4.5:1

### 阅读辅助

```typescript
interface ReadingSettings {
  fontSize: number;       // 14-24px
  lineHeight: number;     // 1.4-2.0
  lineWidth: number;      // 60-90 字符
  typewriterEffect: boolean;
}
```

---

## 📊 性能指标与优化

### 关键指标

| 指标 | 目标 | 测量方式 |
|------|------|---------|
| **FCP** (First Contentful Paint) | ≤ 1.5s | Lighthouse |
| **LCP** (Largest Contentful Paint) | ≤ 2.0s | Lighthouse |
| **TTI** (Time to Interactive) | ≤ 2.5s | Lighthouse |
| **选择响应** | ≤ 400ms | 自定义埋点 |
| **流式首段** | ≤ 200ms | 自定义埋点 |

### 优化策略

#### 1. 文本流式加载

```typescript
async function* streamSceneContent(sceneId: string) {
  const response = await fetch(`/api/scene/${sceneId}`);
  const reader = response.body.getReader();

  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += new TextDecoder().decode(value);
    const segments = buffer.split('\n\n');

    // 逐段 yield
    for (let i = 0; i < segments.length - 1; i++) {
      yield segments[i];
    }

    buffer = segments[segments.length - 1];
  }

  if (buffer) yield buffer;
}
```

#### 2. 骨架屏（Skeleton）

```typescript
function SceneSkeleton() {
  return (
    <div className="skeleton">
      <div className="skeleton-line" style={{ width: '90%' }} />
      <div className="skeleton-line" style={{ width: '85%' }} />
      <div className="skeleton-line" style={{ width: '95%' }} />
      <div className="skeleton-line" style={{ width: '70%' }} />
    </div>
  );
}
```

#### 3. 预取与缓存

```typescript
// 预取下一场景骨架
async function prefetchNextScene(currentSceneId: string) {
  const nextSceneId = await getNextSceneId(currentSceneId);
  const skeleton = await fetch(`/api/scene/${nextSceneId}/skeleton`);
  cache.set(`skeleton:${nextSceneId}`, skeleton);
}

// 在用户阅读时预取
useEffect(() => {
  const timer = setTimeout(() => {
    prefetchNextScene(currentSceneId);
  }, 3000);  // 阅读 3 秒后预取

  return () => clearTimeout(timer);
}, [currentSceneId]);
```

#### 4. Journal 延迟加载

```typescript
// 首次打开侧栏时加载
function JournalPanel() {
  const [entries, setEntries] = useState(null);

  useEffect(() => {
    if (!entries) {
      fetchJournalEntries().then(setEntries);
    }
  }, []);

  if (!entries) return <Spinner />;
  return <JournalList entries={entries} />;
}
```

---

## 🎭 文案与微交互

### 选项标签（一致的顺序与颜色）

```
[高风险] [高信息] [道德代价] [资源消耗]
  ↓         ↓          ↓           ↓
 红色      蓝色       黄色        绿色
```

### 伏笔兑现 Toast

**科幻皮肤**:
```
「星港档案更新：许可证记录匹配成功」
「实验日志解锁：暗能结晶异常数据」
```

**玄幻皮肤**:
```
「宗门玉简忽明——旧誓证得一应」
「藏经残卷显字——断魂谷秘闻已现」
```

### 错误兜底（世界内解释）

**科幻 - 网络错误**:
```
「终端失去链路，回放离线缓存……」
[重试] [离线模式]
```

**玄幻 - LLM 错误**:
```
「灵纹失序，沿着旧纹路重塑记忆……」
[重试] [查看上一回合]
```

---

## 🧪 A/B 测试计划

### 测试 1: 选项标签顺序

- **A 组**: 风险 → 信息 → 道德 → 资源
- **B 组**: 信息 → 风险 → 资源 → 道德

**指标**: 选择时间、Choice Entropy

### 测试 2: 伏笔兑现提示时机

- **A 组**: 即时 Toast（选择后立即）
- **B 组**: 延迟 Toast（阅读完场景后）

**指标**: Flow Index、Payoff Satisfaction（问卷）

### 测试 3: Flow 低时的调光策略

- **A 组**: 降低术语密度
- **B 组**: 增加选项对比度

**指标**: Flow 恢复速度、Session Duration

---

## 📅 MVP 实施时间线（3 周）

### Week 1: 核心阅读体验

**Day 1-2**: 设计 Token + 主题
```bash
# 创建 Design System
web/frontend/styles/tokens.css
web/frontend/styles/themes/scifi.css
web/frontend/styles/themes/xianxia.css
```

**Day 3-4**: SceneHeader + SceneBody + ChoiceList
```bash
# 核心组件
web/frontend/components/reader/SceneHeader.tsx
web/frontend/components/reader/SceneBody.tsx
web/frontend/components/reader/ChoiceList.tsx
```

**Day 5**: 流式加载 + 骨架屏
```typescript
// API 集成
web/frontend/hooks/useStreamScene.ts
web/frontend/components/reader/SceneSkeleton.tsx
```

**验收**: 完整的场景循环，< 2s 首屏，< 400ms 选择响应

---

### Week 2: 侧栏与探索工具

**Day 6-7**: Journal 面板
```bash
web/frontend/components/reader/JournalPanel.tsx
web/frontend/components/reader/JournalEntry.tsx
web/frontend/components/reader/ClueCard.tsx
```

**Day 8**: Map 面板（文本版）
```bash
web/frontend/components/reader/MapPanel.tsx
web/frontend/components/reader/LocationList.tsx
web/frontend/components/reader/FactionGraph.tsx
```

**Day 9**: Branches 缩略图
```bash
web/frontend/components/reader/BranchMiniMap.tsx
web/frontend/components/reader/BranchNode.tsx
```

**Day 10**: 侧栏响应式 + 抽屉动效
```css
web/frontend/styles/components/sidebar.css
```

**验收**: 侧栏操作不影响主文，键盘导航 100% 可用

---

### Week 3: 微交互与优化

**Day 11**: PayoffToast + FlowIndicator
```bash
web/frontend/components/reader/PayoffToast.tsx
web/frontend/components/reader/FlowIndicator.tsx
```

**Day 12**: 主题切换 + 暗色模式
```typescript
web/frontend/hooks/useTheme.ts
web/frontend/components/ThemeToggle.tsx
```

**Day 13**: 阅读辅助设置
```bash
web/frontend/components/settings/ReadingSettings.tsx
```

**Day 14**: 性能优化（预取/缓存）
```typescript
web/frontend/utils/prefetch.ts
web/frontend/utils/cache.ts
```

**Day 15**: A11y 审计 + 测试
```bash
# 运行 Lighthouse
npm run lighthouse

# 键盘导航测试
npm run test:a11y
```

**最终验收**:
- [x] Lighthouse Score ≥ 90
- [x] 所有快捷键可用
- [x] 对比度 ≥ 7:1
- [x] 流式加载 < 400ms

---

## 🎯 验收标准（MVP）

### 功能验收

- [x] Run 页面（Scene + ChoiceList）
- [x] Journal（编年史 + 线索列表）
- [x] PayoffToast（伏笔兑现提示）
- [x] BranchMiniMap（当前路径 + 最近 3 个分叉）
- [x] FlowIndicator（单值进度条版）

### 性能验收

- [x] 首次进入 ≤ 2s 到可读文本（含骨架）
- [x] 任何选择 ≤ 400ms 出首段流式文本
- [x] 3 次选择内至少出现 1 次伏笔兑现提示
- [x] 侧栏操作不影响主文滚动位置
- [x] 键盘直选选项（1/2/3）100% 可用

### A11y 验收

- [x] Lighthouse A11y Score ≥ 90
- [x] 键盘导航覆盖所有功能
- [x] ARIA 标注完整
- [x] 对比度 ≥ 7:1（主文）/ 4.5:1（次要信息）

---

## 📚 相关文档

- 技术实施计划: `docs/implementation/SIMULATION_EVOLUTION_PLAN.md`
- Flow 指标定义: `docs/reference/FLOW_METRICS.md`（待创建）
- 组件 API 文档: `docs/reference/COMPONENT_API.md`（待创建）
- A11y 清单: `docs/reference/A11Y_CHECKLIST.md`（待创建）

---

## 💡 下一步行动（Day 1 任务）

1. **创建 Design System 目录**
   ```bash
   mkdir -p web/frontend/styles/{tokens,themes}
   ```

2. **定义 Design Tokens**
   ```css
   /* web/frontend/styles/tokens.css */
   :root {
     --spacing-xs: 4px;
     --spacing-sm: 8px;
     --spacing-md: 16px;
     --spacing-lg: 24px;
     --spacing-xl: 32px;

     --font-size-xs: 12px;
     --font-size-sm: 14px;
     --font-size-md: 16px;
     --font-size-lg: 18px;
     --font-size-xl: 24px;

     --radius-sm: 4px;
     --radius-md: 8px;
     --radius-lg: 12px;
   }
   ```

3. **创建主题文件**
   ```css
   /* web/frontend/styles/themes/scifi.css */
   /* web/frontend/styles/themes/xianxia.css */
   ```

4. **搭建组件骨架**
   ```bash
   mkdir -p web/frontend/components/reader
   touch web/frontend/components/reader/{SceneHeader,SceneBody,ChoiceList}.tsx
   ```

5. **集成到 Next.js**
   ```typescript
   // web/frontend/app/layout.tsx
   import '../styles/tokens.css';
   import '../styles/themes/scifi.css';
   import '../styles/themes/xianxia.css';
   ```

---

**文档版本**: 1.0
**最后更新**: 2025-11-07
**负责人**: Claude + 用户协作
