# CLAUDE.md

本文件为 Claude Code（claude.ai/code）在此仓库中工作时提供指导。

## 项目概述

BUAAthesis 是北京航空航天大学（北航）毕业设计的 LaTeX 模板，由北航开源俱乐部（BHOSC）维护。支持本科、硕士、博士学位论文，以及开题报告/文献综述。

## 构建命令

**首次完整编译**（xelatex → bibtex → xelatex → xelatex）：
```bash
# Windows (CMD/PowerShell)
msmake bachelor        # 或: master, kaitireport

# Unix/Mac
make bachelor          # 或: master, kaitireport
```

**快速增量编译**（仅 xelatex，跳过 bibtex；首次完整编译后使用）：
```bash
msmake bachelor fast   # Windows
```

**清理：**
```bash
msmake clean           # 删除中间文件，保留 PDF
msmake clean empty     # 删除中间文件和 PDF

make clean             # 删除中间文件
make depclean          # 删除中间文件和 PDF
```

**编辑器编译：** 按 `xelatex → bibtex → xelatex × 2` 顺序编译。模板依赖 `ctex` v2.0 及以上版本，推荐使用 TeXLive 2019 发行版。

## 架构

### 核心模板引擎

`buaathesis.cls` 是 LaTeX 文档类，基于 `ctexbook` 构建。负责以下内容：
- **学位相关布局**：文档类选项 `bachelor`、`master`、`doctor`、`professional`、`ktreport` 决定页面几何、页眉、封面和章节样式
- **字体设置**：英文主字体为 Times New Roman；中文字体为 SimSun（宋体）、SimHei（黑体）、STXingkai（华文行楷）、STKaiti（华文楷体）。非 Windows 环境需手动安装这些字体
- **页面几何**：本科使用 `bachelorgeometry`（上下左右边距 30/25/30/20mm）；硕士/博士使用 `mastergeometry`（上下左右边距 25/25/30/20mm）
- **页眉页脚样式**：`frontmatter`（罗马数字页码，无页眉线）与 `mainmatter`（页眉带学校标识）

### 入口文件

三个主要的 `.tex` 文件作为构建目标：
- `sample-bachelor.tex` — 本科毕设（使用 `openany,oneside`）
- `sample-master.tex` — 研究生毕设（使用 `openright,twoside`）
- `sample-kaitireport.tex` — 开题报告/文献综述

每个入口文件按顺序引入用户信息文件及正文各章节。

### 数据文件结构

- `data/com_info.tex` — 公共信息（学院、专业、作者、导师、论文标题、关键词、日期、中图分类号）
- `data/bachelor/bachelor_info.tex` — 本科特有信息（班级、学号、单位代码、论文日期）
- `data/master/master_info.tex` — 硕士特有信息
- `data/abstract.tex` — 中英文摘要
- `data/chapter*.tex` — 正文各章节
- `data/conclusion.tex` — 结论
- `data/bachelor/acknowledgement.tex` / `data/master/back2-acknowledgement.tex` — 致谢
- `data/reference.tex` — 参考文献设置（从 `data/bibs.bib` 加载）
- `data/appendix*.tex` — 附录
- `data/bachelor/assign.tex` — 任务书（本科特有）

### 参考文献

使用 `gbt7714` 宏包，遵循 GB/T 7714-2005 国家标准。在入口 `.tex` 文件中设置引用格式：
- `\citestyle{numerical}` — 按出现顺序排列（默认）
- `\citestyle{authoryear}` — 按作者姓名和年份排列

参考文献数据库：`data/bibs.bib`。样式文件：`gbt7714-author-year.bst`、`gbt7714-numerical.bst`、`gbt7714.sty`。

### CI/CD

GitHub Actions（`.github/workflows/build.yml`）在每次 push/PR 时，使用 `xu-cheng/latex-action@v3` 配合 xelatex 编译全部三份样例 PDF。中文字体在构建时从 dolbydu/font 下载。提交信息中包含 `ci skip` 可跳过 CI。

## 字体依赖（非 Windows 环境）

非 Windows 系统需安装以下字体：
- Times New Roman（Debian/Ubuntu 下可通过 `ttf-mscorefonts-installer` 安装）
- SimSun、SimHei、STXingkai、STKaiti（可从 Windows 系统字体库获取，或从 [dolbydu/font](https://github.com/dolbydu/font) 下载）
