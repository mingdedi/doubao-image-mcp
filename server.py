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
DEFAULT_MODEL = "doubao-seedream-4-5-251128"
DEFAULT_SIZE = "2K"
DEFAULT_TIMEOUT = 1800.0

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

        if "data" not in result or not result["data"]:
            raise RuntimeError("未返回任何图像数据")

        return result
    except httpx.TimeoutException:
        raise RuntimeError(f"API 请求超时（{DEFAULT_TIMEOUT}秒）")
    except httpx.RequestError as e:
        raise RuntimeError(f"网络请求失败：{str(e)}")


@mcp.tool(
    name="generate_image",
    description="使用豆包图像生成模型创建图像。支持文生图、图生图、多图融合等模式。",
)
async def generate_image(
    prompt: str = Field(..., description="图像生成提示词，详细描述想要生成的图像内容"),
    model: str = Field(
        default=DEFAULT_MODEL,
        description="模型名称，可选值：doubao-seedream-4-5-251128",
    ),
    size: str = Field(
        default=DEFAULT_SIZE,
        description="图像尺寸，同时需要在 prompt 中用自然语言描述图片宽高比、图片形状或图片用途，最终由模型判断生成图片的大小，可选值：2K, 4K",
    ),
    watermark: bool = Field(
        default=False,
        description="是否在生成的图像上添加水印",
    ),
    negative_prompt: Optional[str] = Field(
        default=None,
        description="负面提示词，描述不希望出现在图像中的内容",
    ),
    image: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="参考图 URL，支持单张或多张。单张图传字符串 URL，多张图传 URL 列表。用于图生图、图像编辑、多图融合等场景",
    )
) -> dict:
    """
    使用豆包图像生成模型创建图像。

    Args:
        prompt: 图像生成提示词
        model: 模型名称
        size: 图像尺寸
        watermark: 是否添加水印
        negative_prompt: 负面提示词
        image: 参考图 URL（单张或列表）

    Returns:
        包含生成图像 URL 的字典
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

    if image:
        request_data["image"] = image
    if negative_prompt:
        request_data["negative_prompt"] = negative_prompt

    result = await _call_api(request_data)
    image_data = result["data"][0]

    return {
        "url": image_data.get("url", ""),
        "revised_prompt": image_data.get("revised_prompt", prompt),
        "model": model,
        "size": size,
    }


@mcp.tool(
    name="generate_sequential_images",
    description="使用豆包图像生成模型创建一组内容关联的图片（组图）。仅 doubao-seedream-5.0/4.5/4.0 模型支持此功能。",
)
async def generate_sequential_images(
    prompt: str = Field(..., description="图像生成提示词，详细描述想要生成的图像内容"),
    model: str = Field(
        default=DEFAULT_MODEL,
        description="模型名称，可选值：doubao-seedream-4-5-251128",
    ),
    size: str = Field(
        default=DEFAULT_SIZE,
        description="图像尺寸，同时需要在 prompt 中用自然语言描述图片宽高比、图片形状或图片用途，可选值：2K, 4K",
    ),
    watermark: bool = Field(
        default=False,
        description="是否在生成的图像上添加水印",
    ),
    negative_prompt: Optional[str] = Field(
        default=None,
        description="负面提示词，描述不希望出现在图像中的内容",
    ),
    max_images: int = Field(
        default=4,
        ge=1,
        le=15,
        description="最多可生成的图片数量，取值范围 [1, 15]。注意：参考图数量 + 生成图片数量 ≤ 15",
    ),
    image: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="参考图 URL，支持单张或多张。单张图传字符串 URL，多张图传 URL 列表。用于基于参考图生成系列图片",
    ),
) -> dict:
    """
    使用豆包图像生成模型创建一组内容关联的图片（组图）。

    Args:
        prompt: 图像生成提示词
        model: 模型名称
        size: 图像尺寸
        watermark: 是否添加水印
        negative_prompt: 负面提示词
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

    if image:
        request_data["image"] = image
    if negative_prompt:
        request_data["negative_prompt"] = negative_prompt

    result = await _call_api(request_data)

    image_urls = []
    revised_prompt = prompt
    for item in result["data"]:
        url = item.get("url", "")
        if url:
            image_urls.append(url)
        if "revised_prompt" in item:
            revised_prompt = item["revised_prompt"]

    return {
        "urls": image_urls,
        "count": len(image_urls),
        "revised_prompt": revised_prompt,
        "model": model,
        "size": size,
    }


def main():
    """启动 MCP 服务器"""
    mcp.run()


if __name__ == "__main__":
    main()
