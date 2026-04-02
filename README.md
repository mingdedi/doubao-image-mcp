# 豆包图像生成 MCP 服务器

基于 MCP (Model Context Protocol) 的豆包图像生成工具，允许其他 AI 模型调用豆包图像生成 API。

## 功能特性

- 🎨 **图像生成** - 使用豆包 Seedream 5.0/4.5/4.0 模型生成高质量图像
- 📦 **组图生成** - 支持生成内容关联的系列图片（文生组图、图生组图）
- 🔍 **联网搜索** - Seedream 5.0 lite 支持联网搜索，融合实时信息提升生图时效性
- 🖼️ **多图融合** - 支持 2-14 张参考图融合创作
- 🎭 **多种输出格式** - 支持 PNG/JPEG 格式（5.0 lite）
- 📋 **预设模板** - 提供人物肖像、风景、产品、动漫、LOGO、海报等快速生成模板
- 🔎 **模型查询** - 可查询可用模型列表及其详细信息
- 🔒 **安全配置** - API 密钥通过环境变量管理
- 🚀 **简单易用** - 使用 uv 管理环境，开箱即用

## 环境要求

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) 包管理器
- 豆包 API 密钥（从 [火山引擎控制台](https://console.volcengine.com/ark) 获取）

## 安装

### 1. 克隆/下载项目

```bash
cd doubao-image-mcp
```

### 2. 安装依赖

```bash
uv sync
```

### 3. 配置 API 密钥

在命令行设置环境变量：

**Windows:**
```cmd
setx DOUBAO_API_KEY "your-api-key-here"
```

**Linux/macOS:**
```bash
export DOUBAO_API_KEY="your-api-key-here"
```

## 使用方法

### 作为 MCP 服务器运行

```bash
uv run server.py
```

### 在 Claude Desktop 中配置

在 Claude Desktop 的配置文件中添加：

**Windows (`%APPDATA%\Claude\claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "doubao-image": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "C:/projects/MCP_Server/doubao-image-mcp",
      "env": {
        "DOUBAO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**macOS/Linux (`~/Library/Application Support/Claude/claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "doubao-image": {
      "command": "uv",
      "args": ["run", "server.py"],
      "cwd": "/path/to/doubao-image-mcp",
      "env": {
        "DOUBAO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 可用工具

### 1. `generate_image`

生成单张图像。支持文生图、图生图、多图融合等模式。

**参数:**
- `prompt` (string): 图像生成提示词，建议不超过300个汉字或600个英文单词
- `model` (string, 可选): 模型名称，默认 `doubao-seedream-5-0-260128`
  - `doubao-seedream-5-0-260128` (推荐，最新版)
  - `doubao-seedream-4-5-251128`
  - `doubao-seedream-4-0-250828`
- `size` (string, 可选): 图像尺寸
  - 5.0-lite: `2K`, `3K`
  - 4.5: `2K`, `4K`
  - 4.0: `1K`, `2K`, `4K`
  - 也可指定具体像素如 `2048x2048`
- `output_format` (string, 可选): 输出图像格式，默认 `jpeg`，仅 5.0-lite 支持自定义
  - `png`: PNG 格式
  - `jpeg`: JPEG 格式
- `watermark` (boolean, 可选): 是否添加水印（右下角AI生成字样），默认 `false`
- `enable_web_search` (boolean, 可选): 是否开启联网搜索，默认 `false`，仅 5.0-lite 支持
- `optimize_prompt_mode` (string, 可选): 提示词优化模式，默认 `standard`
  - `standard`: 标准模式，质量更高但耗时较长
  - `fast`: 快速模式，速度更快但质量一般，仅 4.0 支持
- `image` (string/array, 可选): 参考图 URL，支持单张或多张（2-14张）

**返回:**
```json
{
  "url": "https://...",
  "size": "2048x2048",
  "model": "doubao-seedream-5-0-260128",
  "generated_images": 1,
  "web_search_count": 0
}
```

### 2. `generate_sequential_images`

生成一组内容关联的图片（组图）。支持文生组图、单图生组图、多图生组图。

**⚠️ 注意：在选择4K分辨率生成多张图片时，由于生图需要时间相当长，要注意额外在软件中延长设置MCP工具超时时长**

**参数:**
- `prompt` (string): 图像生成提示词
- `model` (string, 可选): 模型名称，默认 `doubao-seedream-5-0-260128`
- `size` (string, 可选): 图像尺寸，默认 `2K`
- `output_format` (string, 可选): 输出图像格式，默认 `jpeg`，仅 5.0-lite 支持
- `watermark` (boolean, 可选): 是否添加水印，默认 `false`
- `enable_web_search` (boolean, 可选): 是否开启联网搜索，默认 `false`，仅 5.0-lite 支持
- `max_images` (integer, 可选): 最多生成数量 (1-15)，默认 `4`
- `image` (string/array, 可选): 参考图 URL，支持单张或多张（最多14张）

**返回:**
```json
{
  "urls": ["https://...", "..."],
  "sizes": ["2048x2048", "2048x2048"],
  "count": 2,
  "model": "doubao-seedream-5-0-260128",
  "generated_images": 2,
  "output_tokens": 12345,
  "web_search_count": 0
}
```

### 3. `get_model_info`

获取可用的豆包图像生成模型列表及其详细信息，包括支持的分辨率、功能特性等。

**参数:** 无

**返回:**
```json
{
  "models": {
    "doubao-seedream-5-0-260128": {
      "name": "Seedream 5.0 lite",
      "description": "最新版本，支持文生图、图生图、多图融合、组图生成、联网搜索",
      "supported_sizes": ["2K", "3K"],
      "features": ["文生图", "图生图", "多图融合", "组图", "联网搜索", "PNG/JPEG输出"],
      "max_reference_images": 14,
      "supports_web_search": true,
      "supports_output_format": true,
      "supports_optimize_prompt": false
    }
  },
  "default_model": "doubao-seedream-5-0-260128",
  "recommended_model": "doubao-seedream-5-0-260128"
}
```

### 4. `get_preset_templates`

获取预设的图像生成模板列表，包括人物肖像、风景、产品、动漫、LOGO、海报等模板。

**参数:** 无

**返回:**
```json
{
  "templates": {
    "portrait": {
      "name": "人物肖像",
      "description": "生成高质量人物肖像",
      "prompt_template": "{subject}的专业肖像照，{style}风格，高质量摄影，精细细节，专业打光",
      "default_size": "2K"
    }
  },
  "usage": "使用 generate_image_with_preset 工具，传入 template_id、subject 和可选的 style 参数"
}
```

### 5. `generate_image_with_preset`

使用预设模板快速生成图像。提供模板名称、主体和风格即可自动生成提示词并创建图像。

**可用模板:**
- `portrait`: 人物肖像
- `landscape`: 风景照片
- `product`: 产品展示
- `anime`: 动漫风格
- `logo`: 品牌LOGO
- `poster`: 海报设计

**参数:**
- `template_id` (string): 模板ID（见上方列表）
- `subject` (string): 图像主体，例如"一只可爱的猫咪"、"现代科技感的智能手表"
- `style` (string, 可选): 图像风格，例如"复古"、"赛博朋克"、"水彩"、"极简"等，默认"现代"
- `model` (string, 可选): 模型名称
- `size` (string, 可选): 图像尺寸，不指定时使用模板默认值
- `output_format` (string, 可选): 输出图像格式
- `watermark` (boolean, 可选): 是否添加水印
- `enable_web_search` (boolean, 可选): 是否开启联网搜索
- `image` (string/array, 可选): 参考图 URL

**返回:**
```json
{
  "template_id": "portrait",
  "template_name": "人物肖像",
  "generated_prompt": "一只可爱猫咪的专业肖像照，水彩风格，高质量摄影，精细细节，专业打光",
  "url": "https://...",
  "size": "2K",
  "model": "doubao-seedream-5-0-260128",
  "generated_images": 1
}
```

## 使用场景示例

### 文生图（纯文本输入）

通过给模型提供清晰准确的文字指令，即可快速获得符合描述的高质量单张图片。

**示例提示词:**
```
充满活力的特写编辑肖像，模特眼神犀利，头戴雕塑感帽子，色彩拼接丰富，眼部焦点锐利，景深较浅，具有Vogue杂志封面的美学风格，采用中画幅拍摄，工作室灯光效果强烈。
```

### 图生图（单图输入）

基于已有图片，结合文字指令进行图像编辑，包括图像元素增删、风格转化、材质替换、色调迁移等。

**示例提示词:**
```
保持模特姿势和液态服装的流动形状不变。将服装材质从银色金属改为完全透明的清水（或玻璃）。透过液态水流，可以看到模特的皮肤细节。光影从反射变为折射。
```

### 多图融合（多图输入）

根据您输入的文本描述和多张参考图片，融合它们的风格、元素等特征来生成新图像。

**示例提示词:**
```
将图1的服装换为图2的服装
```

### 组图生成

支持通过一张或者多张图片和文字信息，生成漫画分镜、品牌视觉等一组内容关联的图片。

**示例提示词:**
```
生成一组电影级科幻写实风的4张影视分镜：
场景1为宇航员在空间站维修飞船...
场景2为突然遇到陨石带袭击...
场景3为宇航员紧急躲避...
场景4为受伤后惊险逃回飞船...
```

### 联网搜索（仅 5.0-lite）

开启联网搜索后，模型会根据用户的提示词自主判断是否搜索互联网内容（如商品、天气等），提升生成图片的时效性。

**示例提示词:**
```
制作一张上海未来5日的天气预报图，采用现代扁平化插画风格，清晰展示每日天气、温度和穿搭建议。
```

## 推荐分辨率和宽高比

### 2K 分辨率

| 宽高比 | 宽高像素值 |
|--------|-----------|
| 1:1 | 2048x2048 |
| 4:3 | 2304x1728 |
| 3:4 | 1728x2304 |
| 16:9 | 2848x1600 |
| 9:16 | 1600x2848 |
| 3:2 | 2496x1664 |
| 2:3 | 1664x2496 |
| 21:9 | 3136x1344 |

### 3K 分辨率（仅 5.0-lite）

| 宽高比 | 宽高像素值 |
|--------|-----------|
| 1:1 | 3072x3072 |
| 4:3 | 3456x2592 |
| 3:4 | 2592x3456 |
| 16:9 | 4096x2304 |
| 9:16 | 2304x4096 |
| 3:2 | 3744x2496 |
| 2:3 | 2496x3744 |
| 21:9 | 4704x2016 |

### 4K 分辨率（4.5/4.0）

| 宽高比 | 宽高像素值 |
|--------|-----------|
| 1:1 | 4096x4096 |
| 4:3 | 4704x3520 |
| 3:4 | 3520x4704 |
| 16:9 | 5504x3040 |
| 9:16 | 3040x5504 |
| 3:2 | 4992x3328 |
| 2:3 | 3328x4992 |
| 21:9 | 6240x2656 |

## 提示词建议

- 建议用**简洁连贯**的自然语言写明 **主体 + 行为 + 环境**
- 若对画面美学有要求，可用自然语言或短语补充 **风格**、**色彩**、**光影**、**构图** 等美学元素
- 文本提示词（prompt）建议不超过300个汉字或600个英文单词。字数过多信息容易分散，模型可能因此忽略细节

## 项目结构

```
doubao-image-mcp/
├── pyproject.toml        # 项目配置和依赖
├── README.md             # 项目说明文档
└── server.py             # MCP 服务器主模块
```

## 获取 API 密钥

1. 访问 [火山引擎方舟控制台](https://console.volcengine.com/ark)
2. 登录/注册账号
3. 创建或选择一个应用
4. 在应用详情页面获取 API Key

## 使用限制

### 图片传入限制

- 图片格式：jpeg、png、webp、bmp、tiff、gif
- 图片传入方式：
  - 图片 URL：请确保图片 URL 可被访问
  - Base64 编码：请遵循格式 `data:image/<图片格式>;base64,<Base64编码>`，注意 `<图片格式>` 必须采用小写字母
- 宽高比（宽/高）范围：[1/16, 16]
- 宽高长度（px）> 14
- 大小：不超过 10 MB
- 总像素：不超过 `6000x6000=36000000` px
- 最多支持传入 14 张参考图

### 保存时间

任务数据（如任务状态、图片URL等）仅保留24小时，超时后会被自动清除。请您务必及时保存生成的图片。

### 限流说明

- RPM 限流：账号下同模型（区分模型版本）每分钟生成图片数量上限
- 不同模型的限制值不同，详见 [图片生成能力](https://www.volcengine.com/docs/82379/1330310)

## 故障排除

### 未找到 DOUBAO_API_KEY 环境变量

确保已正确设置环境变量，在终端中设置环境变量后重新启动

### API 请求失败

- 检查 API 密钥是否正确
- 确认网络连接正常
- 查看火山引擎控制台的配额限制
- 检查参考图 URL 是否可访问

### 组图生成超时

- 组图生成需要较长时间，特别是 4K 分辨率
- 可以在 MCP 客户端配置中增加超时时间
- 建议开启流式输出模式（当前版本暂不支持）

## 许可证

MIT License

## 参考文档

- [豆包图像生成 API 文档](https://www.volcengine.com/docs/82379/1541523)
- [Seedream 5.0 lite 提示词指南](https://www.volcengine.com/docs/82379/1829186)
- [火山引擎方舟控制台](https://console.volcengine.com/ark)
