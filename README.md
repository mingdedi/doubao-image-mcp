# 豆包图像生成 MCP 服务器

基于 MCP (Model Context Protocol) 的豆包图像生成工具，允许其他 AI 模型调用豆包图像生成 API。

## 功能特性

- 🎨 **图像生成** - 使用豆包 Seedream 模型生成高质量图像
- 📦 **组图生成** - 支持生成内容关联的系列图片
- 🔒 **安全配置** - API 密钥通过环境变量管理
- 🚀 **简单易用** - 使用 uv 管理环境，开箱即用

## 环境要求

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) 包管理器
- 豆包 API 密钥（从 [火山引擎控制台](https://console.volcengine.com/ark) 获取）

## 安装

### 1. 克隆/下载项目

```bash
cd doubao-image
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
      "cwd": "C:/projects/MCP_Server/doubao-image",
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
      "cwd": "/path/to/doubao-image",
      "env": {
        "DOUBAO_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 可用工具

### `generate_image`

生成单张图像。

**参数:**
- `prompt` (string): 图像生成提示词
- `model` (string, 可选): 模型名称，默认 `doubao-seedream-4-5-251128`
- `size` (string, 可选): 图像尺寸，默认 `2K`
- `watermark` (boolean, 可选): 是否添加水印，默认 `false`
- `negative_prompt` (string, 可选): 负面提示词
- `image` (string/array, 可选): 参考图 URL，支持单张或多张

**返回:**
```json
{
  "url": "https://...",
  "revised_prompt": "...",
  "model": "doubao-seedream-4-5-251128",
  "size": "2K"
}
```

### `generate_sequential_images`

生成一组内容关联的图片（组图）。

**额外警告，在选择4K分辨率多张生图时，由于生图需要时间相当长，要注意额外在软件中延长设置MCP工具超时时长**

**参数:**
- `prompt` (string): 图像生成提示词
- `model` (string, 可选): 模型名称，默认 `doubao-seedream-4-5-251128`
- `size` (string, 可选): 图像尺寸，默认 `2K`
- `watermark` (boolean, 可选): 是否添加水印，默认 `false`
- `negative_prompt` (string, 可选): 负面提示词
- `max_images` (integer, 可选): 最多生成数量 (1-15)，默认 `4`
- `image` (string/array, 可选): 参考图 URL，支持单张或多张。注意：参考图数量 + 生成图片数量 ≤ 15

**返回:**
```json
{
  "urls": ["https://...", "..."],
  "count": 2,
  "revised_prompt": "...",
  "model": "doubao-seedream-4-5-251128",
  "size": "2K"
}
```

## 示例提示词

```
星际穿越，黑洞，黑洞里冲出一辆快支离破碎的复古列车，抢视觉冲击力，
电影大片，末日既视感，动感，对比色，oc 渲染，光线追踪，动态模糊，
景深，超现实主义，深蓝，画面通过细腻的丰富的色彩层次塑造主体与场景，
质感真实，暗黑风背景的光影效果营造出氛围，整体兼具艺术幻想感，
夸张的广角透视效果，耀光，反射，极致的光影，强引力，吞噬
```

## 项目结构

```
doubao-image/
├── pyproject.toml        # 项目配置和依赖
├── README.md
└── server.py     # MCP 服务器主模块
```

## 获取 API 密钥

1. 访问 [火山引擎方舟控制台](https://console.volcengine.com/ark)
2. 登录/注册账号
3. 创建或选择一个应用
4. 在应用详情页面获取 API Key

## 故障排除

### 未找到 DOUBAO_API_KEY 环境变量

确保已正确设置环境变量，在终端中设置环境变量后重新启动

### API 请求失败

- 检查 API 密钥是否正确
- 确认网络连接正常
- 查看火山引擎控制台的配额限制

## 许可证

MIT License
