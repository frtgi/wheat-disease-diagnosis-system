"""
模型文件下载脚本

使用 modelscope 下载损坏的模型文件
"""
from modelscope.hub.file_download import model_file_download
import os

def download_model_file():
    """
    下载 MiniCPM-V-4_5 模型文件
    
    Returns:
        str: 下载文件的路径，失败返回 None
    """
    model_id = 'OpenBMB/MiniCPM-V-4_5'
    filename = 'model-00002-of-00004.safetensors'
    cache_dir = 'D:/Project/WheatAgent/models'
    
    print(f'开始下载: {filename}')
    print(f'模型ID: {model_id}')
    print(f'缓存目录: {cache_dir}')
    print('=' * 60)
    
    try:
        file_path = model_file_download(
            model_id=model_id,
            file_path=filename,
            cache_dir=cache_dir
        )
        print(f'下载完成: {file_path}')
        
        if os.path.exists(file_path):
            size_bytes = os.path.getsize(file_path)
            size_gb = size_bytes / (1024**3)
            print(f'文件大小: {size_gb:.2f} GB ({size_bytes:,} bytes)')
            
            expected_size_gb = 4.92
            if abs(size_gb - expected_size_gb) < 0.1:
                print('✓ 文件大小验证通过')
            else:
                print(f'⚠ 文件大小异常，预期约 {expected_size_gb} GB')
        
        return file_path
    except Exception as e:
        print(f'下载失败: {e}')
        return None

if __name__ == '__main__':
    download_model_file()
