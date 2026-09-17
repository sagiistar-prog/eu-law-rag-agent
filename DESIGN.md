---
name: EU Law RAG Agent
description: 以检索结果和来源原文并列组织可追溯证据
colors:
  ink: "#232c47"
  muted: "#59647c"
  blue: "#405bc4"
  line: "#d9dfea"
  background: "#f7f8fc"
  surface: "#ffffff"
  secondary: "#e9edf9"
  primary-hover: "#334aab"
typography:
  display:
    fontFamily: 'EvidenceDisplay, "Microsoft YaHei", sans-serif'
    fontSize: "clamp(32px,5vw,52px)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  body:
    fontFamily: '"Segoe UI", "Microsoft YaHei", sans-serif'
    fontSize: "16px"
    lineHeight: 1.65
  title:
    fontSize: "20px"
rounded:
  button: "8px"
  query: "14px"
  panel: "16px"
spacing:
  page: "28px"
  page-mobile: "20px"
  column-gap: "40px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.surface}"
    rounded: "{rounded.button}"
    padding: "12px 22px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.secondary}"
    textColor: "{colors.blue}"
    rounded: "{rounded.button}"
    padding: "12px 22px"
---

# Design System: EU Law RAG Agent

## Overview

**Creative North Star: "展开的证据夹"**

冷灰背景、淡紫光影与白色工作面将注意力留给检索问题、摘录和原文。蓝色只强调行动与来源链接。用户先看依据，再形成自己的判断。

规范从 knowledge/workbench.html 的实际样式与状态处理提取。界面是本地证据检索入口，示例资料为虚构；设计不能暗示检索相关性等于条款适用或法律结论。

## Colors

Blue 是主动作和来源链接色，secondary 承载核对出处与导出。Ink 与 muted 区分正文和辅助信息，line 用于页头及来源条目。背景右上有淡紫径向光，结果面保持纯白。

状态必须有文字，资料不足与请求失败使用不同表述。不要以装饰色或“成功”色暗示法律有效性。

## Typography

标题使用本地 Noto Sans SC 600 子集，以 EvidenceDisplay 名称嵌入 HTML 的 data URL；许可材料保留在 docs/fonts。它针对当前标题字形，新增标题需补充子集或接受回退，不能假定覆盖全部中文。

标题显式分为两行，按 display 尺度响应。正文按 body 尺度阅读，段落最大宽度 65ch，区域标题用 title。长来源保留原文换行并允许长词断行。

## Layout

页头与主区最大宽度 1180px，内边距 28px。查询栏独占一行，结果与来源区按 1.2:1 分栏，栏距 40px；720px 以下变为单列，外边距 20px、面板内边距 22px，查询按钮占满一行。

来源原文区域最大高 680px 后滚动。空状态直接说明输入或选择来源的下一步，不填造示例命中数。

## Elevation & Depth

结果和来源面板通过白底与留白分层，没有面板阴影。查询栏使用唯一宽柔影（0 12px 40px #3a467312），强调可启动的任务入口。

九点活动标记仅在实际请求期间显示，以 1s 透明度循环和交错延迟反馈忙碌；reduced-motion 关闭点阵动画。它不表达百分比或模型思考内容。

## Shapes

按钮、查询栏、面板按 frontmatter 的三级圆角区分。来源条目采用直线分隔与自然段落，不套多层卡片。点阵为小圆点，不用于正文分隔。

## Components

- 查询字段必填、最多 1000 字；请求期间只读，提交和导出禁用，结束后恢复编辑。请求超时或失败保留问题。
- 主按钮最小高 44px；次按钮使用浅蓝底。hover 加深主色，focus-visible 使用 2px 蓝轮廓、4px 偏移，禁用降低透明度。
- 状态区域区分正在检索、找到摘录、资料不足及失败；页面 aria-busy 与真实请求同步。
- 结果中的“核对出处”更新右侧原文并移动焦点，保留标题、采集日期与可用页码。原始链接仅接受 HTTP(S)。
- 导出使用已有结果数据；编辑问题后先禁用导出，避免将旧结果误作新查询结果。

## Do's and Don'ts

- **Do** 保留原文与元数据的阅读位置，让不确定项清晰可见。
- **Do** 复用白色面板、蓝色动作和低强度紫灰背景。
- **Don't** 使用间隔点、重复解释、假进度或虚构来源来制造可信感。
- **Don't** 将字体子集、截图或样式定义表述为全站字体覆盖、法律验证或可访问性认证。
