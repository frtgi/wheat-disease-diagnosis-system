"""
病害知识数据库种子脚本

将 disease_knowledge.py 中的 15 种病害知识数据填充到数据库 Disease 表中。
在 backend 目录下运行：python scripts/seed_disease_knowledge.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SyncSessionLocal, sync_engine
from app.core.disease_knowledge import DISEASE_KNOWLEDGE_BASE, DiseaseCategory
from app.models.disease import Disease


SEVERITY_MAP = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.9,
}

VALID_CATEGORIES = {"fungal", "bacterial", "viral", "pest", "nutritional"}


def build_disease_record(info) -> dict:
    """
    将 DiseaseInfo 数据类转换为 Disease 模型所需的字段字典。

    参数:
        info: DiseaseInfo 数据类实例

    返回:
        包含 Disease 模型字段的字典
    """
    code = info.name_en.upper().replace(" ", "_")
    category_value = info.category.value

    severity_float = SEVERITY_MAP.get(info.severity, 0.0)

    return {
        "name": info.name_cn,
        "scientific_name": info.name_en,
        "code": code,
        "category": category_value,
        "symptoms": "\n".join(info.symptoms),
        "description": info.description,
        "causes": "\n".join(info.causes) if info.causes else None,
        "prevention_methods": info.prevention,
        "treatment_methods": info.treatment,
        "severity": severity_float,
        "image_urls": [f"/images/diseases/{code.lower()}.jpg"],
        "is_active": True,
    }


def seed_diseases():
    """
    主函数：将病害知识数据填充到数据库。

    逻辑：
    1. 遍历 DISEASE_KNOWLEDGE_BASE 中所有病害
    2. 跳过 category 不在 Disease 模型合法枚举值中的条目（如 healthy）
    3. 检查数据库中是否已存在相同 code 的记录，避免重复插入
    4. 插入新记录并打印结果统计
    """
    db = SyncSessionLocal()
    try:
        existing_codes = {
            row[0] for row in db.query(Disease.code).all() if row[0] is not None
        }
        print(f"数据库中已有 {len(existing_codes)} 条病害记录")

        inserted = 0
        skipped = 0

        for key, info in DISEASE_KNOWLEDGE_BASE.items():
            category_value = info.category.value
            if category_value not in VALID_CATEGORIES:
                print(f"  跳过 [{info.name_cn}]：category='{category_value}' 不在合法枚举值中")
                skipped += 1
                continue

            code = info.name_en.upper().replace(" ", "_")
            if code in existing_codes:
                print(f"  跳过 [{info.name_cn}]：code='{code}' 已存在")
                skipped += 1
                continue

            record = build_disease_record(info)
            disease = Disease(**record)
            db.add(disease)
            existing_codes.add(code)
            inserted += 1
            print(f"  插入 [{info.name_cn}] (code={code}, category={category_value}, severity={record['severity']})")

        db.commit()
        print(f"\n种子数据填充完成：插入 {inserted} 条，跳过 {skipped} 条")

    except Exception as e:
        db.rollback()
        print(f"种子数据填充失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("病害知识数据库种子脚本")
    print("=" * 60)
    seed_diseases()
