# PNG 转 SVG 转 PPT Codex Skill

[English README](README.md)

`pngtosvgtoppt` 是一个 Codex skill，用来把扁平的 PNG/JPG 幻灯片图片重建成分层的、适合 PowerPoint 的 SVG 场景，并导出可编辑的 PPTX 文件。它采用实用的混合重建方式：复杂背景、人物、照片或重效果可以保留为图片层；重要文字、面板、形状、图表、标签和动画对象则尽量重建成可编辑的 SVG/PPT 元素。

## 能做什么

- 判断一张幻灯片截图是否适合重建。
- 规划烘焙层、可编辑层、混合层和可动画层。
- 可选调用 AI 视觉模型生成 scene JSON。
- 将 scene JSON 渲染为 PPT 安全的 SVG。
- 检查并后处理 SVG，提高 PowerPoint 兼容性。
- 导出带分组动画锚点的可编辑 PPTX。

## 安装为 Codex Skill

### macOS / Linux

把这个仓库克隆或复制到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/everhonorstar/pngtosvgtoppt.git ~/.codex/skills/pngtosvgtoppt
```

安装 Python 依赖：

```bash
cd ~/.codex/skills/pngtosvgtoppt
python3 -m pip install -r requirements.txt
```

重启 Codex，让它重新发现 `SKILL.md` 里的 skill 元数据。

### Windows PowerShell

把这个仓库克隆或复制到 Codex skills 目录：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills"
git clone https://github.com/everhonorstar/pngtosvgtoppt.git "$env:USERPROFILE\.codex\skills\pngtosvgtoppt"
```

安装 Python 依赖：

```powershell
cd "$env:USERPROFILE\.codex\skills\pngtosvgtoppt"
python -m pip install -r requirements.txt
```

如果你的系统没有注册 `python` 命令，可以改用 `py`：

```powershell
py -m pip install -r requirements.txt
```

重启 Codex，让它重新发现 `SKILL.md` 里的 skill 元数据。

## 配置 AI 视觉模型

AI 视觉是可选功能。手动生成场景脚手架、SVG 渲染、质量检查、SVG 后处理和 PPTX 导出都可以在本地完成。

如果要启用 AI 场景拆解，复制示例环境变量文件并填入你的服务商配置：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

运行 `ai-scene` 或 `auto` 前，需要同时填写 API key 和支持视觉输入的模型名称。

skill 会按以下顺序查找 `.env`：

1. 当前工作目录
2. 这个 skill 目录
3. `~/.pngtosvgtoppt/.env`

不要提交真实密钥。`.env` 已在 `.gitignore` 中忽略。

## 快速开始

下面的示例使用 `python3`。在 Windows 上，请把 `python3` 替换为 `python` 或 `py`。

不调用 AI，先为图片创建一个 scene JSON 脚手架：

```bash
python3 scripts/png_scene_scaffold.py input.png -o scene.json --canvas ppt169
```

把 scene JSON 渲染成 SVG：

```bash
python3 scripts/scene_to_svg.py scene.json -o slide_01.svg
```

对单张图片运行 AI 辅助自动转换：

```bash
python3 scripts/pngtosvgtoppt_pipeline.py auto input.png --project projects/demo --slide 1 --canvas ppt169
```

当 `svg_output/` 中已经有 SVG 后，运行确定性的检查、后处理和导出流程：

```bash
python3 scripts/pngtosvgtoppt_pipeline.py build projects/demo
```

## 项目目录结构

流水线默认使用下面这种项目目录：

```text
project/
├── images/
├── scenes/
├── svg_output/
├── svg_final/
├── exports/
└── backup/
```

生成的项目目录和 PPTX 导出文件默认会被忽略，不会进入 git 上传清单。

## Windows 注意事项

- 建议在 PowerShell、Windows Terminal，或能访问本机 Python 的 Codex 终端里运行命令。
- 脚本内部主要使用 Python 的 `pathlib`/`shutil` 等跨平台 API；Windows 上请用 `python scripts/...` 调用，不要依赖 Unix shebang 直接执行。
- `cairosvg` 在 Windows 上可能需要额外的 Cairo 运行库。如果安装不方便，native editable PPTX 导出仍然可用；主要影响的是 legacy PNG fallback 渲染。也可以安装 `svglib` 和 `reportlab` 作为备选。
- 建议使用较新的 Python 3，推荐 Python 3.10+。

## 仓库结构

- `SKILL.md`：给 Codex 读取的工作流和触发说明。
- `agents/openai.yaml`：Codex skill 列表里的 UI 元数据。
- `references/`：重建策略、scene schema、PPT 兼容性等详细参考。
- `scripts/`：本地转换、验证、SVG 后处理和 PPTX 导出脚本。
- `templates/icons/`：可选图标库目录，用于 `<use data-icon="...">` 占位符。

## 分享前注意

公开发布前，建议添加一份符合你授权意愿的 license 文件。上传前也请确认没有包含本地 `.env`、生成的 `projects/` 目录或导出的 `.pptx` 文件。
