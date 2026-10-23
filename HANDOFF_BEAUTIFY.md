# 四六级学习助手 (CETTrainer) UI 审美提升 — 结果交接

## 状态：已完成（待老大验收）

源码已从 `CETTrainer.exe` 反编译全量还原，本次在还原出的源码上做了完整的 UI 重设计，
`E:\Python315\python.exe build.bat` 重打包通过，产物 `dist\CETTrainer.exe`（约 15.9 MB）已实测启动正常。

---

## 一、设计 token（全部集中定义在 `ui_common.py` 顶部，页面禁止再写裸 hex）

参考对象：ttkbootstrap（语义化意图配色 / Meter / 8px 栅格）、Sun Valley ttk（圆角、主色高亮选中态、
浅灰底+白卡）、墨墨背单词 / 不背单词（大字号单词卡、留白、进度环）。

### 色板（墨墨暖红体系，取代原「浅蓝 + 白卡」）
| 用途 | 变量 | 值 |
|---|---|---|
| 页面底色 | `BG` | `#F6F7F9` |
| 卡片底 | `CARD` / `CARD_SOFT` | `#FFFFFF` / `#FBFBFC` |
| 主色 | `PRIMARY` / `PRIMARY_DARK` / `PRIMARY_DEEP` | `#E8455F` / `#CF3752` / `#A82A42` |
| 主色浅底 | `PRIMARY_SOFT` / `PRIMARY_TINT` | `#FDEEF1` / `#FDF6F7` |
| 正文 | `TEXT` / `TEXT_MUTED` / `TEXT_FAINT` | `#1F2933` / `#6B7280` / `#9CA3AF` |
| 描边 | `BORDER` / `BORDER_SOFT` | `#E6E8EC` / `#F0F1F4` |
| 语义色 | `OK` / `OK_SOFT`、`WARN` / `WARN_SOFT`、`AMBER` / `AMBER_SOFT`、`INFO` / `INFO_SOFT` | 绿 / 红 / 琥珀 / 蓝，各配浅底 |

### 圆角 / 间距 / 字号
- 圆角：`R_CARD=12`、`R_BTN=8`、`R_INPUT=8`、`R_CHIP=999`（胶囊）
- 间距（8px 节奏）：`S_XS=4` `S_SM=8` `S_MD=12` `S_LG=16` `S_XL=24`；`PAGE_PAD=16` `CARD_PAD=16` `GAP=12`
- 字体族统一 `Microsoft YaHei UI`；`FONT_UI(10)` `FONT_UI_B` `FONT_SMALL(9)`
  `FONT_SUBTITLE(12,bold)` `FONT_TITLE(17,bold)` `FONT_HERO(26,bold)`
  `FONT_WORD=(Georgia,40,bold)` `FONT_WORD_MD=(28)` `FONT_PHON=(Consolas,12)`
  `FONT_MONO=(Consolas,11)` `FONT_EX=(Georgia,12)`

---

## 二、`ui_common.py` 新增/重写的核心组件

- `round_rect(canvas,…)`：**真圆弧**圆角矩形（四角按角度插值打点后连多边形）。
  ⚠ 不能用 `create_polygon(smooth=True)` —— Tk 的 smooth 是贝塞尔样条，会把直角顶点当控制点，
  圆角被完全抹平成直角。
- `RoundedFrame` / `card(parent)->(outer, inner)`：Canvas 绘制的圆角卡片。
  ⚠ Canvas 必须 `width=1, height=1` 起（默认请求尺寸 382×268 会把每张卡撑高，造成「卡内大片留白」）。
- `RoundButton` / `button(parent, text, command, kind, icon, height)`：自绘圆角按钮，
  `kind ∈ primary / ghost / danger / soft / text`；兼容旧的 `style="Primary.TButton"` 写法；
  文字宽度用 `tkfont.measure` 实测（不用字符数估算，否则中文被裁）。
- `icon(canvas, name, x, y, s, color)` / `Icon(parent, name, …)`：**24×24 网格 Canvas 手绘线性图标**，
  共 31 个（book/star/pen/headphone/music/doc/grid/swap/sheet/tag/brace/clock/import/chart/
  search/check/close/speaker/plus/arrow-left/arrow-right/trash/eye/bookmark/info/light/undo/
  refresh/play/edit/folder/save）。取代原先的彩色 emoji（emoji 破坏单色体系）。
  ⚠ 试过 Segoe MDL2 Assets 字体图标，语义匹配差且缺字检测不可靠，已弃用。
- `Segment` / `segment(parent, options, value, command)`：分段选择器（白底圆角选中块 + 主色粗体字），
  取代页面里成排的 `ttk.Radiobutton`。
- `Meter` / `meter(parent, size, thickness, value, caption)`：环形进度，取代普通进度条。
- `empty_state(parent, icon, title, desc, action_text, action_command)`：统一空状态（线性图标 + 标题 + 说明 + 可选按钮）。
- `wrap_label(parent, …)`：绑定 `<Configure>` 自动重算 `wraplength`，解决固定换行宽度被裁的问题。
- `chip(parent, text, …)`：胶囊标签。
- `scrollable(parent, bg, autohide=True)`：自动隐藏不必要滚动条；
  ⚠ Canvas 同样必须 `width=1, height=1`，否则破坏 `PanedWindow` 比例。
- `setup_style(root)`：clam 主题；Treeview 行高 30、斑马纹、选中 `PRIMARY_SOFT` + `PRIMARY_DEEP`；
  细窄滚动条（`width=11, arrowsize=0`）。
- 业务工具保留原样：`accuracy()`、`diff_words()`、`center_window()`。

---

## 三、`app.py` 重写：侧边导航取代 14 个挤爆的 Notebook 标签

- 左侧 208px 白色侧栏 + 白色顶栏（页标题 / 副标题 / 音色·音高·语速·试听）+ 底部状态栏。
- `NavHost` 提供 `add / select / index / tabs / enable_traversal / bind("<<NotebookTabChanged>>")`，
  对页面完全兼容原 `ttk.Notebook` 用法；`App.notebook` 仍指向它。
- 导航分四组：学习（词汇记忆 / 单词本 / 错题本）、训练（听写 / 听力 / 阅读 / 选词 / 翻译 / 作文）、
  资料（短语 / 语法）、进度（模考 / 导入 / 统计）。
- `NavItem`：选中态 `PRIMARY_SOFT` 圆角底 + 左侧 3.5px 主色指示条 + `PRIMARY_DEEP` 粗体字。
- 契约未变：`self.store` / `self.tts` / `self.tts.speak()` / `self.set_status()` /
  `self.pages` / `self.switch_to(key)` / `self.refresh_all()`。

---

## 四、14 个页面（`pages/page_*.py` 均重写）

统一后每页都做到：`ui.segment` 做筛选、`ui.card` 圆角卡、`ui.empty_state` 空状态、
`ui.button` 主色/幽灵语义按钮、线性图标、`place` 叠层空状态（不用 `pack_forget` 切内容，避免布局塌陷）。

| 页面 | 关键改造 |
|---|---|
| 词汇记忆 | Georgia 40 大字单词居中；例句区未展开时不占位；底部 6 个语义按钮；空词库时按钮置灰 |
| 单词本 | 左右分栏 + 搜索框自绘；空状态遮罩；列表空时连同滚动条一起隐藏 |
| 错题本 | 表格 + 右侧 376px 详情卡（软色块分区）；空状态居中 |
| 听写训练 | 左 326px 听音卡（四个整宽按钮 + 环形 Meter 待判分占位）+ 右作答卡（逐词 chip 判分） |
| 听力训练 | 左 368px 音频卡（原文默认折叠）+ 右题目卡（选项行整行可点，交卷后对错染色） |
| 阅读理解 | `PanedWindow` 上下分栏（sash 初始 46%）；文章 Georgia 12 带行距 |
| 选词填空 | 左文章（空位内联 ①②③ + 判分后插入答案）+ 右 356px 逐空下拉 |
| 翻译训练 | 三段式：中文卡 / 译文输入卡 / 判分结果卡（初始不占位）；逐词 chip 染色 |
| 作文模板 | 左三块（题干 / 写作区 / 结果）+ 右 392px 模板卡（分段「插入」按钮 + 字数计时） |
| 短语搭配 | Georgia 28 大字短语居中；底部 6 个语义按钮；`place` 遮罩空状态 |
| 语法知识 | 左 272px 自绘行列表（圆角选中态 + 主色指示条 + 完成勾）；右讲解软色块（规则/错句/正解/记忆点） |
| 模拟考试 | 工具条两行（套卷 + 剩余时钟 / 开始 + 交卷）；居中空状态 |
| 题库导入 | `Segment` 选题型与等级；左粘贴区 + 右 520px 题库表格（短标签防截断）；备份弹窗重绘 |
| 学习统计 | 三个环形 Meter（高中/四级/六级掌握度）+ 数字卡网格 + 错词 chip 云 + 练习记录表 |

---

## 五、打包

- `build.bat` 三个改动：
  1. **文件必须保持 CRLF 换行** —— 被改成 LF 后 cmd 无法识别 `^` 续行符，会把参数当命令执行导致打包失败。
  2. 加入 `--runtime-tmpdir "_rt"`（相对路径，落在 exe 所在目录的 `_rt`）。
  3. 其余参数不变（`--onefile --windowed --add-data "cet_pack.json;."` + 25 个 `--hidden-import`）。
- **为什么加 `--runtime-tmpdir`**：本机用户名含单引号（`C:\Users\g'z'x\`），
  PyInstaller onefile 引导器在 TEMP 路径处理上会崩，弹 `Could not create temporary directory!`。
  实测：同一 exe 放在 `E:\deep seek111\…`、`E:\with space`、`E:\CETTrainerRun` 三种目录，
  只有前者失败；用相对 `_rt` 后三处全部正常。
  副作用：exe 旁边会生成 `_rt\_MEIxxxxxx` 解压目录，退出后不自动删（占用约 29 MB / 次运行，可手工清理）。

## 六、TTS 音色（v1.6 新增，10 个在线神经音色）

原程序只有本机 SAPI5 的两个 2010 年代拼接式音色（Zira 英文 / Huihui 中文），机械感很重。
现接入微软 Edge 神经网络语音（与 Edge 浏览器「大声朗读」同一套），音质为真人录音级。

- 新文件 `tts_edge.py`（**纯标准库**，无 pip 依赖）：
  手写 WebSocket 客户端 + 完整移植 edge-tts 7.3.1 的 `Sec-MS-GEC` 签名算法
  （CS64 + SHA256 混合摘要，81 字符）。**不要试图退回简单 SHA256(ticks+token)，会被 403。**
- 音色（`tts_edge.VOICES`，10 个）：Ava / Andrew / Emma / Brian（美音），
  Sonia / Ryan（英音），晓晓 / 云希 / 晓伊 / 云扬（中文）。
- `tts.py` 的 `synthesize()` 改为**三级降级**：
  ① Edge 在线神经音色 → ② 百度在线（`fanyi.baidu.com/gettts`，仍可用）→ ③ 本机 SAPI5。
  Edge 连续失败 3 次自动 `use_edge=False`，避免每次操作干等超时。
- 语速映射：UI 的 1~9 档 → `rate = level - 5`（-4..+4）→ Edge prosody `±10%/级`（最大 ±40%）。
  语速对在线音色同样生效（实测 语速1=32976B / 语速5=19872B / 语速9=14400B，文件递减）。
- 顶栏只保留「语速 / 音色 / 试听」三个控件（音高已移除，否则挤不下）；
  音色下拉显示形如 `Ava 美音女·在线`，`_voice_map` 负责显示文本 → 真实 id 的映射。

## 七、App 图标（v1.6）

- 图形：Lucide `graduation-cap` 白色描边，底版暖红对角渐变（与主色 `#E8455F` 同源）。
  **分尺寸绘制**（`_build_icon.py`）：≥32px 用官方描边 SVG，<32px 换成简化实心剪影，
  否则 16px 下描边只有 1px、抗锯齿后糊成「蘑菇」。
- `_ico_pack.py`：**手写 ICO 封装器**。PIL 的 `im.save(sizes=…, append_images=…)` 对 ICO
  会写出坏帧（读回全黑），必须用这个手写版（≥256 存 PNG，其余存 BMP DIB + AND 掩码）。
- `app.py` 的 `_set_app_icon()` 依次在 `_MEIPASS` / exe 目录 / 源码目录找 `icon_app.ico`/`cet.ico`，
  并额外 `iconphoto` 彩色大图给 Alt+Tab；`_load_brand_image()` 给侧栏品牌区提供同款 40px 图标。

## 八、辅助脚本（保留可复用）


- `_shots_all.py [key …]`：逐页截图 → `shots/all/p_<key>.png`（不传参数则截全部 14 页）。
  必须先 `root.attributes('-topmost', True)`，否则会抓到别的窗口。
- `_exe_shot.py`：启动 `dist\CETTrainer.exe` 并整窗截图 → `shots/exe_shot.png`。
  文件开头必须最先 `SetProcessDpiAwareness(2)`，否则高 DPI 下只截到窗口左上角。
- `_smoke.py`：14 页逐页实例化冒烟测试。

## 部署（v1.6 已上线）

- 程序位置：`E:\CETTrainer\CETTrainer.exe`（16.4 MB，含图标）
- 桌面快捷方式：`C:\Users\g'z'x\Desktop\四六级学习助手.lnk`
  指向上面这个 exe，工作目录 `E:\CETTrainer`，图标取 exe 内嵌资源。
- 老版本（v1.3/v1.4 三个 exe + 使用说明 + pack_data.zip）已备份到
  `C:\Temp\CETTrainer_old_backup\`（44.5 MB），确认无学习记录后才替换的：
  老库 `E:\CETTrainer\cet_data\progress.db` 里 `question_log`/`vocab_progress`/`wordbook`
  全为 0，只有 5 条 settings，删除无数据损失。
- 数据跟着 exe 走（`store._app_dir()` = exe 所在目录），所以 `cet_data\progress.db` 在 `E:\CETTrainer\` 下。

## 九、源码保护（重要，老大特别交代）

源码目录 `E:\deep seek111\cet_trainer_recovered\` 是唯一可维护的源，**别弄丢**。
已做三层保护：

1. **源码原地**：41 个 `.py` + `build.bat` + `CETTrainer.spec` + `cet.ico` / `icon_app*.png`
   + `HANDOFF_BEAUTIFY.md`。全部 `compileall` 通过。
2. **双位快照**：`E:\Python315\python.exe _backup.py` 生成带时间戳的 zip，同时写两处：
   - `C:\Temp\cet_src_snapshots\`
   - `E:\CETTrainer_src_backup\`（跨盘，防单盘故障）
   `_backup.py --list` 列出已有快照。**每次改完代码跑一次**。
   脚本内 `MUST_HAVE` 清单会在关键文件缺失时拒绝出包（防备份出残废版本）。
3. **已实测可完整重建**：把快照解压到空目录后依次跑
   `compileall` → `_smoke.py`（14 页 `ERRORS: []`）→ `build_pack.py`（9923 词/1800 短语/8 阅读/45 翻译/111 听写句）
   → `build.bat`（产出 16.4 MB exe）→ 启动（窗口正常）。
   即：**只要有那个 zip，整个程序能从零复活。**

注意：`cet_pack.json` 故意不进快照（2.5 MB，可由 `build_pack.py` 从 `data_*.py` 稳定重建）。
`data_*.py`（题库源码，共 11 个，最大 `data_gaokao.py` 672 KB）必须进快照，那是数据的本体。

本机**没有装 git**，所以用时间戳 zip 代替版本控制。若以后装了 git，直接
`git init` 即可，`.gitignore` 需要忽略 `__pycache__/ _rt/ build/ dist/ cet_data/ shots/ cet_pack.json cet_tts_*`。

## 十、垃圾清理（`_clean.py` / `_clean.bat`）

PyInstaller onefile 每次启动把自身解压到 `%TEMP%\_MEIxxxxxx`，退出正常会删，
但被强杀/崩溃时留下约 **27 MB/次**。打包调试期间实测积累过 **626 MB**。

用法（双击 `_clean.bat` 也行，有菜单）：

```bat
python _clean.py              :: 直接清
python _clean.py --dry        :: 只看会删什么
python _clean.py --all        :: 连源码 build/ __pycache__ 一起清
python _clean.py --keep-hours 6   :: 只清 6 小时前的
```

**安全设计（重要）**：
- 用 `CreateToolhelp32Snapshot` 枚举 `CETTrainer.exe` 进程，再用 `Module32First`
  读出它**实际加载的 `_MEI` 目录**，这些一律跳过 —— 实测程序开着时清理，
  程序本体不受任何影响（2 个进程照常运行）。
- 只按名字白名单匹配（`_MEI*` / `cet_tts_*`），不做通配乱扫。
- 删不掉的跳过并报告，不报错退出；目标已不存在算成功（两个清理器可能同时跑）。
- 扫描范围：`TEMP`/`TMP`/`LOCALAPPDATA\Temp`/`Windows\Temp` **以及其下一层**
  （终端或编排环境常重定向 TEMP 到子目录，只扫根会漏）。

**另外程序启动时也会自动清一次**：`app.py` 的 `_sweep_old_mei()` 在后台线程
（daemon，绝不阻塞启动）里清掉 **6 小时以上**的旧 `_MEI`，跳过当前进程正在用的那个。
所以正常使用下这个目录不会无限膨胀，`_clean.py` 主要给「攒了一堆」时手动扫一遍。

### 一个曾经埋下的坑（已修）
`build.bat` 原先写的是 `--runtime-tmpdir "_rt"`。**相对路径是按「当前工作目录」解析的，
不是按 exe 所在目录**。从桌面双击时 CWD 是 `C:\Windows\System32`（无写权限），
程序会直接启动失败；只有从命令行在某个可写目录启动才正常。
现已**删掉该参数**，用默认系统 TEMP（配合上面的自动清理）。实测把 CWD 设成
`C:\Windows\System32` 启动正常，无 Error 弹窗。

## 不要做的（仍然有效）
- 不破坏 `store / tts / cetpack / 数据模块` 的逻辑与数据内容。
- 不引入需 pip 安装的新依赖（保持纯 ttk + Canvas）。
- 页面里不要出现裸 hex 颜色，一律走 `ui.*` 常量。
