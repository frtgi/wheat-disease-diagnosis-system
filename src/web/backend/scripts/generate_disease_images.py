import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SyncSessionLocal
from app.models.disease import Disease


def generate_placeholder_images():
    db = SyncSessionLocal()
    diseases = db.query(Disease).all()

    img_dir = r'd:\Project\WheatAgent\src\web\frontend\public\images\diseases'
    os.makedirs(img_dir, exist_ok=True)

    colors = [
        '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
        '#00BCD4', '#795548', '#607D8B', '#E91E63', '#3F51B5',
        '#8BC34A', '#FF5722', '#009688', '#FFC107'
    ]

    for i, d in enumerate(diseases):
        code = d.code or f'disease_{d.id}'
        filename = f'{code.lower()}.jpg'
        color = colors[i % len(colors)]
        name = d.name or 'Unknown'
        sci = d.scientific_name or ''

        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            f'<rect width="400" height="300" fill="{color}" opacity="0.15"/>'
            f'<rect x="10" y="10" width="380" height="280" rx="8" fill="white" opacity="0.9"/>'
            f'<text x="200" y="140" text-anchor="middle" font-size="20" font-weight="bold" fill="#333">{name}</text>'
            f'<text x="200" y="170" text-anchor="middle" font-size="14" fill="#666">{sci}</text>'
            f'</svg>'
        )

        filepath = os.path.join(img_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(svg)

        d.image_urls = [f'/images/diseases/{filename}']
        print(f'  Updated {d.name}: {filename}')

    db.commit()
    db.close()
    print(f'\nDone! Updated {len(diseases)} diseases with placeholder images.')


if __name__ == '__main__':
    print('=' * 60)
    print('Generating placeholder disease images and updating database')
    print('=' * 60)
    generate_placeholder_images()
