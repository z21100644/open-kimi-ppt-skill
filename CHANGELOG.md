# 更新日志

[简体中文](CHANGELOG.md) | [English](CHANGELOG_EN.md)

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。1.0.0 起为离线、规划优先的分支版本；上游的版本记录保留在文末「上游历史」。

## [1.0.3] - 2026-10-11

### 新增

- `pptd_kit.py` API 索引：`python pptd_kit.py [关键字]` 列出每个公开函数的签名与一行说明（另列 THEMES／LAYOUTS／SEMANTIC_ICONS），关键字比对完整说明；约 13 KB，取代通读 1,800 行的原始文件；原本缺说明的 24 个函数（`Page.text`、`shape`、`solid`、`chart`、`save`、`Kit.area`…）补上一行说明
- `pptd2pptx.py --lang auto|zh-TW|zh-CN|ja|ko`：东亚字体依简报文字自动选择（繁中 Microsoft JhengHei／PMingLiU、简中 Microsoft YaHei／SimSun、日文 Yu Gothic／Yu Mincho、韩文 Malgun Gothic／Batang），简中、日文与韩文简报不再落到繁中字体而缺字换字；只计算假名字母，中文常用的「・」「ー」不会被误判为日文——以 39 份繁中简报与 3 份上游简中范例验证判定全部正确

### 变更

- SKILL.md：构建时改用 API 索引查组件；转换一节说明依文字选择东亚字体

## [1.0.2] - 2026-10-11

### 变更

- `storyboard.py check`：标题、重点句与副标里由 `build.py` 填值的 `{占位符}` 在句中以短数字估宽，整栏只有一个占位符（由资料选出的整句）时不估宽，不再误报标题放不下；有讲者备注（`notes`）的页面不再警告缺少支持论点；同一讯息出现在 3 处以上时合并为一行（`×19 no supporting points — journey, …`），每页计数不变；`brief.mode` 不合法时依 `design-workflow.md` 的定义提示三种模式（live＝作者亲自讲、reading＝无人讲解的阅读、hybrid＝由他人上台）——以一份实际完成的 26 页简报验证：29 条输出降为 4 条真问题
- README（中英）：说明本分支未发布到 npm、`npx` 会装到上游版本，改以 `node bin/open-kimi-ppt-skill.js install` 从仓库安装、`serve` 启动本地编辑器；修正「自动嵌入字体」「编辑器随时导出 PPTX」等与离线流程不符的描述，Windows 常驻浏览器一节标明只用于 Kimi 线上导出；功能列表补上规划流程、组件库与模板、讲者备注
- `design-workflow.md`：QA 改读分页总览图；修正指向 SKILL.md 的失效编号；`storyboard.md` 说明占位符的估宽方式与合并输出

## [1.0.1] - 2026-10-11

### 新增

- `render_pptx.py`：超过 8 页时另输出每张 6 页的总览 `overview-<k>.jpg`（`--per-sheet` 可调，0 关闭），长简报不再缩到看不清；页码标签移到每张缩图上方的标签列，不再盖住投影片右下角的页码与页尾
- `Page.takeaway(..., reveal="第 1 题答案：B")`：在重点列右端放绿色勾选胶囊，测验答案等揭晓固定出现在同一位置；策划稿页面可写 `reveal:`
- 线框稿：开场页与附录页标示「开场」「附录」，不再显示第 1 章的进度

### 变更

- SKILL.md 精简改写（28.7 KB → 18.5 KB，规则不变）：依任务列出要读的参考文件，用 `pptd_kit` 构建时不必通读 88 KB 的 `pptd.md`（只在手写或转换 `.page` 时读 §1–§5）；修正过时的「浏览器端 PPTX 写入器」描述、错置的「其他格式」段落与模板说明的断句；17 项视觉检查依「基本／设计／材质／主次／图表」分组，统一为英文；交付与验证步骤合并最终的 `--embed-fonts --pdf-to`

### 修复

- `lint_pptd.py` `container`：以文字中心所在的色块判定容器，跨在两个相邻色块交界的小标签（象限线上的编号圆点）不再误报超出容器
- `lint_pptd.py` `collision`：重叠判定扣除行距，图表原点相邻的两个刻度（「0.0」与「0.4」）不再误报重叠；真正重叠的文字仍会报出
- `lint_pptd.py` `container`：超出量改以字形估算（不含行距）而非文字框边缘——比柱子或栏位宽、但数字置中的标签不再误报；以本仓库外 39 份既有简报回归比对：移除 10 个误报、新增 0 个误报、多抓到 1 个真实溢出

## [1.0.0] - 2026-10-11

首个正式版：离线、规划优先的分支版本（fork 自上游 binaryify/open-kimi-ppt-skill 1.2.0）。汇总 1.0.0-rc.1（离线 PPTX 转换与渲染 QA）、1.0.0-rc.2（规划工作流、便当网格、图标库）与之后的装饰、卡片工艺、模板、材质与美术方向，以及本次定版的讲者备注、字体内嵌与主次规则。

### 新增

- 装饰流程 `reference/decoration.md`：每个内容页一个视觉主体（图表、照片、图示组、大数字）＋ 2–6 个有明确作用的辅助图形；全篇固定 2–3 种重复图形（`brief.decor`）；区分「卡片」与「图块」（贴边色带、全宽色条、徽章、标签），在「默认不用卡片」规则下仍能美化；卡片模式的做法；各页型的装饰预算与 QA
- `pptd_kit` 不用卡片的装饰组件：`band`（贴边色带）、`watermark`（12% 透明度的大号数字／关键字）、`photo`（图片＋色条＋说明）、`motif`（角落圆点／同心弧／叶片）、`pictogram`（图示单位图，例如「10 度电有 1 度」）
- `lint_pptd.py`：`plain` 检查（整页只有文字与细线时警告）；颜色透明度低于 0.5 的文字视为装饰，不做对比检查
- 需求调研：未指定设计时，可在同一轮问题中提供版面风格选项（卡片式资讯块／开放式版面／图像主导），选卡片式即视为使用者明确要求
- `design-workflow.md` 加入装饰阶段与「太素／不够美／没有图块」的修正方式；`storyboard.md` 新增 `brief.decor` 与页面 `decor` 栏位；`SKILL.md` 视觉检查加入第 11 项
- `Page.module` 默认渲染美化：短文字自动放大到放得下的最大字级、每个区块在模块内垂直置中；`stat` 可放 3 个数字，新增 `ring`／`bar`／`pictogram` 直接依资料绘制；图表每栏都是一个系列（附文字图例）、保留小数、横条图由上到下排名；无图示的流程节点显示步骤编号；卡片模式的图片模块改为照片卡
- 便当网格：新增 `mosaic` 版式（中方块＋两个小横块＋一条直栏）；`storyboard.md` 写明模块数量弹性（1–6）与间距换算（960 画布 16pt ≈ 1280 画布 21px，符合 ≥20px）
- `Page.module` 表格依换行后的文字决定各列高度；多个短项目只在不增加换行时才放大字级，并避开行尾左括号与行首标点；图表数字标签统一小数位数（0.41 与 1.00）
- 卡片工艺（`decoration.md` §6）：比对使用者原稿与默认重建版本后归纳的四个做法——每张卡片由 2–3 种元素组成并以虚线分隔、每页至多一张渐层主卡、全篇固定的颜色语意（`brief.colors`）、细节收尾（标签、目标刻度、照片色条、封面弧线）；`design-workflow.md` 新增「没有原稿有设计感／卡片很空」的修正方式，`SKILL.md` 视觉检查加入第 12 项
- `Page.module` 新增 `stack`（一张卡片内组合 2–3 个子模块，虚线分隔，可直排或横排）、`rank`（依群组上色的排名横条＋图例）、`dumbbell`（前→后对照点线图，达标的列转绿）；`feature: true` 让该模块画在渐层主卡上（浅色字、无渐层数字）；`tone` 支援 blue／orange／green／gray，`pictogram` 也可指定
- `pptd_kit` 新组件 `chip`（色条＋名称＋数值）、`tag`（浅底名称标签）、`arc`（封面弧线）；主题新增 `feature`／`feature2`／`on_feature` 主卡颜色
- `lint_pptd.py`：`sparse` 检查（卡片内容只占卡片本体高度不到 70% 时警告）；`storyboard.py check`：大卡片只放一个小元素、同页多张主卡、主卡放图表或表格、使用 `tone` 却未写 `brief.colors` 时警告
- 可执行模板：`pptd_kit` 新增 `ink-ivory`（墨蓝象牙：象牙底、衬线标题、细线卡片、金色点缀、无渐层）与 `sage-mist`（雾绿：灰绿底、圆角无框卡片、柔和阴影），与 `bright-blue` 共用策划稿与 build 脚本，`Kit(..., theme="ink-ivory")` 一个参数整份换装；各附 `design.md`、`sample_build.py` 与 `preview.jpg`，`theme.md`／`theme_EN.md` 新增「可执行模板」一节
- 模板的外观不只配色：卡片圆角／标题带／边框／阴影、标题下的线条、页首（`bar`／`rule`）、重点列（`bar`／`rule`）、渐层或纯色、图示圆盘或单纯图形、标题字体、封面做法都由主题决定；新增 `Page.cover`（`photo-fade`／`frame`／`wash` 三种封面）、`Page.header(..., label=)`（开场／结论／附录页不显示章节进度）、`Page.title_text`
- 精致化预设（`decoration.md` §9）：每页一个主数字（`hero: true` 放到最大、其他数字自动缩小）、颜色与图标各只代表一件事（`brief.colors` 新增 `teal`，图标可用语意名称 `SEMANTIC_ICONS`：carbon、money、power…）、长简报要有喘息页或英雄横幅、装饰只放在卡片角落且避开文字、现场简报以结尾页收尾、副标与重点句精简为一句；SKILL.md 视觉检查加入第 13 项
- `pptd_kit`：模块 `kind: hero`（全宽焦点横幅）、`Page.breather`（照片＋超大数字的喘息页）、`Page.closing`（沿用封面配方的结尾页）、`Page.coins`（钱币堆叠）、主数字 `hero_stat`（单位移入标签，矮卡片改为数字与标签并排）；主卡在标题角落加小圆环（主题键 `feature_pattern`，标题放不下时不画）
- `storyboard.py`：页面 `breather:`、顶层 `closing:`；检查数字太多却没有主数字、一页两个主数字、8 页以上没有喘息页或英雄横幅、现场简报没有结尾页、副标或重点句超过一句；接受语意图标名称
- `lint_pptd.py`：`deco` 检查（半透明或空心的装饰图形压到文字，或超出卡片边缘）
- 可执行模板 `ios-glass-briefing`（`theme="ios-glass"`，玻璃）：沿用亮蓝的版面，只换成 iOS 27 风格材质——晕染桌布（Kit 自动生成 `media/wall.jpg`）、上亮下透的白玻璃卡片与白色亮边、蓝色有色玻璃主卡加高光、App 图标式方块图标、淡色胶囊、大标题页首＋页面指示器、玻璃重点胶囊；封面与结尾页为玻璃相框照片（同心圆角，`Kit.rounded` 预先裁成圆角 PNG）、浮动小卡、分组清单式重点回顾
- `decoration.md` §10 材质：使用者偏好旧版时保留版面只换材质、玻璃要稳不要透、同心圆角、每个区块同一材质、迭代前先自我检视（每个装饰都承载资料）；`design-workflow.md` 回馈对照表新增「沒有 vN 好／質感不對」与「自我迭代」；SKILL.md 视觉检查加入第 14 项
- `lint_pptd.py` `sparse`：卡片第一行的小字被当成标题时，从标题区往下延伸的主数字不再被排除（误报修正）
- `pptd_kit`：新主题键 `material`、`pill`、`wallpaper`、`wallpaper_cover`，`icon_style: tile`、`header: large`、`takeaway: capsule`、`cover: glass`、`feature_pattern: highlight`、`card_rule: none`；函数 `wallpaper`（模糊时以同色透明打底，避免发灰）、`tint`、`deepen`；`Page.cover(widget=…)`，`meta` 可为 `(图标, 文字)`
- 可执行模板 `clear-briefing`（`theme="clear"`，清透）：一套写成规则的美术风格——淡晕染底上的白玻璃卡片、只用圆角矩形（圆形只给数据）、圆角以像素计（`radius_px`）、淡色主卡配深色字（`feature_style: tint`）、全份唯一的实心结论横幅、编号改为渐层方块（`marker: tile`，自动保证白字对比）、单一实线分隔线（`divider: solid`）、同色系明暗过渡、安全边距页首（`header_top`、`title_px`、`dot_off`）、页尾可标注每页来源（`Page.footer(n, source=…)`）
- `pptd_kit`：玻璃材质下呼吸页照片与照片卡改为圆角，暗化遮罩直接烘焙进图片（`Kit.rounded(corners=, shade=)`）；`faint()` 调整桌布浓度
- `decoration.md` §10.6「保留过渡」与 §11「美术方向」；`design-workflow.md` 回馈对照表新增「风格不统一／质感廉价」；SKILL.md 视觉检查加入第 15 项
- 讲者备注：`Page.notes` 写入 PPTD `notes`，`pptd2pptx.py` 带入 PowerPoint 备注窗格；策划稿页面新增 `notes:`；现场简报（`brief.mode: live`／`hybrid`）默认每页附一段讲稿
- `render_pptx.py --embed-fonts`（PowerPoint：以内嵌 TrueType 字体存回 PPTX）与 `--pdf-to`（输出交付用 PDF）；JSON 摘要新增 `fonts_embedded`
- `storyboard.py`：`intro:` 开场页（暖身题、路线图）；`Storyboard.page_numbers()` 依页序产生页码，供「答案在 P5」「见附录 P26」等交叉引用；`check` 新增附录过大（超过 max(3 页, 15%)）与文案写死页码的警告
- `pptd_kit.free_spot()`／`hit()`：散布图与象限图的点标签自动避让（置中上方 → 微移 → 右 → 左 → 下），不压到点、说明文字或其他标签
- `decoration.md` §12 主次：附录约 3 页（名词、资料表、方法与来源同页）、侧卡只讲一个重点、讲同一件事的页面合并、发现汇总页与「发现 N」标记、揭晓位置固定、全份同一套名词、一句话写主结论、页码由页序产生；§12.1 散布／象限图可读性（刻度、平均线标值、象限名称在角落、重叠的点合并并注明家数、参考线在标签处断开、超出范围的点加注）；§12.2 重新审查清单
- `design-workflow.md` 回馈对照表新增「附录太多／搞清主次」「重新审查／整体呈现再迭代」「图看不懂／标签挤成一团」「需要讲稿」；SKILL.md 视觉检查加入第 16、17 项

### 变更

- 设计系统只保留一套目录 `reference/design_system/<分类>/<主题 ID>/design.md`：编号目录中与主目录同名的 16 份早期原稿删除（以精简过的 `design.md` 为准），其余 14 份移入对应分类；`theme.md`／`theme_EN.md` 的链接同步更新
- 精简：`SKILL.md` 的工作流程、组件清单与 lint 检查清单改为指向 `design-workflow.md`、`storyboard.md` 与脚本说明；`design-workflow.md` 的卡片与装饰规则改为指向 `decoration.md`；亮蓝设计系统的网格改用 `storyboard.md` 的命名版式，卡片内容区与 `module_body` 一致
- 版本号改为 1.0.0（首个正式版）；原 1.3.0-local、1.4.0-local 改记为 1.0.0-rc.1、1.0.0-rc.2；上游版本记录移到文末「上游历史」
- SKILL.md：标注版本；字体内嵌说明与实作一致（`pptd2pptx.py` 不内嵌，最终 `render_pptx.py --embed-fonts` 步骤内嵌）；交付步骤加入 `--embed-fonts --pdf-to`；讲者备注改为「使用者要求或现场简报时加入」

### 修复

- `pptd2pptx.py`：未写 `axis.type` 时依资料推断长条图方向（PPTD §5），修正 `horizontal: true` 的图表产生 PowerPoint 无法开启的档案
- `render_pptx.py`：繁中／简中 Windows 上 PowerPoint 错误讯息因编码解码失败而变成空白；开档失败时也会关闭 PowerPoint
- `lint_pptd.py`、`storyboard.py`、`pptd2pptx.py`、`icons.py`、`render_pptx.py` 一律以 UTF-8 输出，不必再设 `PYTHONUTF8=1`
- `Page.module` 同一列的多个数字改用相同字级；高卡片中的进度条会分散到约 85% 的高度，不再挤在中间
- `Page.module`：自动放大字级时不再把数字或英文单字拆到两行（PowerPoint 会整个移到下一行，估算会失准）；单段文字与引言的换行估算改用实际文字框宽度；矮的环形图区块改为圆环与标签并排，不再压到上方小标题
- `storyboard.py check` 接受预设形状名称（`lightningBolt`、`cube`…）作为图示，与 `pptd_kit` 一致
- `lint_pptd.py` `container`：渐层淡出到全透明、无边框的高光或遮罩不再被当成容器（玻璃卡片上的文字不再误报超出容器）

## [1.0.0-rc.2] - 2026-10-05

原记为 1.4.0-local。

### 新增

- 规划优先的工作流：需求调研（先检索、再一次性提出 ≤3 个附选项与默认值的问题）→ 事实表 `plan/facts.md` → 金字塔原理大纲 → 策划稿 `plan/storyboard.yaml` → 灰阶线框稿 → 套用设计 → QA
- `scripts/storyboard.py`：`check` 检查大纲（总论点、各部分论点、结论式标题、重点句、分组数量、事实引用）与版面（便当网格版式、区块重叠、主区块最大、草稿文字在最小字号下是否放得下）；`wireframe` 依策划稿生成灰阶 PPTD 线框稿，可直接走 `pptd2pptx.py` / `render_pptx.py`
- `scripts/pptd_kit.py`：12 栏 × 6 列便当网格（`grid_area`、`Kit.area`、`Kit.layout`）与具名版式（`single`、`split`、`split-2-1`、`three`、`center-main`、`hero-top`、`quad`、`main-stack`、`mixed`）
- `reference/storyboard.md`：策划稿 schema、金字塔大纲规则、便当网格版式表与命令
- `tests/test_storyboard.py` 与 `tests/fixtures/storyboard/`
- 证据表（参考 [CyberPPT](https://github.com/crazyykhllc-bit/CyberPPT)，MIT）：`facts.md` 增加类型、精确来源位置、置信度、caveat／冲突、含义栏；缺值标签（未提供／无法推导／需要外部验证）、冲突并列保留、衍生指标须列出输入
- 故事线比较：大纲前先拟 2–3 条备选（分析／决策／提案类默认 SCR），标记唯一 `chosen`；页面可加 `role`、`caveat`、`bridge`
- `storyboard.py check`：备选故事线数量与选定检查、低置信度事实缺 caveat、缺值事实提示
- `lint_pptd.py`：`container`（文字超出所在卡片／面板）、`collision`（文字互相重叠）、`icon`（离线转换会丢弃的 Font Awesome 图标）、`--scale`（字级须属于全篇字级表）与使用中字级汇总
- 图标库：`assets/icons/tabler-filled/`（[Tabler Icons](https://github.com/tabler/tabler-icons) 填色版，MIT，1,053 个）；`scripts/icons.py` 关键词搜索，并把图标库或任意自订／修改过的 SVG 转成可编辑的 PPTD 自订形状（支持 path／circle／ellipse／rect／polygon、`<g transform>`、多色与透明度）；`pptd_kit` 新增 `Page.svg`，`Page.icon` 可直接用图标库 id；`reference/icons.md` 说明使用时机、自由调整与限制
- 策划稿模块可加 `icon`，检查器验证图标存在，线框稿会画出图标
- `scripts/svgpath.py`：SVG 路径正规化（相对指令、H/V、S/T、A 弧线转三次贝塞尔、transform）

### 变更

- SKILL.md 与 `reference/design-workflow.md`：新增需求调研轮与策划稿阶段；新项目交付含 `plan/`；版面区块是否画成卡片由设计系统决定，场景文档"默认不用卡片"的规定不变
- 实测迭代（以完整简报跑通全流程后修正）：
  - 版式改以非对称为主（新增 `split-7-5`、`split-5-7`、`stack-main`、`three-uneven`、`hero-split`）；平均分割（`split`、`three`、`quad`、`hero-top`）须写 `layout_reason`，与各场景文档“禁止平均分割”一致
  - `storyboard.py check` 新增：连续两页骨架相同、主模块填充率过低、草稿文字孤字与行首标点、`data` 内图标检查；`brief.frame`（`region` 默认／`card`）使检查、线框稿与正式构建使用同一正文区域
  - `pptd_kit`：`Page.module`／`Page.modules` 依策划稿直接渲染模块（text、quote、list、stat、table、chart、diagram、image），`Page.region` 无容器模块，`takeaway(style="rule")`；主题新增 `on_accent`，编号圆点、分段与胶囊标签自动选可读颜色；`table` 自动把 px 换算为比例
  - 线框稿改用与正式构建相同的渲染器与模块框架
  - `lint_pptd.py` 新增 `table`（宽高须为比例）、`cell`（单元格溢出）、`chart`（非 PPTD 的 series 字段与 encode 列）、`contrast`（文字与背后填色对比度，WCAG 大字 3:1）
  - `icons.py search` 多个关键词改为任一命中即列出并按命中数排序
  - `pptd2pptx.py`：图表 series 的 `fill` 改为选填（原本缺少即崩溃）；图表文字默认 18；中和 `p:style` 的 effectRef，LibreOffice 渲染不再出现 PowerPoint 不会显示的阴影
  - `bright-blue-bento-briefing` 示例：修正低对比度标签颜色
- `reference/design-workflow.md`：交付语言判定顺序（用户指定 > 源材料 > 对话）、封面与章节页低密度、QA 修复顺序与严重度
- SKILL.md：复刻时图标改用预设／自定义形状（Font Awesome `icon` 元素在离线 PPTX 中会消失）
- `pptd2pptx.py`：自订形状支持完整 PPTD 路径语法（之前小写相对指令会被当成绝对坐标、A／S／T 会报错）；小 viewBox 自动放大以保留精度；形状支持 `flip`
- 交付前审查修正：
  - `icons.py`：SVG 填色解析修正（`white` 等具名颜色原本被画成黑色、`rgb()` 变黑、`#f00` 三位色未展开）；无法解析的填色给出警告；项目 SVG 路径写错时报“文件不存在”，不再误报为图标库找不到
  - `storyboard.py check`：图表、表格、流程图、图片模块缺少 `data` 时警告（原本只会渲染出说明文字）；`brief.frame` 值检查；启用章节分隔页时不再误报相邻骨架重复；线框稿能解析流程图步骤里的项目 SVG
  - `pptd_kit`：`table` 一律把宽高正规化为总和 1 的比例；流程图节点随模块高度缩放，矮区块不再与下方文字重叠
  - 示例策划稿补上真实的图表与流程图 `data`；`package.json` 把 `tests/fixtures/storyboard/` 打进 npm 包（文档把它当完整示例引用）
- `SKILL.md` 换行由 CRLF 改回 LF（全仓库唯一的 CRLF 文件，导致安装测试的 frontmatter 匹配失败，简单正则解析的加载器也可能读不到）；新增 `.gitattributes`（`* text=auto eol=lf`）与 `.editorconfig`（`end_of_line = lf`）防止再次发生
- `package.json`：`files` 补上离线脚本（`lint_pptd.py`、`pptd2pptx.py`、`pptd_kit.py`、`render_pptx.py`、`storyboard.py`、`icons.py`、`svgpath.py`）与 `assets/`，避免 npm 包缺少默认流程所需脚本

## [1.0.0-rc.1] - 2026-10-03

原记为 1.3.0-local。

### 新增

- `scripts/pptd2pptx.py`：离线 PPTD → PPTX 转换（python-pptx），取代已失效的 Kimi 线上导出（`no available pptx export plan`）；支持文字/富文本、全部预设形状与自定义路径、渐变/透明度、阴影、线条、图片（本地/网络、cover/contain/裁切）、柱状/圆饼/环形图、表格、页面背景、备注、淡入淡出切换
- `scripts/render_pptx.py`：以 PowerPoint COM（Windows）或 LibreOffice 渲染逐页 PNG、总览图与 PDF，用于视觉 QA
- `scripts/lint_pptd.py`：静态版面检查（越界、最小字号、文字溢出估算、孤字/行首标点、图表类别过密、缺失素材）
- `scripts/pptd_kit.py`：Python 组件库（章节进度页首、卡片、数据提炼 stat、圆环、进度条、分段条、胶囊标签、重点列、图表、表格、manifest 输出）
- 设计系统 `academic/bright-blue-bento-briefing`（亮蓝资讯卡简报）：design.md、sample_build.py、preview.jpg
- `reference/design-workflow.md`：简报设计工作流（需求简报 → 内容 → 提炼 → 版面 → 生成 → QA 循环）与常见修改意见对照表
- `tests/test_offline_pipeline.py`

### 变更

- SKILL.md：默认导出改为离线转换；Node.js 仅为可选（浏览器编辑器 / Kimi 图片导出）；验证步骤改为 lint → 转换 → 渲染；新增专业但易懂的用语规范

## 上游历史（binaryify/open-kimi-ppt-skill）

分支之前的上游版本；以下版本号属于上游 npm 包 `open-kimi-ppt-skill`。

### [上游 1.2.0] - 2026-08-06

#### 新增

- CLI 支持 `-h` / `--help` 与 `-V` / `--version`

#### 变更

- npm 包名与 CLI 由 `open-kimi-ppt-skills` 统一为 `open-kimi-ppt-skill`（与 GitHub 仓库名一致）。请改用 `npx open-kimi-ppt-skill@latest`；旧包名将不再更新

### [上游 1.1.3] - 2026-08-06

#### 新增

- `install` 在交互终端下列出 `.agents` / `.codex` / `.claude` / `.cursor` / `.workbuddy` 技能目录，支持空格多选
- 支持 `-y/--yes`（非交互默认目录）、可重复的 `--target`
- `--all` 仅装到已检测到的 Agent 目录；对应目录不存在的 Agent 会跳过并提示，不会新建目录
- Windows 导出自动启动一个常驻调试浏览器（Chrome，未安装时回退 Edge），规避 agent-browser 无法自行拉起 Chrome 导致的导出失败；实例导出后常驻、后续导出复用同一个，也可用 `AGENT_BROWSER_CDP` 指定自己启动的调试浏览器

#### 修复

- 修复 `find_download` 在 Downloads 目录扫描时因 `.crdownload` 被 Chrome 重命名而触发 `FileNotFoundError` 导致导出中断（Related to #4）

#### 变更

- README 默认指引 AI 通过 `npx open-kimi-ppt-skill@latest install -y` 安装，不再建议 clone 仓库

### [上游 1.1.2] - 2026-08-06

#### 修复

- 修复中文 Windows 下 `export_pptx.py` / `export_images.py` 导出卡住或 GBK 解码失败（stdout 改走临时文件 + UTF-8）
- 规避 agent-browser `--download-path` 导致 Chrome 静默取消下载：改为点击下载并轮询默认 Downloads
- 修复 npm 包误打入 `__pycache__/*.pyc`（`files` 仅列出脚本源文件）

### [上游 1.1.1] - 2026-08-06

#### 新增

- PPTD 对齐官方元素级 `animations` 规范；Skill 补充动画 / `notes` 使用边界
- 对齐配图优先级、文风禁令、澄清提问、复刻细则、并行写页等官方策略
- 内置约 30 套 preset design system，并支持点名使用
- 恢复 `customFonts`（Google Fonts）与海报推荐尺寸
- 根目录主题目录：`theme.md` / `theme_EN.md`（含预览图）
- 示例项目 `example/xiaomi-yu7-ppt-animation`（页内元素入场动画）

#### 变更

- 场景文档同步官方动画细则与 `customFonts` 引用
- README 补充元素动画、预设主题说明与示例 Prompt

### [上游 1.0.2] - 2026-08-06

#### 变更

- `install` 默认直接覆盖已安装的 Skill，无需再加 `--force`（旧的 `--force` 仍可兼容传入）

### [上游 1.0.1] - 2026-08-06

#### 新增

- Skill 工作流增加 **step0 本地前置检测**：生成前检查 Node.js 18+、npm/npx、python3，并提示需要 Chromium 系浏览器
- 导出脚本在启动时检测 **Node.js 18+** 与 **npm**；缺失或版本过低时给出明确安装指引
- CLI（`open-kimi-ppt-skill`）启动时校验 Node.js 主版本 ≥ 18
- 缺失 **PyYAML** 时自动 `pip install --user pyyaml`（与 Pillow / websocket-client 行为一致）

#### 文档

- 补充多 Agent / 多模型实测截图（ChatGPT·Codex + 5.6 Luna、Reasonix + DeepSeek、WorkBuddy 等）
- 安装说明改为「自动 / 手动二选一」，并补充 Windows 路径说明
- README 结构与示例图更新

### [上游 1.0.0] - 2026-08-05

#### 新增

- 首次发布 `open-kimi-ppt-skill`
- PPTD 生成 / 编辑 / 复刻，默认同时交付可编辑 PPTD 项目与 PPTX 成品
- 浏览器侧导出 PPTX（嵌字体、淡入淡出切换），导出前可选多模态视觉质检
- 本地在线 PPTD 编辑器（`npx open-kimi-ppt-skill serve`）
- CLI 安装 Skill 到 `~/.agents/skills`（可用 `--target` 指定其他 Agent 目录）
