# ComfyUI H3 Latent Upscale — jingchen573

[中文](#中文) · [English](#english)

A minimal ComfyUI custom node for safely upscaling MiniMax H3 video latents before a second sampling pass.

一个用于 MiniMax H3 二次采样前安全放大视频 latent 的轻量 ComfyUI 自定义节点。

> **在线工作流与效果对比**
>
> 可在 RunningHub 免费查看并下载配套工作流体验：
> [MiniMax H3 latent 放大双采 + 8 步 LoRA 在线工作流](https://www.runninghub.ai/post/2088079643785330689?inviteCode=rh-v1495)
>
> 边缘效果对比：
>
> - [官方 `LatentUpscaleBy`：边缘色条异常]
> - 

https://github.com/user-attachments/assets/9d827b25-761d-4907-a796-e48c24748864



> - [本节点：边缘正常]
> - 

https://github.com/user-attachments/assets/06969417-3cb5-4020-aeee-7c2e936860d1



---

## 中文

### 功能

ComfyUI 官方 `LatentUpscaleBy` 会分别对 latent 宽高执行普通四舍五入。MiniMax H3 的视频 VAE 空间压缩率为 16，而 DiT 使用 2×2 latent patch，因此二采视频 latent 的宽高需要是偶数；换算成像素后，就是宽高都应当能被 32 整除。

当某一条 latent 轴为奇数时，H3 会在模型内部进行 circular padding，采样结束后再裁回原尺寸。这可能在视频右侧或底部产生边缘接缝、色条或异常纹理。

`H3 Latent Upscale By -jingchen573` 保留官方节点的输入和放大方法，只新增 H3 对齐逻辑：

- 直接从输入视频 latent 读取一采宽高，无需额外传入分辨率；
- 自动把二采 latent 宽高对齐为偶数；
- 确保对应像素宽高均能被 32 整除；
- 对齐后的横纵倍率均不超过用户设置的 `scale_by`；
- 尽可能保持输入画面的宽高比。

### 示例

| 一采分辨率 | 目标倍率 | 官方节点结果 | 本节点结果 |
|---|---:|---:|---:|
| 1280×736 | 1.50 | 1920×1104（latent 120×69） | **1888×1088（latent 118×68）** |
| 736×416 | 1.40 | 1024×576（latent 64×36） | **1024×576（latent 64×36）** |

第一个例子中，官方结果的 latent 高度为奇数69，H3需要内部补边；本节点输出118×68，两轴均为偶数。

### 安装

将整个文件夹复制到：

```text
ComfyUI/custom_nodes/ComfyUI-H3LatentUpscale-jingchen573/
```

目录结构：

```text
ComfyUI/
└── custom_nodes/
    └── ComfyUI-H3LatentUpscale-jingchen573/
        └── __init__.py
```

然后重新启动 ComfyUI。

### 使用

在节点搜索中添加：

```text
H3 Latent Upscale By -jingchen573
```

用它替换官方 `LatentUpscaleBy` 即可。输入保持一致：

- `samples`
- `upscale_method`
- `scale_by`

支持与官方节点相同的放大方法：

- `nearest-exact`
- `bilinear`
- `area`
- `bicubic`
- `bislerp`

附加输出：

- `width`：最终像素宽度
- `height`：最终像素高度
- `effective_scale_x`：实际横向倍率
- `effective_scale_y`：实际纵向倍率
- `alignment_info`：输入、目标倍率、输出尺寸与对齐信息

> 本节点只处理空间尺寸对齐。对于 H3 音视频联合工作流，应当先分离 AV latent，只把视频 latent 连接到本节点；音频 latent 不应进行空间放大。

### 原理

```text
H3视频VAE空间压缩率：16
H3 DiT空间patch：2×2 latent
安全像素对齐：16×2 = 32
```

节点先将短边向下对齐到偶数 latent，再为长边选择最接近短边实际倍率、且不超过目标倍率的合法偶数值。这样可以在不依赖固定分辨率列表的情况下，避免 H3 因奇数 latent 轴进行模型内部补边。

---

## English

### What it does

ComfyUI's built-in `LatentUpscaleBy` independently rounds the latent width and height. MiniMax H3 uses a 16× spatial video-VAE downscale and 2×2 spatial latent patches in the DiT, so both video-latent axes should be even. In pixel space, both output axes should therefore be divisible by 32.

If either latent axis is odd, H3 internally applies circular padding for patchification and crops the denoiser output back afterward. This can produce an edge seam, color strip, or abnormal texture near the right or bottom border.

`H3 Latent Upscale By -jingchen573` keeps the same inputs and interpolation methods as the built-in node, while adding H3-aware alignment:

- Reads the first-pass dimensions directly from the incoming video latent;
- Requires no separate width or height input;
- Aligns both second-pass latent axes to even values;
- Guarantees pixel dimensions divisible by 32;
- Never exceeds the requested `scale_by` on either axis;
- Preserves the source aspect ratio as closely as the aligned grid permits.

### Examples

| First-pass size | Requested scale | Built-in result | This node |
|---|---:|---:|---:|
| 1280×736 | 1.50 | 1920×1104 (latent 120×69) | **1888×1088 (latent 118×68)** |
| 736×416 | 1.40 | 1024×576 (latent 64×36) | **1024×576 (latent 64×36)** |

In the first example, the built-in result has an odd latent height of 69, so H3 must pad it internally. This node produces 118×68 instead, keeping both latent axes even.

### Installation

Copy the entire folder into:

```text
ComfyUI/custom_nodes/ComfyUI-H3LatentUpscale-jingchen573/
```

Expected layout:

```text
ComfyUI/
└── custom_nodes/
    └── ComfyUI-H3LatentUpscale-jingchen573/
        └── __init__.py
```

Restart ComfyUI afterward.

### Usage

Add this node from the node search:

```text
H3 Latent Upscale By -jingchen573
```

Use it in place of the built-in `LatentUpscaleBy`. The inputs remain the same:

- `samples`
- `upscale_method`
- `scale_by`

Supported interpolation methods match the built-in node:

- `nearest-exact`
- `bilinear`
- `area`
- `bicubic`
- `bislerp`

Additional outputs:

- `width`: final pixel width
- `height`: final pixel height
- `effective_scale_x`: actual horizontal scale
- `effective_scale_y`: actual vertical scale
- `alignment_info`: input size, requested scale, output size, and alignment summary

> This node only handles spatial alignment. In a joint H3 audio-video workflow, separate the AV latent first and connect only the video latent to this node. Do not spatially upscale the audio latent.

### How it works

```text
H3 video-VAE spatial downscale: 16×
H3 DiT spatial patch: 2×2 latent
Safe pixel alignment: 16×2 = 32
```

The node first aligns the short latent axis downward to an even value. It then selects the legal even value for the long axis that most closely matches the short axis's effective scale without exceeding the requested scale. This avoids H3's internal odd-axis padding without relying on a small list of hand-picked resolutions.

---

## License

No license has been specified yet. All rights reserved by the repository owner unless a license is added later.
