# -*- coding: utf-8 -*-
"""
图像哈希工具模块
实现感知哈希(pHash)算法用于图像唯一标识生成
支持相似图像检测和缓存键生成
"""
import hashlib
import logging
from typing import Optional, Dict, Any
import io

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from PIL import Image
    IMAGE_LIBS_AVAILABLE = True
except ImportError:
    IMAGE_LIBS_AVAILABLE = False
    logger.warning("PIL 或 numpy 不可用，图像哈希功能受限")


class ImageHash:
    """
    图像哈希生成器

    实现多种哈希算法：
    1. MD5: 精确匹配，速度快
    2. pHash (感知哈希): 相似图像匹配，抗干扰
    3. dHash (差异哈希): 简单高效的相似图像检测
    """

    @staticmethod
    def compute_md5(image_data: bytes) -> str:
        """
        计算图像的 MD5 哈希值

        Args:
            image_data: 图像二进制数据

        Returns:
            MD5 哈希字符串（32位十六进制）
        """
        return hashlib.md5(image_data).hexdigest()

    @staticmethod
    def compute_phash(image_data: bytes, hash_size: int = 8) -> Optional[str]:
        """
        计算感知哈希 (pHash)

        pHash 算法步骤：
        1. 缩放图像到 (hash_size+1) x hash_size
        2. 转换为灰度图
        3. 计算相邻像素的差异
        4. 生成二进制哈希值

        特点：
        - 对缩放、旋转、亮度变化具有鲁棒性
        - 适合相似图像检索
        - 汉明距离 <= 5 通常认为是相似图像

        Args:
            image_data: 图像二进制数据
            hash_size: 哈希尺寸，默认 8（生成 64 位哈希）

        Returns:
            感知哈希字符串，失败返回 None
        """
        if not IMAGE_LIBS_AVAILABLE:
            logger.warning("图像处理库不可用，无法计算 pHash")
            return None

        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.convert("L")
            image = image.resize(
                (hash_size + 1, hash_size),
                Image.Resampling.LANCZOS
            )

            pixels = np.array(image, dtype=np.float64)
            diff = pixels[:, 1:] > pixels[:, :-1]

            hash_bits = diff.flatten()
            hash_int = 0
            for bit in hash_bits:
                hash_int = (hash_int << 1) | int(bit)

            hash_hex = f"{hash_int:0{hash_size * hash_size // 4}x}"
            return hash_hex

        except Exception as e:
            logger.error(f"计算 pHash 失败: {e}")
            return None

    @staticmethod
    def compute_dhash(image_data: bytes, hash_size: int = 8) -> Optional[str]:
        """
        计算差异哈希 (dHash)

        dHash 算法步骤：
        1. 缩放图像到 (hash_size+1) x hash_size
        2. 转换为灰度图
        3. 比较相邻列的像素值
        4. 生成二进制哈希值

        特点：
        - 比 pHash 更简单快速
        - 对水平翻转敏感

        Args:
            image_data: 图像二进制数据
            hash_size: 哈希尺寸，默认 8

        Returns:
            差异哈希字符串，失败返回 None
        """
        if not IMAGE_LIBS_AVAILABLE:
            logger.warning("图像处理库不可用，无法计算 dHash")
            return None

        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.convert("L")
            image = image.resize(
                (hash_size + 1, hash_size),
                Image.Resampling.LANCZOS
            )

            pixels = np.array(image, dtype=np.float64)
            diff = pixels[:, 1:] > pixels[:, :-1]

            hash_bits = diff.flatten()
            hash_int = 0
            for bit in hash_bits:
                hash_int = (hash_int << 1) | int(bit)

            hash_hex = f"{hash_int:0{hash_size * hash_size // 4}x}"
            return hash_hex

        except Exception as e:
            logger.error(f"计算 dHash 失败: {e}")
            return None

    @staticmethod
    def compute_ahash(image_data: bytes, hash_size: int = 8) -> Optional[str]:
        """
        计算平均哈希 (aHash)

        aHash 算法步骤：
        1. 缩放图像到 hash_size x hash_size
        2. 转换为灰度图
        3. 计算平均像素值
        4. 每个像素与平均值比较生成哈希

        特点：
        - 最简单的哈希算法
        - 对亮度变化敏感

        Args:
            image_data: 图像二进制数据
            hash_size: 哈希尺寸，默认 8

        Returns:
            平均哈希字符串，失败返回 None
        """
        if not IMAGE_LIBS_AVAILABLE:
            logger.warning("图像处理库不可用，无法计算 aHash")
            return None

        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.convert("L")
            image = image.resize(
                (hash_size, hash_size),
                Image.Resampling.LANCZOS
            )

            pixels = np.array(image, dtype=np.float64)
            avg = pixels.mean()
            diff = pixels > avg

            hash_bits = diff.flatten()
            hash_int = 0
            for bit in hash_bits:
                hash_int = (hash_int << 1) | int(bit)

            hash_hex = f"{hash_int:0{hash_size * hash_size // 4}x}"
            return hash_hex

        except Exception as e:
            logger.error(f"计算 aHash 失败: {e}")
            return None

    @staticmethod
    def hamming_distance(hash1: str, hash2: str) -> int:
        """
        计算两个哈希值的汉明距离

        汉明距离表示两个等长字符串对应位置不同字符的数量
        对于图像哈希，汉明距离越小表示图像越相似

        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值

        Returns:
            汉明距离（整数）

        Raises:
            ValueError: 哈希长度不匹配时抛出
        """
        if len(hash1) != len(hash2):
            raise ValueError(
                f"哈希长度不匹配: {len(hash1)} vs {len(hash2)}"
            )

        distance = 0
        for c1, c2 in zip(hash1, hash2):
            val1 = int(c1, 16)
            val2 = int(c2, 16)
            xor = val1 ^ val2
            distance += bin(xor).count("1")

        return distance

    @staticmethod
    def is_similar(
        hash1: str,
        hash2: str,
        threshold: int = 5
    ) -> bool:
        """
        判断两个哈希是否表示相似图像

        Args:
            hash1: 第一个哈希值
            hash2: 第二个哈希值
            threshold: 汉明距离阈值，默认 5

        Returns:
            是否相似
        """
        try:
            distance = ImageHash.hamming_distance(hash1, hash2)
            return distance <= threshold
        except Exception:
            return False

    @staticmethod
    def compute_all_hashes(
        image_data: bytes,
        hash_size: int = 8
    ) -> Dict[str, Optional[str]]:
        """
        计算所有类型的哈希值

        Args:
            image_data: 图像二进制数据
            hash_size: 哈希尺寸

        Returns:
            包含所有哈希值的字典
        """
        return {
            "md5": ImageHash.compute_md5(image_data),
            "phash": ImageHash.compute_phash(image_data, hash_size),
            "dhash": ImageHash.compute_dhash(image_data, hash_size),
            "ahash": ImageHash.compute_ahash(image_data, hash_size)
        }


class ImageHashCacheKey:
    """
    图像哈希缓存键生成器

    用于生成唯一的缓存键，支持多种策略
    """

    @staticmethod
    def generate_key(
        image_data: bytes,
        prefix: str = "diagnosis",
        include_phash: bool = True,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成缓存键

        策略：
        1. 使用 MD5 作为基础标识
        2. 可选添加 pHash 用于相似图像检测
        3. 可选添加额外参数（如症状描述）

        Args:
            image_data: 图像二进制数据
            prefix: 缓存键前缀
            include_phash: 是否包含感知哈希
            extra_params: 额外参数字典

        Returns:
            缓存键字符串
        """
        md5_hash = ImageHash.compute_md5(image_data)

        parts = [prefix, md5_hash[:16]]

        if include_phash:
            phash = ImageHash.compute_phash(image_data)
            if phash:
                parts.append(phash[:8])

        if extra_params:
            params_str = "_".join(
                f"{k}:{v}" for k, v in sorted(extra_params.items()) if v
            )
            if params_str:
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                parts.append(params_hash)

        return ":".join(parts)

    @staticmethod
    def generate_key_from_pil(
        image: "Image.Image",
        prefix: str = "diagnosis",
        include_phash: bool = True,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        从 PIL Image 对象生成缓存键

        Args:
            image: PIL Image 对象
            prefix: 缓存键前缀
            include_phash: 是否包含感知哈希
            extra_params: 额外参数字典

        Returns:
            缓存键字符串，失败返回 None
        """
        if not IMAGE_LIBS_AVAILABLE:
            return None

        try:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_data = buffer.getvalue()

            return ImageHashCacheKey.generate_key(
                image_data=image_data,
                prefix=prefix,
                include_phash=include_phash,
                extra_params=extra_params
            )
        except Exception as e:
            logger.error(f"从 PIL Image 生成缓存键失败: {e}")
            return None


def compute_image_hash(
    image_data: bytes,
    method: str = "phash"
) -> Optional[str]:
    """
    便捷函数：计算图像哈希

    Args:
        image_data: 图像二进制数据
        method: 哈希方法 ("md5", "phash", "dhash", "ahash")

    Returns:
        哈希字符串
    """
    method_map = {
        "md5": ImageHash.compute_md5,
        "phash": ImageHash.compute_phash,
        "dhash": ImageHash.compute_dhash,
        "ahash": ImageHash.compute_ahash
    }

    if method not in method_map:
        logger.warning(f"未知的哈希方法: {method}，使用默认 phash")
        method = "phash"

    return method_map[method](image_data)


def generate_cache_key(
    image_data: bytes,
    prefix: str = "diagnosis",
    extra_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    便捷函数：生成缓存键

    Args:
        image_data: 图像二进制数据
        prefix: 缓存键前缀
        extra_params: 额外参数

    Returns:
        缓存键字符串
    """
    return ImageHashCacheKey.generate_key(
        image_data=image_data,
        prefix=prefix,
        extra_params=extra_params
    )
