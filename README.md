# 四六级学习助手 · CETTrainer

一个**纯本地运行**的 Windows 桌面英语学习软件，面向大学英语四六级（CET-4 / CET-6）备考。
界面基于 Python 标准库 `tkinter` + `Canvas` 手写绘制，**除 PyInstaller 外零第三方依赖**。

> 源码从已发布的 `CETTrainer.exe` 反编译还原，并在还原版上完成了整套 UI 重设计，
> 逻辑层（`store` / `tts` / `cetpack` / 题库数据）与原版保持一致，未做破坏性改动。

---

## 功能一览

界面采用「左侧导航 + 白色顶栏 + 卡片内容区」的三段式布局，共 **14 个功能页面**，
导航分为四组：**学习 / 训练 / 资料 / 进度**。

### 学习

| 页面 | 说明 |
|---|---|
| 词汇记忆 | Georgia 40 号大字号居中显示单词，例句区默认折叠不占位；底部 6 个语义按钮；空词库时按钮自动置灰 |
| 单词本 | 左右分栏 + 搜索框自动聚焦；列表为空时连同滚动条一起隐藏的空状态 |
| 错题本 | 表格 + 右侧 376px 详情卡（彩色卡片分块呈现） |

### 训练

| 页面 | 说明 |
|---|---|
| 听写练习 | 左侧 326px 音频卡（四个等宽按钮 + 环形 Meter 待判分占位）+ 右侧作答卡（答案 chip 切分） |
| 听力练习 | 左侧 368px 音频卡（原文默认遮盖）+ 右侧题目卡（选项整行可点，双击后错项标红） |
| 阅读理解 | `PanedWindow` 上下分栏（初始 46%），Georgia 12 号带行距正文 |
| 选词填空 | 左文章（空位内联「◯ ◯ ◯」+ 切分后插入答案）+ 右 356px 备选下拉 |
| 翻译练习 | 三段式：中文题干 / 译文输入框 / 切分结果卡（初始不占位）；提示词 chip 着色 |
| 写作模板 | 左三栏（题干 / 写作卡 / 结果）+ 右 392px 模板卡（分段、插入按钮 + 字数计时） |

### 资料

| 页面 | 说明 |
|---|---|
| 短语匹配 | Georgia 28 号大字号短语居中；底部 6 个释义按钮；空状态用 `place` 淡入淡出 |
| 语法知识 | 左 272px 自绘章节列表（圆角选中态 + 主色指示条 + 完成勾）+ 右侧折叠彩色块（规则 / 错句 / 正解 / 记忆点） |

### 进度

| 页面 | 说明 |
|---|---|
| 模拟测试 | 工具栏两行（倒计时 + 剩余时长 / 开始 + 交卷）；居中空状态 |
| 题库导入 | `Segment` 选择题型与等级；左滚动加载区 + 右 520px 题库表格（短标签拦截长文案）；备胎线程重组织 |
| 学习统计 | 三个环形 Meter（高级 / 四级 / 六级掌握度）+ 数字卡片网格 + 错词 chip 条 + 练习记录表 |

---

## 题库规模

题库全部以 **Python 源码形式**内置于 `data_*.py`，不依赖外部数据文件。

| 模块 | 内容 | 条数 |
|---|---|---|
| `data_vocab.py` | CET-4 核心词汇 | 4,105 |
| | CET-6 核心词汇 | 2,153 |
| | CET-4 扩展词汇 | 140 |
| | CET-6 扩展词汇 | 100 |
| `data_cet4_big.py` | CET-4 扩充词库 | 3,699 |
| `data_cet6_big.py` | CET-6 扩充词库 | 1,914 |
| `data_gaokao.py` | 高考词库 | 3,665 |
| `data_phrases.py` | 短语库 | 1,800 |
| `data_sentences.py` | 听写句 / 翻译句 | 81 / 30 |
| | 完形 / 阅读篇章 | 5 / 5 |
| `data_extra.py` | 补充句 / 翻译 / 完形 / 阅读 | 30 / 15 / 3 / 3 |
| `data_listening.py` | 听力题 | 8 |
| `data_writing.py` | 写作话题 / 模板 / 升级词 / 连接词 | 12 / 6 / 15 / 6 |
| `data_grammar.py` | 语法知识点 | 21 |

**词汇合计约 16,076 条**，短语 1,800 条，另有听写、听力、阅读、完形、翻译、写作、语法等整卷资源。

> `cet_pack.json`（题库打包产物，约 2.5 MB）**刻意不进版本库**，
> 它可由 `data_*.py` 通过 `build_pack.py` 稳定重建。

---

## 运行

### 直接运行（开发）

需要 Python 3.10+（开发与打包环境为 3.15），无需安装任何第三方包：

```bash
python app.py
```

### 打包成单文件 exe

```bash
build.bat
```

`build.bat` 会依次：
1. 运行 `build_pack.py` 生成 `cet_pack.json`；
2. 调用 PyInstaller 以 `--onefile --windowed` 打包（含 25 个 `--hidden-import`）；
3. 产物输出到 `dist\CETTrainer.exe`（约 16 MB）。

> 脚本默认 Python 路径为 `E:\Python315\python.exe`，如路径不同请修改 `build.bat` 顶部的 `PY` 变量。
>
> **注意**：`build.bat` 必须保持 CRLF 行尾。改成 LF 后 cmd 无法识别 `^` 续行符，
> 会把参数当成独立命令执行，导致打包失败。

---

## 语音朗读（TTS）

内置**三级降级**合成策略，网络状况变化时自动切换，无需用户干预：

1. **Edge 在线神经网络语音**（与 Edge 浏览器、大型投影仪同款，真人级音质）
2. **百度在线合成**（`fanyi.baidu.com/gettts`，仅中文可用）
3. **本机 SAPI5**（离线兜底）

- `tts_edge.py` 为**零依赖标准库实现**：手写 WebSocket 客户端，完整移植 `edge-tts` 7.3.1 的
  `Sec-MS-GEC` 签名算法（DRM 系列标志位 + Base64 + SHA256 混合）。
  > 切勿图省事退化成简单 `SHA256(ticks + token)`，那样会被服务端 403 拒绝。
- 内置 **10 个音色**：Ava / Andrew / Emma / Brian（美音）、Sonia / Ryan（英音）、
  晓晓 / 希希 / 云冲 / 康翔（中文）。
- Edge 连续失败 3 次后自动置 `use_edge = False`，避免每次操作都等待超时。
- UI 的 1~9 速度档映射为 `rate = level - 5`（−4…+4），在线语音同样生效。

---

## 项目结构

```
.
├── app.py                 # 主入口：侧边导航 + 顶栏 + 页面宿主 NavHost
├── ui_common.py           # 设计 token 与自绘组件（圆角卡片/按钮/图标/进度环/空状态）
├── store.py               # 学习数据持久化（SQLite）
├── tts.py                 # 语音合成三级降级调度
├── tts_edge.py            # Edge 在线语音（零依赖标准库实现）
├── cetpack.py             # 题库打包 / 解包
├── importer.py            # 题库导入
├── build_pack.py          # 由 data_*.py 重建 cet_pack.json
├── build.bat              # PyInstaller 一键打包
├── smoke_test.py          # 14 个页面的冒烟测试
├── models.json            # 模型清单
├── cet.ico / icon_app*.png# 应用图标（Lucide graduation-cap，暖红渐变底）
├── data_*.py              # 题库源码（14 个模块）
└── pages/                 # 14 个功能页面
    ├── page_vocab.py          # 词汇记忆
    ├── page_wordbook.py       # 单词本
    ├── page_wrong.py          # 错题本
    ├── page_dictation.py      # 听写练习
    ├── page_listening.py      # 听力练习
    ├── page_reading.py        # 阅读理解
    ├── page_cloze.py          # 选词填空
    ├── page_translate.py      # 翻译练习
    ├── page_writing.py        # 写作模板
    ├── page_phrase.py         # 短语匹配
    ├── page_grammar.py        # 语法知识
    ├── page_mock.py           # 模拟测试
    ├── page_import.py         # 题库导入
    └── page_stats.py          # 学习统计
```

---

## 设计说明

设计 token 集中在 `ui_common.py` 顶部，页面代码禁止再写十六进制颜色。

- **配色**：暖红主色系（`#E8455F` / `#CF3752` / `#A82A42`）+ 白卡 + 灰阶文字。
  参考对象：ttkbootstrap（语义化色彩 / Meter / 8px 网格）、Sun Valley ttk（圆角 / 主色高亮 /
  淡雅卡片）。
- **间距**：4px 递进（4 / 8 / 12 / 16 / 24），`PAGE_PAD=16`、`CARD_PAD=16`、`GAP=12`。
- **圆角**：卡片 12、按钮 8、输入框 8、chip 999（全圆角）。
- **字体**：全局 `Microsoft YaHei UI`；单词大字用 Georgia，音标与等宽用 Consolas。

自绘组件包括：真圆角矩形 `round_rect()`、`RoundedFrame` / `card()`、
`RoundButton` / `button()`、31 个线性图标 `icon()` / `Icon`、
分段选择器 `Segment` / `segment()`、环形进度 `Meter` / `meter()`、
统一空状态 `empty_state()`、自动换行 `wrap_label()`、胶囊 `chip()`、
自动隐藏滚动条 `scrollable()`。

---

## 辅助脚本

| 脚本 | 用途 |
|---|---|
| `_backup.py` | 生成带时间戳的源码快照 zip（双位置写入）；关键文件缺失时中止打包。`--list` 列出已有快照 |
| `_clean.py` / `_clean.bat` | 清理 PyInstaller onefile 残留的 `_MEI*` 解压目录（约 27 MB/次） |
| `_smoke.py` | 14 个页面实例化冒烟测试 |
| `_shots_all.py` | 批量截取全部 14 个页面 → `shots/all/p_<key>.png` |
| `_exe_shot.py` | 启动 `dist\CETTrainer.exe` 并整窗截图 → `shots/exe_shot.png` |
| `_build_icon.py` 等 | 图标资源生成（SVG → 多尺寸 PNG/ICO） |

> `_clean.py` 通过 `CreateToolhelp32Snapshot` + `Module32First` 读出进程**实际加载**的 `_MEI` 目录并跳过，
> 实测程序运行时清理，程序本身不受任何影响。只按名字白名单匹配（`_MEI*` / `cet_tts_*`），不做模糊扫描。
> 扫描范围覆盖 `TEMP` / `TMP` / `LOCALAPPDATA\Temp` / `Windows\Temp` 及其下一层。

---

## 已知事项

- **运行时数据不进版本库**：`cet_data/progress.db` 跟随 exe 所在目录，已由 `.gitignore` 排除。
- **`--runtime-tmpdir` 已移除**：该参数按「当前工作目录」解析，双击桌面快捷方式启动时 CWD 是
  `C:\Windows\System32`（无写权限），程序会直接启动失败。现改用默认系统 TEMP，
  配合 `app.py` 后台线程 `_sweep_old_mei()` 自动清理 6 小时以上的旧 `_MEI` 目录。
- **打包环境**：Windows + Python 3.15 + PyInstaller；未在 Linux / macOS 验证。

---

## 许可

仓库未附许可证文件。如需开源发布，建议补充 `LICENSE`（例如 MIT），
并在发布前确认 `tts_edge.py` 中移植的 `Sec-MS-GEC` 签名算法的上游项目许可。
