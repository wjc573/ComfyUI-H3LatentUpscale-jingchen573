"""MiniMax H3 专用 latent 空间放大节点。

以 ComfyUI 官方 LatentUpscaleBy 为基础：
- 保留相同的放大方法与 scale_by 输入；
- 从输入视频 latent 自身读取一采宽高，不需要额外传入分辨率；
- 自动把二采 latent 宽高对齐到偶数，确保像素宽高可被 32 整除；
- 对齐结果不超过用户设置的目标放大倍数。
"""

import math

import comfy.utils


class H3LatentUpscaleByJingchen573:
    """按 H3 的 2×2 latent patch 网格安全放大视频 latent。"""

    upscale_methods = ["nearest-exact", "bilinear", "area", "bicubic", "bislerp"]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "samples": ("LATENT",),
                "upscale_method": (cls.upscale_methods,),
                "scale_by": (
                    "FLOAT",
                    {"default": 1.5, "min": 0.01, "max": 8.0, "step": 0.01},
                ),
            }
        }

    RETURN_TYPES = ("LATENT", "INT", "INT", "FLOAT", "FLOAT", "STRING")
    RETURN_NAMES = (
        "LATENT",
        "width",
        "height",
        "effective_scale_x",
        "effective_scale_y",
        "alignment_info",
    )
    FUNCTION = "upscale"
    CATEGORY = "model/latent"
    DESCRIPTION = (
        "MiniMax H3 专用 latent 放大。自动使二采宽高可被 32 整除，"
        "避免 H3 因奇数 latent 轴进行内部 circular padding。"
    )

    # H3 视频 VAE 的空间压缩率为 16；DiT 使用 2×2 latent patch。
    # 因此像素宽高要被 32 整除，latent 宽高就必须被 2 整除。
    LATENT_ALIGNMENT = 2
    H3_VAE_SPATIAL_DOWNSCALE = 16

    @classmethod
    def _floor_aligned(cls, value):
        """向下对齐到偶数 latent 单位，且至少保留一个完整对齐单位。"""
        return max(
            cls.LATENT_ALIGNMENT,
            math.floor(value / cls.LATENT_ALIGNMENT) * cls.LATENT_ALIGNMENT,
        )

    @classmethod
    def _calculate_aligned_size(cls, latent_width, latent_height, scale_by):
        """计算不超过目标倍率的 H3 合法 latent 宽高。

        短边先向下对齐；长边再寻找最接近短边实际倍率的合法值，
        同时不允许长边超过用户指定的 scale_by。
        """
        if latent_width <= 0 or latent_height <= 0:
            raise ValueError("输入 latent 的宽高必须大于 0")

        if latent_width >= latent_height:
            long_is_width = True
            long_in, short_in = latent_width, latent_height
        else:
            long_is_width = False
            long_in, short_in = latent_height, latent_width

        short_out = cls._floor_aligned(short_in * scale_by)
        short_effective_scale = short_out / short_in
        ideal_long = long_in * short_effective_scale
        long_cap = cls._floor_aligned(long_in * scale_by)

        # 比较理想长边两侧的合法偶数值；只保留不超过目标倍率上限的值。
        lower = cls._floor_aligned(ideal_long)
        upper = lower + cls.LATENT_ALIGNMENT
        candidates = {
            candidate
            for candidate in (lower, upper, long_cap)
            if cls.LATENT_ALIGNMENT <= candidate <= long_cap
        }
        long_out = min(candidates, key=lambda candidate: (abs(candidate - ideal_long), candidate))

        if long_is_width:
            return long_out, short_out
        return short_out, long_out

    def upscale(self, samples, upscale_method, scale_by):
        source = samples["samples"]
        latent_width = source.shape[-1]
        latent_height = source.shape[-2]

        output_latent_width, output_latent_height = self._calculate_aligned_size(
            latent_width, latent_height, scale_by
        )

        result = samples.copy()
        result["samples"] = comfy.utils.common_upscale(
            source,
            output_latent_width,
            output_latent_height,
            upscale_method,
            "disabled",
        )

        input_pixel_width = latent_width * self.H3_VAE_SPATIAL_DOWNSCALE
        input_pixel_height = latent_height * self.H3_VAE_SPATIAL_DOWNSCALE
        output_pixel_width = output_latent_width * self.H3_VAE_SPATIAL_DOWNSCALE
        output_pixel_height = output_latent_height * self.H3_VAE_SPATIAL_DOWNSCALE
        effective_scale_x = output_latent_width / latent_width
        effective_scale_y = output_latent_height / latent_height

        alignment_info = (
            f"输入: {input_pixel_width} x {input_pixel_height} | "
            f"目标倍率: {scale_by:.4f} | "
            f"输出: {output_pixel_width} x {output_pixel_height} | "
            f"实际倍率 X/Y: {effective_scale_x:.6f} / {effective_scale_y:.6f} | "
            "32 像素对齐: 是"
        )

        return (
            result,
            output_pixel_width,
            output_pixel_height,
            effective_scale_x,
            effective_scale_y,
            alignment_info,
        )


NODE_CLASS_MAPPINGS = {
    "H3LatentUpscaleByJingchen573": H3LatentUpscaleByJingchen573,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "H3LatentUpscaleByJingchen573": "H3 Latent Upscale By -jingchen573",
}
