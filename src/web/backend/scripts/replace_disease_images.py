import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('MINIO_ACCESS_KEY', 'minioadmin')
os.environ.setdefault('MINIO_SECRET_KEY', 'minioadmin')

from app.core.database import SyncSessionLocal
from app.models.disease import Disease


DATASET_DIR = r'd:\Project\datasets\wheat_data_unified\images'
FRONTEND_IMG_DIR = r'd:\Project\WheatAgent\src\web\frontend\public\images\diseases'


CODE_TO_DATASET_NAME = {
    'aphid': 'Aphid',
    'black_rust': 'Black Rust',
    'blast': 'Blast',
    'brown_rust': 'Brown Rust',
    'common_root_rot': 'Common Root Rot',
    'fusarium_head_blight': 'Fusarium Head Blight',
    'leaf_blight': 'Leaf Blight',
    'mildew': 'Mildew',
    'mite': 'Mite',
    'septoria': 'Septoria',
    'smut': 'Smut',
    'stem_fly': 'Stem fly',
    'tan_spot': 'Tan spot',
    'yellow_rust': 'Yellow Rust',
}


def find_best_image(disease_code: str) -> str | None:
    dataset_name = CODE_TO_DATASET_NAME.get(disease_code)
    if not dataset_name:
        return None

    for split in ['val', 'train']:
        split_dir = os.path.join(DATASET_DIR, split)
        if not os.path.exists(split_dir):
            continue

        for ext in ['.jpg', '.png']:
            candidate = os.path.join(split_dir, f'{dataset_name}_0{ext}')
            if os.path.exists(candidate):
                return candidate

            candidates = [
                f for f in os.listdir(split_dir)
                if f.startswith(dataset_name + '_') and f.endswith(ext)
            ]
            if candidates:
                candidates.sort()
                return os.path.join(split_dir, candidates[0])

    return None


def replace_disease_images():
    db = SyncSessionLocal()
    diseases = db.query(Disease).all()

    os.makedirs(FRONTEND_IMG_DIR, exist_ok=True)

    updated = 0
    for d in diseases:
        code = (d.code or f'disease_{d.id}').lower()
        source = find_best_image(code)

        if not source:
            print(f'  SKIP {d.name} ({code}): no dataset image found')
            continue

        ext = os.path.splitext(source)[1]
        filename = f'{code.lower()}{ext}'
        dest = os.path.join(FRONTEND_IMG_DIR, filename)

        shutil.copy2(source, dest)

        old_svg = os.path.join(FRONTEND_IMG_DIR, f'{code.lower()}.svg')
        if os.path.exists(old_svg) and old_svg != dest:
            os.remove(old_svg)

        d.image_urls = [f'/images/diseases/{filename}']
        print(f'  OK {d.name}: {source} -> {filename}')
        updated += 1

    db.commit()
    db.close()
    print(f'\nDone! Updated {updated}/{len(diseases)} diseases with real images.')


if __name__ == '__main__':
    print('=' * 60)
    print('Replacing placeholder images with real dataset images')
    print('=' * 60)
    replace_disease_images()
