"""豆包图像生成 MCP 服务器主模块"""

import os
from typing import Optional, List, Union, Literal
import httpx
from pydantic import Field
from mcp.server.fastmcp import FastMCP

# 初始化 MCP 服务器
mcp = FastMCP("doubao-image", dependencies=["httpx", "pydantic", "python-dotenv"])

# API 配置
API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
# 默认使用最新的 doubao-seedream-5.0-lite 模型
DEFAULT_MODEL = "doubao-seedream-5-0-260128"
DEFAULT_SIZE = "2K"
DEFAULT_TIMEOUT = 1800.0

# 模型支持的分辨率
MODEL_SIZES = {
    "doubao-seedream-5-0-lite": ["2K", "3K"],
    "doubao-seedream-5-0-260128": ["2K", "3K"],
    "doubao-seedream-4-5-251128": ["2K", "4K"],
    "doubao-seedream-4-0-250828": ["1K", "2K", "4K"],
}

# 模型详细信息
MODEL_INFO = {
    "doubao-seedream-5-0-260128": {
        "name": "Seedream 5.0 lite",
        "description": "最新版本，支持文生图、图生图、多图融合、组图生成、联网搜索",
        "sizes": ["2K", "3K"],
        "features": ["文生图", "图生图", "多图融合", "组图", "联网搜索", "PNG/JPEG输出"],
        "max_images": 14,
        "supports_web_search": True,
        "supports_output_format": True,
        "supports_optimize_prompt": False,
    },
    "doubao-seedream-4-5-251128": {
        "name": "Seedream 4.5",
        "description": "支持文生图、图生图、多图融合、组图生成",
        "sizes": ["2K", "4K"],
        "features": ["文生图", "图生图", "多图融合", "组图"],
        "max_images": 14,
        "supports_web_search": False,
        "supports_output_format": False,
        "supports_optimize_prompt": False,
    },
    "doubao-seedream-4-0-250828": {
        "name": "Seedream 4.0",
        "description": "支持文生图、图生图、多图融合、组图生成、提示词极速模式",
        "sizes": ["1K", "2K", "4K"],
        "features": ["文生图", "图生图", "多图融合", "组图", "提示词极速模式"],
        "max_images": 14,
        "supports_web_search": False,
        "supports_output_format": False,
        "supports_optimize_prompt": True,
    },
}

# 预设模板
PRESET_TEMPLATES = {
    "portrait": {
        "name": "人物肖像",
        "prompt_template": "{subject}的专业肖像照，{style}风格，高质量摄影，精细细节，专业打光",
        "size": "2K",
        "description": "生成高质量人物肖像",
    },
    "landscape": {
        "name": "风景照片",
        "prompt_template": "{subject}，{style}风格，广角镜头，自然光线，风景摄影",
        "size": "2K",
        "description": "生成风景照片",
    },
    "product": {
        "name": "产品展示",
        "prompt_template": "{subject}的产品展示图，{style}风格，商业摄影，白色背景，专业打光",
        "size": "2K",
        "description": "生成产品宣传图",
    },
    "anime": {
        "name": "动漫风格",
        "prompt_template": "{subject}，{style}动漫风格，二次元插画，精美细节",
        "size": "2K",
        "description": "生成动漫风格插画",
    },
    "logo": {
        "name": "品牌LOGO",
        "prompt_template": "{subject}的品牌LOGO设计，{style}风格，简洁现代，矢量图形",
        "size": "2K",
        "description": "生成品牌LOGO设计",
    },
    "poster": {
        "name": "海报设计",
        "prompt_template": "{subject}的海报设计，{style}风格，视觉冲击力强，精美排版",
        "size": "2K",
        "description": "生成海报设计",
    },
}


def _get_api_key() -> str:
    """从环境变量获取 API 密钥"""
    api_key = os.getenv("DOUBAO_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DOUBAO_API_KEY 环境变量，请设置后再使用。\n"
            "可以通过以下方式设置：\n"
            "  - Windows: setx DOUBAO_API_KEY \"your-api-key\"\n"
            "  - Linux/macOS: export DOUBAO_API_KEY=\"your-api-key\"\n"
        )
    return api_key


async def _call_api(request_data: dict) -> dict:
    """调用豆包图像生成 API"""
    api_key = _get_api_key()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(API_URL, headers=headers, json=request_data)

            if response.status_code != 200:
                error_msg = f"API 请求失败：{response.status_code}"
                try:
                    error_data = response.json()
                    # 只返回错误信息，不暴露完整响应
                    if "error" in error_data:
                        error_msg += f", 错误：{error_data['error'].get('message', '未知错误')}"
                    else:
                        error_msg += f", 错误：{error_data}"
                except Exception:
                    error_msg += f", 状态码：{response.status_code}"
                raise RuntimeError(error_msg)

            result = response.json()

        # 检查是否有全局错误
        if "error" in result and result["error"]:
            error_info = result["error"]
            raise RuntimeError(f"API 返回错误：{error_info.get('message', '未知错误')} (code: {error_info.get('code', 'N/A')})")

        if "data" not in result or not result["data"]:
            raise RuntimeError("未返回任何图像数据")

        return result
    except httpx.TimeoutException:
        raise RuntimeError(f"API 请求超时（{DEFAULT_TIMEOUT}秒）")
    except httpx.RequestError as e:
        raise RuntimeError(f"网络请求失败：{str(e)}")


@mcp.tool(
    name="generate_image",
    description="使用豆包图像生成模型创建单张图像。支持文生图、图生图、多图融合等模式。",
)
async def generate_image(
    prompt: str = Field(..., description="图像生成提示词，详细描述想要生成的图像内容。建议不超过300个汉字或600个英文单词"),
    model: str = Field(
        default=DEFAULT_MODEL,
        description="模型名称。可选值：doubao-seedream-5-0-260128(推荐), doubao-seedream-4-5-251128, doubao-seedream-4-0-250828",
    ),
    size: str = Field(
        default=DEFAULT_SIZE,
        description="图像尺寸。5.0-lite 支持 2K/3K；4.5 支持 2K/4K；4.0 支持 1K/2K/4K。也可指定具体像素如 2048x2048。需在 prompt 中描述图片宽高比/形状/用途",
    ),
    output_format: Literal["png", "jpeg"] = Field(
        default="jpeg",
        description="输出图像格式。仅 5.0-lite 支持自定义，默认 jpeg。可选：png, jpeg",
    ),
    watermark: bool = Field(
        default=False,
        description="是否在生成的图像上添加水印（右下角AI生成字样）",
    ),
    enable_web_search: bool = Field(
        default=False,
        description="是否开启联网搜索功能。开启后模型会根据提示词自主判断是否需要搜索互联网内容，提升生成图片的时效性。仅 5.0-lite 支持",
    ),
    optimize_prompt_mode: Literal["standard", "fast"] = Field(
        default="standard",
        description="提示词优化模式。standard 质量更高但耗时较长，fast 速度更快但质量一般。仅 4.0 支持 fast 模式",
    ),
    image: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="参考图 URL，支持单张或多张（2-14张）。可传 URL 或 Base64 编码（格式：data:image/<格式>;base64,<编码>）。用于图生图、图像编辑、多图融合等场景",
    ),
) -> dict:
    """
    使用豆包图像生成模型创建单张图像。

    支持以下场景：
    - 文生图：仅提供文本提示词
    - 图生图：提供单张参考图 + 文本提示词
    - 多图融合：提供多张参考图（2-14张）+ 文本提示词

    Args:
        prompt: 图像生成提示词
        model: 模型名称
        size: 图像尺寸
        output_format: 输出图像格式（仅 5.0-lite 支持）
        watermark: 是否添加水印
        enable_web_search: 是否开启联网搜索（仅 5.0-lite 支持）
        optimize_prompt_mode: 提示词优化模式
        image: 参考图 URL（单张或列表）

    Returns:
        包含生成图像信息的字典
    """
    request_data = {
        "model": model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": watermark,
    }

    # 添加 output_format（仅 5.0-lite 支持）
    if "5-0" in model or "5.0" in model:
        request_data["output_format"] = output_format

    # 添加联网搜索工具（仅 5.0-lite 支持）
    if enable_web_search and ("5-0" in model or "5.0" in model):
        request_data["tools"] = [{"type": "web_search"}]

    # 添加提示词优化选项
    if optimize_prompt_mode != "standard":
        request_data["optimize_prompt_options"] = {"mode": optimize_prompt_mode}

    # 添加参考图
    if image:
        request_data["image"] = image

    result = await _call_api(request_data)
    image_data = result["data"][0]

    # 构建返回结果
    response = {
        "url": image_data.get("url", ""),
        "size": image_data.get("size", size),
        "model": model,
        "generated_images": result.get("usage", {}).get("generated_images", 1),
    }

    # 如果有联网搜索信息，添加到返回结果
    if "usage" in result and "tool_usage" in result["usage"]:
        response["web_search_count"] = result["usage"]["tool_usage"].get("web_search", 0)

    return response


@mcp.tool(
    name="generate_sequential_images",
    description="使用豆包图像生成模型创建一组内容关联的图片（组图）。支持文生组图、单图生组图、多图生组图。仅 doubao-seedream-5.0/4.5/4.0 模型支持此功能。",
)
async def generate_sequential_images(
    prompt: str = Field(..., description="图像生成提示词，详细描述想要生成的图像内容。建议不超过300个汉字或600个英文单词"),
    model: str = Field(
        default=DEFAULT_MODEL,
        description="模型名称。可选值：doubao-seedream-5-0-260128(推荐), doubao-seedream-4-5-251128, doubao-seedream-4-0-250828",
    ),
    size: str = Field(
        default=DEFAULT_SIZE,
        description="图像尺寸。5.0-lite 支持 2K/3K；4.5 支持 2K/4K；4.0 支持 1K/2K/4K。也可指定具体像素如 2048x2048",
    ),
    output_format: Literal["png", "jpeg"] = Field(
        default="jpeg",
        description="输出图像格式。仅 5.0-lite 支持自定义，默认 jpeg。可选：png, jpeg",
    ),
    watermark: bool = Field(
        default=False,
        description="是否在生成的图像上添加水印（右下角AI生成字样）",
    ),
    enable_web_search: bool = Field(
        default=False,
        description="是否开启联网搜索功能。开启后模型会根据提示词自主判断是否需要搜索互联网内容。仅 5.0-lite 支持",
    ),
    max_images: int = Field(
        default=4,
        ge=1,
        le=15,
        description="最多可生成的图片数量，取值范围 [1, 15]。注意：参考图数量 + 生成图片数量 ≤ 15",
    ),
    image: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="参考图 URL，支持单张或多张（最多14张）。可传 URL 或 Base64 编码。用于基于参考图生成系列图片",
    ),
) -> dict:
    """
    使用豆包图像生成模型创建一组内容关联的图片（组图）。

    支持以下场景：
    - 文生组图：仅提供文本提示词
    - 单图生组图：提供单张参考图 + 文本提示词
    - 多图生组图：提供多张参考图（2-14张）+ 文本提示词

    Args:
        prompt: 图像生成提示词
        model: 模型名称
        size: 图像尺寸
        output_format: 输出图像格式（仅 5.0-lite 支持）
        watermark: 是否添加水印
        enable_web_search: 是否开启联网搜索（仅 5.0-lite 支持）
        max_images: 最多可生成的图片数量 [1, 15]
        image: 参考图 URL（单张或列表）

    Returns:
        包含生成图像 URL 列表的字典
    """
    request_data = {
        "model": model,
        "prompt": prompt,
        "sequential_image_generation": "auto",
        "sequential_image_generation_options": {"max_images": max_images},
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": watermark,
    }

    # 添加 output_format（仅 5.0-lite 支持）
    if "5-0" in model or "5.0" in model:
        request_data["output_format"] = output_format

    # 添加联网搜索工具（仅 5.0-lite 支持）
    if enable_web_search and ("5-0" in model or "5.0" in model):
        request_data["tools"] = [{"type": "web_search"}]

    # 添加参考图
    if image:
        request_data["image"] = image

    result = await _call_api(request_data)

    image_urls = []
    image_sizes = []
    for item in result["data"]:
        url = item.get("url", "")
        if url:
            image_urls.append(url)
        size = item.get("size", size)
        image_sizes.append(size)

    # 构建返回结果
    response = {
        "urls": image_urls,
        "sizes": image_sizes,
        "count": len(image_urls),
        "model": model,
        "generated_images": result.get("usage", {}).get("generated_images", len(image_urls)),
        "output_tokens": result.get("usage", {}).get("output_tokens", 0),
    }

    # 如果有联网搜索信息，添加到返回结果
    if "usage" in result and "tool_usage" in result["usage"]:
        response["web_search_count"] = result["usage"]["tool_usage"].get("web_search", 0)

    return response


@mcp.tool(
    name="get_model_info",
    description="获取可用的豆包图像生成模型列表及其详细信息，包括支持的分辨率、功能特性等。",
)
async def get_model_info() -> dict:
    """
    获取可用的豆包图像生成模型列表及其详细信息。

    Returns:
        包含所有可用模型信息的字典
    """
    models = {}
    for model_id, info in MODEL_INFO.items():
        models[model_id] = {
            "name": info["name"],
            "description": info["description"],
            "supported_sizes": info["sizes"],
            "features": info["features"],
            "max_reference_images": info["max_images"],
            "supports_web_search": info["supports_web_search"],
            "supports_output_format": info["supports_output_format"],
            "supports_optimize_prompt": info["supports_optimize_prompt"],
        }

    return {
        "models": models,
        "default_model": DEFAULT_MODEL,
        "recommended_model": "doubao-seedream-5-0-260128",
    }


@mcp.tool(
    name="get_preset_templates",
    description="获取预设的图像生成模板列表，包括人物肖像、风景、产品、动漫、LOGO、海报等模板。",
)
async def get_preset_templates() -> dict:
    """
    获取预设的图像生成模板列表。

    Returns:
        包含所有预设模板的字典
    """
    templates = {}
    for template_id, template in PRESET_TEMPLATES.items():
        templates[template_id] = {
            "name": template["name"],
            "description": template["description"],
            "prompt_template": template["prompt_template"],
            "default_size": template["size"],
        }

    return {
        "templates": templates,
        "usage": "使用 generate_image_with_preset 工具，传入 template_id、subject 和可选的 style 参数",
    }


@mcp.tool(
    name="generate_image_with_preset",
    description="使用预设模板快速生成图像。提供模板名称、主体和风格即可自动生成提示词并创建图像。",
)
async def generate_image_with_preset(
    template_id: str = Field(..., description="模板ID。可选值：portrait(人物肖像), landscape(风景), product(产品展示), anime(动漫风格), logo(品牌LOGO), poster(海报设计)"),
    subject: str = Field(..., description="图像主体，例如'一只可爱的猫咪'、'现代科技感的智能手表'"),
    style: str = Field(
        default="现代",
        description="图像风格，例如'复古'、'赛博朋克'、'水彩'、'极简'等",
    ),
    model: str = Field(
        default=DEFAULT_MODEL,
        description="模型名称。可选值：doubao-seedream-5-0-260128(推荐), doubao-seedream-4-5-251128, doubao-seedream-4-0-250828",
    ),
    size: Optional[str] = Field(
        default=None,
        description="图像尺寸，不指定时使用模板默认值",
    ),
    output_format: Literal["png", "jpeg"] = Field(
        default="jpeg",
        description="输出图像格式。仅 5.0-lite 支持自定义，默认 jpeg。可选：png, jpeg",
    ),
    watermark: bool = Field(
        default=False,
        description="是否在生成的图像上添加水印（右下角AI生成字样）",
    ),
    enable_web_search: bool = Field(
        default=False,
        description="是否开启联网搜索功能。仅 5.0-lite 支持",
    ),
    image: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="参考图 URL，支持单张或多张。用于图生图、图像编辑等场景",
    ),
) -> dict:
    """
    使用预设模板快速生成图像。

    Args:
        template_id: 模板ID
        subject: 图像主体
        style: 图像风格
        model: 模型名称
        size: 图像尺寸
        output_format: 输出图像格式
        watermark: 是否添加水印
        enable_web_search: 是否开启联网搜索
        image: 参考图 URL

    Returns:
        包含生成图像信息的字典
    """
    # 检查模板ID是否有效
    if template_id not in PRESET_TEMPLATES:
        available_templates = ", ".join(PRESET_TEMPLATES.keys())
        raise ValueError(f"无效的模板ID '{template_id}'。可用的模板：{available_templates}")

    # 获取模板
    template = PRESET_TEMPLATES[template_id]

    # 生成提示词
    prompt = template["prompt_template"].format(subject=subject, style=style)

    # 使用模板的默认尺寸（如果未指定）
    if size is None:
        size = template["size"]

    # 调用 generate_image 工具
    request_data = {
        "model": model,
        "prompt": prompt,
        "sequential_image_generation": "disabled",
        "response_format": "url",
        "size": size,
        "stream": False,
        "watermark": watermark,
    }

    # 添加 output_format（仅 5.0-lite 支持）
    if "5-0" in model or "5.0" in model:
        request_data["output_format"] = output_format

    # 添加联网搜索工具（仅 5.0-lite 支持）
    if enable_web_search and ("5-0" in model or "5.0" in model):
        request_data["tools"] = [{"type": "web_search"}]

    # 添加参考图
    if image:
        request_data["image"] = image

    result = await _call_api(request_data)
    image_data = result["data"][0]

    # 构建返回结果
    response = {
        "template_id": template_id,
        "template_name": template["name"],
        "generated_prompt": prompt,
        "url": image_data.get("url", ""),
        "size": image_data.get("size", size),
        "model": model,
        "generated_images": result.get("usage", {}).get("generated_images", 1),
    }

    # 如果有联网搜索信息，添加到返回结果
    if "usage" in result and "tool_usage" in result["usage"]:
        response["web_search_count"] = result["usage"]["tool_usage"].get("web_search", 0)

    return response


# 注意：Base64 输出工具已禁用，因为 Base64 数据会占用大量 token，容易撑爆模型的输入上下文
# 如需使用，请取消下方的注释

# @mcp.tool(
#     name="generate_image_b64",
#     description="【已禁用】生成图像并返回 Base64 编码数据。因会撑爆输入上下文，默认禁用。",
# )
# async def generate_image_b64(
#     prompt: str = Field(..., description="图像生成提示词，详细描述想要生成的图像内容"),
#     model: str = Field(
#         default=DEFAULT_MODEL,
#         description="模型名称。可选值：doubao-seedream-5-0-260128(推荐), doubao-seedream-4-5-251128, doubao-seedream-4-0-250828",
#     ),
#     size: str = Field(
#         default=DEFAULT_SIZE,
#         description="图像尺寸。5.0-lite 支持 2K/3K；4.5 支持 2K/4K；4.0 支持 1K/2K/4K",
#     ),
#     output_format: Literal["png", "jpeg"] = Field(
#         default="jpeg",
#         description="输出图像格式。仅 5.0-lite 支持自定义。可选：png, jpeg",
#     ),
#     watermark: bool = Field(
#         default=False,
#         description="是否在生成的图像上添加水印",
#     ),
#     enable_web_search: bool = Field(
#         default=False,
#         description="是否开启联网搜索功能。仅 5.0-lite 支持",
#     ),
#     image: Optional[Union[str, List[str]]] = Field(
#         default=None,
#         description="参考图 URL，支持单张或多张",
#     ),
# ) -> dict:
#     """
#     生成图像并返回 Base64 编码数据。
# 
#     Args:
#         prompt: 图像生成提示词
#         model: 模型名称
#         size: 图像尺寸
#         output_format: 输出图像格式
#         watermark: 是否添加水印
#         enable_web_search: 是否开启联网搜索
#         image: 参考图 URL
# 
#     Returns:
#         包含 Base64 编码图像数据的字典
#     """
#     request_data = {
#         "model": model,
#         "prompt": prompt,
#         "sequential_image_generation": "disabled",
#         "response_format": "b64_json",  # 使用 Base64 格式返回
#         "size": size,
#         "stream": False,
#         "watermark": watermark,
#     }
# 
#     # 添加 output_format（仅 5.0-lite 支持）
#     if "5-0" in model or "5.0" in model:
#         request_data["output_format"] = output_format
# 
#     # 添加联网搜索工具（仅 5.0-lite 支持）
#     if enable_web_search and ("5-0" in model or "5.0" in model):
#         request_data["tools"] = [{"type": "web_search"}]
# 
#     # 添加参考图
#     if image:
#         request_data["image"] = image
# 
#     result = await _call_api(request_data)
#     image_data = result["data"][0]
# 
#     # 构建返回结果
#     response = {
#         "b64_json": image_data.get("b64_json", ""),
#         "size": image_data.get("size", size),
#         "model": model,
#         "generated_images": result.get("usage", {}).get("generated_images", 1),
#         "output_format": output_format if ("5-0" in model or "5.0" in model) else "jpeg",
#         "note": "Base64 数据可直接用于 <img src='data:image/jpeg;base64,...'> 或 <img src='data:image/png;base64,...'>",
#     }
# 
#     # 如果有联网搜索信息，添加到返回结果
#     if "usage" in result and "tool_usage" in result["usage"]:
#         response["web_search_count"] = result["usage"]["tool_usage"].get("web_search", 0)
# 
#     return response
# 
# 
# @mcp.tool(
#     name="generate_sequential_images_b64",
#     description="【已禁用】生成组图并返回 Base64 编码数据。因会撑爆输入上下文，默认禁用。",
# )
# async def generate_sequential_images_b64(
#     prompt: str = Field(..., description="图像生成提示词"),
#     model: str = Field(
#         default=DEFAULT_MODEL,
#         description="模型名称",
#     ),
#     size: str = Field(
#         default=DEFAULT_SIZE,
#         description="图像尺寸",
#     ),
#     output_format: Literal["png", "jpeg"] = Field(
#         default="jpeg",
#         description="输出图像格式。仅 5.0-lite 支持自定义",
#     ),
#     watermark: bool = Field(
#         default=False,
#         description="是否添加水印",
#     ),
#     enable_web_search: bool = Field(
#         default=False,
#         description="是否开启联网搜索。仅 5.0-lite 支持",
#     ),
#     max_images: int = Field(
#         default=4,
#         ge=1,
#         le=15,
#         description="最多可生成的图片数量 [1, 15]",
#     ),
#     image: Optional[Union[str, List[str]]] = Field(
#         default=None,
#         description="参考图 URL，支持单张或多张（最多14张）",
#     ),
# ) -> dict:
#     """
#     生成组图并返回 Base64 编码数据。
# 
#     Args:
#         prompt: 图像生成提示词
#         model: 模型名称
#         size: 图像尺寸
#         output_format: 输出图像格式
#         watermark: 是否添加水印
#         enable_web_search: 是否开启联网搜索
#         max_images: 最多可生成的图片数量
#         image: 参考图 URL
# 
#     Returns:
#         包含 Base64 编码图像数据列表的字典
#     """
#     request_data = {
#         "model": model,
#         "prompt": prompt,
#         "sequential_image_generation": "auto",
#         "sequential_image_generation_options": {"max_images": max_images},
#         "response_format": "b64_json",
#         "size": size,
#         "stream": False,
#         "watermark": watermark,
#     }
# 
#     # 添加 output_format（仅 5.0-lite 支持）
#     if "5-0" in model or "5.0" in model:
#         request_data["output_format"] = output_format
# 
#     # 添加联网搜索工具（仅 5.0-lite 支持）
#     if enable_web_search and ("5-0" in model or "5.0" in model):
#         request_data["tools"] = [{"type": "web_search"}]
# 
#     # 添加参考图
#     if image:
#         request_data["image"] = image
# 
#     result = await _call_api(request_data)
# 
#     image_b64_list = []
#     image_sizes = []
#     for item in result["data"]:
#         b64 = item.get("b64_json", "")
#         if b64:
#             image_b64_list.append(b64)
#         size = item.get("size", size)
#         image_sizes.append(size)
# 
#     # 构建返回结果
#     response = {
#         "b64_json_list": image_b64_list,
#         "sizes": image_sizes,
#         "count": len(image_b64_list),
#         "model": model,
#         "generated_images": result.get("usage", {}).get("generated_images", len(image_b64_list)),
#         "output_tokens": result.get("usage", {}).get("output_tokens", 0),
#         "output_format": output_format if ("5-0" in model or "5.0" in model) else "jpeg",
#     }
# 
#     # 如果有联网搜索信息，添加到返回结果
#     if "usage" in result and "tool_usage" in result["usage"]:
#         response["web_search_count"] = result["usage"]["tool_usage"].get("web_search", 0)
# 
#     return response


def main():
    """启动 MCP 服务器"""
    mcp.run()


if __name__ == "__main__":
    main()
