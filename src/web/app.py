# -*- coding: utf-8 -*-
"""
WheatAgent Gradio Web 界面 - 优化版

优化特性:
- 懒加载引擎初始化，提升启动速度
- 响应式设计，支持移动端
- 现代化UI设计
- 深色/浅色主题切换
- 加载动画和进度指示
- 诊断历史记录
"""
import os
import sys

# 设置控制台编码
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.system('chcp 65001 >nul 2>&1')

import threading
import time
import atexit
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from collections import deque

import gradio as gr
import numpy as np
from PIL import Image

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class LazyEngineManager:
    """
    懒加载引擎管理器（支持预加载和并行诊断）
    
    优化特性:
    - 懒加载：延迟初始化，提升启动速度
    - 预加载：启动时一次性加载所有引擎
    - 并行诊断：视觉和认知并行执行
    - 模型缓存：避免重复加载
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._vision_engine = None
        self._cognition_engine = None
        self._fusion_engine = None
        self._graph_engine = None
        self._init_lock = threading.RLock()  # 使用可重入锁，避免嵌套调用死锁
        self._preload_thread = None  # 预加载线程
    
    @property
    def vision_engine(self):
        """
        懒加载视觉引擎
        """
        if self._vision_engine is None:
            with self._init_lock:
                if self._vision_engine is None:
                    print("📷 懒加载视觉引擎...", flush=True)
                    from src.vision.vision_engine import VisionAgent as VisionEngine
                    self._vision_engine = VisionEngine()
                    print("✅ 视觉引擎加载完成", flush=True)
        return self._vision_engine
    
    @property
    def cognition_engine(self):
        """
        懒加载认知引擎
        """
        if self._cognition_engine is None:
            with self._init_lock:
                if self._cognition_engine is None:
                    print("🧠 懒加载认知引擎...", flush=True)
                    from src.cognition.cognition_engine import CognitionEngine
                    self._cognition_engine = CognitionEngine()
                    print("✅ 认知引擎加载完成", flush=True)
        return self._cognition_engine
    
    @property
    def graph_engine(self):
        """
        懒加载知识图谱引擎
        """
        if self._graph_engine is None:
            with self._init_lock:
                if self._graph_engine is None:
                    print("📚 懒加载知识图谱引擎...", flush=True)
                    print("   [Web] 正在导入graph_engine模块...", flush=True)
                    from src.graph.graph_engine import KnowledgeAgent as GraphEngine
                    print("   [Web] graph_engine模块导入完成", flush=True)
                    print("   [Web] 正在创建KnowledgeAgent实例...", flush=True)
                    self._graph_engine = GraphEngine()
                    print("✅ 知识图谱引擎加载完成", flush=True)
        return self._graph_engine
    
    @property
    def fusion_engine(self):
        """
        懒加载融合引擎
        """
        if self._fusion_engine is None:
            with self._init_lock:
                if self._fusion_engine is None:
                    print("🔗 懒加载融合引擎...", flush=True)
                    print("   [Web] 正在导入fusion_engine模块...", flush=True)
                    from src.fusion.fusion_engine import FusionAgent as FusionEngine
                    print("   [Web] fusion_engine模块导入完成", flush=True)
                    print("   [Web] 正在获取知识图谱引擎...", flush=True)
                    kg = self.graph_engine
                    print("   [Web] 知识图谱引擎获取完成", flush=True)
                    print("   [Web] 正在创建FusionAgent实例...", flush=True)
                    self._fusion_engine = FusionEngine(knowledge_agent=kg)
                    print("✅ 融合引擎加载完成", flush=True)
        return self._fusion_engine
    
    def is_engine_ready(self, engine_name: str) -> bool:
        """
        检查引擎是否已加载
        
        :param engine_name: 引擎名称
        :return: 是否已加载
        """
        if engine_name == 'vision':
            return self._vision_engine is not None
        elif engine_name == 'cognition':
            return self._cognition_engine is not None
        elif engine_name == 'graph':
            return self._graph_engine is not None
        elif engine_name == 'fusion':
            return self._fusion_engine is not None
        return False
    
    def preload_all_engines(self):
        """
        后台预加载所有引擎（启动时一次性加载）
        
        关键优化:
        - 避免首次诊断时的长时间等待
        - 后台线程异步加载，不阻塞界面
        - 加载完成后自动缓存
        """
        def preload_worker():
            """后台加载工作线程"""
            print("\n🚀 开始预加载所有引擎...", flush=True)
            start_time = time.time()
            
            try:
                # 1. 加载视觉引擎
                print("  [1/4] 视觉引擎...", flush=True)
                t0 = time.time()
                _ = self.vision_engine
                print(f"       ✅ 完成 ({time.time()-t0:.2f}s)", flush=True)
                
                # 2. 加载知识图谱引擎
                print("  [2/4] 知识图谱引擎...", flush=True)
                t0 = time.time()
                _ = self.graph_engine
                print(f"       ✅ 完成 ({time.time()-t0:.2f}s)", flush=True)
                
                # 3. 加载融合引擎
                print("  [3/4] 融合引擎...", flush=True)
                t0 = time.time()
                _ = self.fusion_engine
                print(f"       ✅ 完成 ({time.time()-t0:.2f}s)", flush=True)
                
                # 4. 加载认知引擎
                print("  [4/4] 认知引擎...", flush=True)
                t0 = time.time()
                _ = self.cognition_engine
                print(f"       ✅ 完成 ({time.time()-t0:.2f}s)", flush=True)
                
                total_time = time.time() - start_time
                print(f"\n✅ 所有引擎预加载完成，总耗时：{total_time:.2f}s", flush=True)
                print(f"   首次诊断将节省约 {total_time:.1f} 秒等待时间", flush=True)
                
            except Exception as e:
                print(f"❌ 预加载失败：{e}", flush=True)
                import traceback
                traceback.print_exc()
        
        # 启动后台线程
        self._preload_thread = threading.Thread(target=preload_worker, daemon=True)
        self._preload_thread.start()
        print("📡 预加载线程已启动（后台运行）", flush=True)
    
    def diagnose_image_parallel(self, image_path: str, use_knowledge: bool = True, top_k: int = 3):
        """
        并行诊断图像（视觉和认知并行执行）
        
        :param image_path: 图像路径
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前 K 个结果
        :return: 诊断结果
        """
        import concurrent.futures
        
        def vision_task():
            """视觉检测任务"""
            return self.vision_engine.detect_and_visualize(
                image_path, 
                conf_threshold=0.05
            )
        
        def cognition_task():
            """认知分析任务（可选）"""
            if use_knowledge and self.cognition_engine:
                # 如果有认知引擎，执行认知分析
                # 这里可以添加认知分析逻辑
                pass
            return None
        
        # 并行执行
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # 提交视觉任务
            future_vision = executor.submit(vision_task)
            
            # 提交认知任务（如果启用）
            if use_knowledge:
                future_cognition = executor.submit(cognition_task)
            else:
                future_cognition = None
            
            # 获取视觉结果
            vision_result = future_vision.result()
            
            # 获取认知结果（如果有）
            cognition_result = None
            if future_cognition:
                try:
                    cognition_result = future_cognition.result(timeout=2.0)
                except concurrent.futures.TimeoutError:
                    pass  # 认知超时，不影响视觉结果
        
        elapsed = time.time() - start_time
        print(f"⚡ 并行诊断完成，耗时：{elapsed:.3f}s", flush=True)
        
        return vision_result


class TempFileManager:
    """
    临时文件管理器
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.temp_dir = Path("temp_uploads")
        self.temp_dir.mkdir(exist_ok=True)
        self.max_age_hours = 24
        self.max_files = 100
        
        self._start_cleanup_thread()
        atexit.register(self.cleanup_all)
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_loop():
            while True:
                time.sleep(3600)
                self.cleanup_old_files()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def cleanup_old_files(self):
        """清理过期文件"""
        now = time.time()
        max_age_seconds = self.max_age_hours * 3600
        
        files = list(self.temp_dir.glob("*"))
        deleted_count = 0
        
        for f in files:
            if f.is_file():
                age = now - f.stat().st_mtime
                if age > max_age_seconds:
                    try:
                        f.unlink()
                        deleted_count += 1
                    except Exception:
                        pass
        
        files = sorted(self.temp_dir.glob("*"), key=lambda x: x.stat().st_mtime)
        while len(files) > self.max_files:
            try:
                files[0].unlink()
                files.pop(0)
            except Exception:
                break
    
    def cleanup_all(self):
        """清理所有临时文件"""
        try:
            for f in self.temp_dir.glob("*"):
                if f.is_file():
                    f.unlink()
        except Exception:
            pass


class DiagnosisHistory:
    """
    诊断历史记录管理器
    """
    
    def __init__(self, max_records: int = 50):
        """
        初始化历史记录管理器
        
        :param max_records: 最大记录数
        """
        self.max_records = max_records
        self.history_file = Path("logs/diagnosis_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._history = self._load_history()
    
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history[-self.max_records:], f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def add_record(self, record: Dict):
        """
        添加诊断记录
        
        :param record: 诊断记录
        """
        record['timestamp'] = datetime.now().isoformat()
        self._history.append(record)
        if len(self._history) > self.max_records:
            self._history = self._history[-self.max_records:]
        self._save_history()
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """
        获取历史记录
        
        :param limit: 返回记录数
        :return: 历史记录列表
        """
        return self._history[-limit:][::-1]
    
    def clear_history(self):
        """清空历史记录"""
        self._history = []
        self._save_history()


class ConcurrencyManager:
    """
    并发控制管理器
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化并发管理器
        
        :param max_concurrent: 最大并发数
        """
        self.max_concurrent = max_concurrent
        self._semaphore = threading.Semaphore(max_concurrent)
        self._active_count = 0
        self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """
        获取处理槽位
        
        :return: 是否成功获取
        """
        acquired = self._semaphore.acquire(blocking=False)
        if acquired:
            with self._lock:
                self._active_count += 1
        return acquired
    
    def release(self):
        """释放处理槽位"""
        self._semaphore.release()
        with self._lock:
            self._active_count = max(0, self._active_count - 1)
    
    @property
    def active_count(self) -> int:
        """当前活跃请求数"""
        return self._active_count
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'active_count': self._active_count,
            'max_concurrent': self.max_concurrent,
            'available_slots': self.max_concurrent - self._active_count
        }


class WheatAgentWebApp:
    """
    WheatAgent Web应用 - 优化版
    """
    
    def __init__(self):
        """初始化应用"""
        self.engine_manager = LazyEngineManager()
        self.temp_manager = TempFileManager()
        self.concurrency_manager = ConcurrencyManager(max_concurrent=5)
        self.history = DiagnosisHistory()
        self._system_status = {
            'vision_ready': False,
            'cognition_ready': False,
            'graph_ready': False,
            'fusion_ready': False
        }
        self._start_status_monitor()
    
    def _start_status_monitor(self):
        """启动状态监控线程"""
        def monitor_loop():
            while True:
                time.sleep(2)
                self._system_status['vision_ready'] = self.engine_manager.is_engine_ready('vision')
                self._system_status['cognition_ready'] = self.engine_manager.is_engine_ready('cognition')
                self._system_status['graph_ready'] = self.engine_manager.is_engine_ready('graph')
                self._system_status['fusion_ready'] = self.engine_manager.is_engine_ready('fusion')
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
    
    def get_system_status(self) -> str:
        """
        获取系统状态
        
        :return: 状态信息文本
        """
        output = []
        output.append("🔧 系统引擎状态")
        output.append("-" * 30)
        
        status_map = {
            'vision': ('📷 视觉引擎', 'vision_ready'),
            'cognition': ('🧠 认知引擎', 'cognition_ready'),
            'graph': ('📚 知识图谱', 'graph_ready'),
            'fusion': ('🔗 融合引擎', 'fusion_ready')
        }
        
        for key, (name, status_key) in status_map.items():
            ready = self._system_status.get(status_key, False)
            icon = "✅" if ready else "⏳"
            status_text = "已就绪" if ready else "加载中..."
            output.append(f"{icon} {name}: {status_text}")
        
        stats = self.concurrency_manager.get_stats()
        output.append("-" * 30)
        output.append(f"📊 并发状态: {stats['active_count']}/{stats['max_concurrent']}")
        
        return "\n".join(output)
    
    def diagnose_image(
        self,
        image: Optional[np.ndarray],
        use_knowledge: bool = True,
        top_k: int = 3,
        progress: gr.Progress = None
    ) -> Tuple[str, Optional[Image.Image], str]:
        """
        图像诊断
        
        :param image: 输入图像
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前K个结果
        :param progress: 进度条
        :return: (诊断结果文本, 可视化图像, 历史记录)
        """
        if image is None:
            return "请先上传图像", None, self._format_history()
        
        if not self.concurrency_manager.acquire():
            stats = self.concurrency_manager.get_stats()
            return f"系统繁忙，请稍后再试。当前处理中: {stats['active_count']}/{stats['max_concurrent']}", None, self._format_history()
        
        try:
            if progress:
                progress(0.1, desc="正在初始化引擎...")
            
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = temp_dir / f"{timestamp}.jpg"
            
            pil_image = Image.fromarray(image.astype('uint8'))
            pil_image.save(image_path)
            
            if progress:
                progress(0.3, desc="正在执行视觉检测...")
            
            # 使用融合引擎进行诊断（会自动触发懒加载）
            try:
                results = self.engine_manager.fusion_engine.diagnose(
                    image_path=str(image_path),
                    use_knowledge=use_knowledge,
                    top_k=top_k,
                    vision_engine=self.engine_manager.vision_engine,
                    cognition_engine=self.engine_manager.cognition_engine
                )
                
                if progress:
                    progress(0.7, desc="正在生成可视化结果...")
                
                _, vis_path = self.engine_manager.vision_engine.detect_and_visualize(
                    str(image_path), 
                    conf_threshold=0.05
                )
            except Exception as e:
                print(f"❌ 诊断过程出错: {e}", flush=True)
                import traceback
                traceback.print_exc()
                return f"诊断失败: {str(e)}", None, self._format_history()
            
            if progress:
                progress(0.9, desc="正在生成报告...")
            
            result_text = self._format_diagnosis_results(results)
            
            if vis_path and os.path.exists(vis_path):
                vis_image = Image.open(vis_path)
            else:
                vis_image = pil_image
            
            record = {
                'type': 'image',
                'result': result_text[:500],
                'image_path': str(image_path)
            }
            self.history.add_record(record)
            
            if progress:
                progress(1.0, desc="诊断完成!")
            
            return result_text, vis_image, self._format_history()
            
        except Exception as e:
            print(f"❌ 诊断失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            return f"诊断失败: {str(e)}", None, self._format_history()
        
        finally:
            self.concurrency_manager.release()
    
    def diagnose_text(
        self,
        text: str,
        use_knowledge: bool = True,
        top_k: int = 3,
        progress: gr.Progress = None
    ) -> Tuple[str, str]:
        """
        文本症状诊断
        
        :param text: 症状描述
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前K个结果
        :param progress: 进度条
        :return: (诊断结果文本, 历史记录)
        """
        if not text.strip():
            return "请输入症状描述", self._format_history()
        
        try:
            if progress:
                progress(0.3, desc="正在分析症状...")
            
            if not self.engine_manager.cognition_engine:
                return "认知引擎未加载", self._format_history()
            
            results = self.engine_manager.cognition_engine.analyze_text(
                text=text,
                use_knowledge=use_knowledge,
                top_k=top_k
            )
            
            if progress:
                progress(0.8, desc="正在生成报告...")
            
            result_text = self._format_text_results(results)
            
            record = {
                'type': 'text',
                'input': text[:200],
                'result': result_text[:500]
            }
            self.history.add_record(record)
            
            if progress:
                progress(1.0, desc="诊断完成!")
            
            return result_text, self._format_history()
            
        except Exception as e:
            return f"诊断失败: {str(e)}", self._format_history()
    
    def get_disease_list(self) -> str:
        """获取病害列表"""
        try:
            if not self.engine_manager.graph_engine:
                return "知识图谱引擎未加载"
            
            diseases = self.engine_manager.graph_engine.get_all_diseases()
            
            output = []
            output.append("=" * 50)
            output.append("📚 知识图谱病害列表")
            output.append("=" * 50)
            output.append(f"\n共 {len(diseases)} 种病害:\n")
            
            for i, disease in enumerate(diseases, 1):
                output.append(f"{i}. {disease}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"获取病害列表失败: {str(e)}"
    
    def get_disease_detail(self, disease_name: str) -> str:
        """获取病害详细信息"""
        if not disease_name.strip():
            return "请输入病害名称"
        
        try:
            if not self.engine_manager.graph_engine:
                return "知识图谱引擎未加载"
            
            info = self.engine_manager.graph_engine.get_disease_info(disease_name)
            
            if not info:
                return f"未找到病害: {disease_name}"
            
            output = []
            output.append("=" * 50)
            output.append(f"🔍 {disease_name} 详细信息")
            output.append("=" * 50)
            output.append("")
            
            for key, value in info.items():
                output.append(f"{key}: {value}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"获取病害信息失败: {str(e)}"
    
    def diagnose_batch(
        self,
        images: List[np.ndarray],
        use_knowledge: bool = True,
        top_k: int = 3,
        progress: gr.Progress = None
    ) -> Tuple[str, str]:
        """
        批量图像诊断
        
        :param images: 图像列表
        :param use_knowledge: 是否使用知识图谱
        :param top_k: 返回前K个结果
        :param progress: 进度条
        :return: (批量诊断报告, 历史记录)
        """
        if not images or len(images) == 0:
            return "请先上传图像", self._format_history()
        
        results = []
        total = len(images)
        
        for i, image in enumerate(images):
            if progress:
                progress((i + 1) / total, desc=f"正在诊断第 {i+1}/{total} 张图像...")
            
            result_text, _, _ = self.diagnose_image(image, use_knowledge, top_k, None)
            results.append({
                'index': i + 1,
                'result': result_text
            })
        
        batch_report = self._format_batch_results(results)
        
        record = {
            'type': 'batch',
            'count': total,
            'result': batch_report[:500]
        }
        self.history.add_record(record)
        
        return batch_report, self._format_history()
    
    def export_report(self, result_text: str, format_type: str = "txt") -> str:
        """
        导出诊断报告
        
        :param result_text: 诊断结果文本
        :param format_type: 导出格式 (txt/json)
        :return: 导出文件路径或错误信息
        """
        if not result_text.strip():
            return "没有可导出的报告内容"
        
        try:
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "json":
                export_path = export_dir / f"diagnosis_report_{timestamp}.json"
                report_data = {
                    'timestamp': datetime.now().isoformat(),
                    'content': result_text,
                    'export_format': format_type
                }
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
            else:
                export_path = export_dir / f"diagnosis_report_{timestamp}.txt"
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(result_text)
            
            return f"✅ 报告已导出至: {export_path}"
            
        except Exception as e:
            return f"导出失败: {str(e)}"
    
    def get_knowledge_stats(self) -> str:
        """
        获取知识图谱统计信息
        
        :return: 统计信息文本
        """
        try:
            if not self.engine_manager.graph_engine:
                return "知识图谱引擎未加载"
            
            stats = self.engine_manager.graph_engine.get_statistics()
            
            output = []
            output.append("=" * 50)
            output.append("📊 知识图谱统计信息")
            output.append("=" * 50)
            output.append("")
            
            if isinstance(stats, dict):
                for key, value in stats.items():
                    output.append(f"  {key}: {value}")
            else:
                output.append(str(stats))
            
            output.append("")
            output.append("=" * 50)
            
            return "\n".join(output)
            
        except Exception as e:
            return f"获取统计信息失败: {str(e)}"
    
    def _format_batch_results(self, results: List[Dict]) -> str:
        """格式化批量诊断结果"""
        output = []
        output.append("=" * 60)
        output.append("📋 批量诊断报告")
        output.append("=" * 60)
        output.append(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append(f"图像数量: {len(results)}")
        output.append("=" * 60)
        output.append("")
        
        for result in results:
            output.append(f"\n【图像 {result['index']}】")
            output.append("-" * 40)
            output.append(result['result'][:800])
            if len(result['result']) > 800:
                output.append("... (内容已截断)")
        
        output.append("\n" + "=" * 60)
        output.append("批量诊断完成")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def clear_history(self) -> str:
        """清空历史记录"""
        self.history.clear_history()
        return self._format_history()
    
    def _format_diagnosis_results(self, results: List[Dict]) -> str:
        """格式化诊断结果"""
        if not results:
            return "未检测到病害"
        
        output = []
        output.append("=" * 60)
        output.append("🌾 小麦病害智能诊断报告")
        output.append("=" * 60)
        output.append("")
        
        output.append("【检测结果】")
        output.append("-" * 60)
        
        for i, result in enumerate(results[:5], 1):
            disease = result.get('name', '未知')
            confidence = result.get('confidence', 0)
            bbox = result.get('bbox', None)
            
            output.append(f"{i}. {disease}")
            output.append(f"   置信度: {confidence:.2%}")
            
            if bbox:
                output.append(f"   位置: [{', '.join([f'{x:.1f}' for x in bbox])}]")
            
            if 'description' in result:
                output.append(f"   描述: {result['description'][:150]}...")
            if 'treatment' in result:
                output.append(f"   防治: {result['treatment'][:150]}...")
            if 'symptoms' in result:
                output.append(f"   症状: {result['symptoms'][:100]}...")
            
            output.append("")
        
        if results and 'llava_report' in results[0]:
            output.append("-" * 60)
            output.append("【智能诊断分析】")
            output.append("-" * 60)
            output.append(results[0]['llava_report'])
            output.append("")
        
        if results and 'reasoning' in results[0]:
            output.append("-" * 60)
            output.append("【诊断推理过程】")
            output.append("-" * 60)
            output.append(results[0]['reasoning'])
            output.append("")
        
        output.append("=" * 60)
        output.append(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)
        
        return "\n".join(output)
    
    def _format_text_results(self, results: List[Dict]) -> str:
        """格式化文本诊断结果"""
        if not results:
            return "无法根据描述确定病害"
        
        output = []
        output.append("=" * 50)
        output.append("📝 基于症状的诊断结果")
        output.append("=" * 50)
        output.append("")
        
        for i, result in enumerate(results[:5], 1):
            disease = result.get('name', '未知')
            confidence = result.get('confidence', 0)
            reason = result.get('reason', '')
            
            output.append(f"{i}. {disease}")
            output.append(f"   匹配度: {confidence:.2%}")
            if reason:
                output.append(f"   依据: {reason}")
            output.append("")
        
        output.append("=" * 50)
        return "\n".join(output)
    
    def _format_history(self) -> str:
        """格式化历史记录"""
        records = self.history.get_history(10)
        if not records:
            return "暂无诊断历史"
        
        output = []
        for i, record in enumerate(records, 1):
            timestamp = record.get('timestamp', '未知时间')
            rtype = record.get('type', 'unknown')
            result = record.get('result', '')[:100]
            
            icon = "📷" if rtype == 'image' else "📝"
            output.append(f"{i}. {icon} {timestamp[:19]}")
            output.append(f"   {result}...")
            output.append("")
        
        return "\n".join(output)


OPTIMIZED_CSS = """
/* 全局样式 - 玻璃拟态设计 */
* {
    box-sizing: border-box;
}

:root {
    --primary-gradient: linear-gradient(135deg, #1a5f2a 0%, #2d8f4e 50%, #45b369 100%);
    --glass-bg: rgba(255, 255, 255, 0.85);
    --glass-border: rgba(255, 255, 255, 0.3);
    --shadow-soft: 0 8px 32px rgba(0, 0, 0, 0.1);
    --shadow-glow: 0 0 40px rgba(45, 143, 78, 0.15);
}

body {
    background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    min-height: 100vh;
}

.gradio-container {
    max-width: 1500px !important;
    margin: 0 auto !important;
    background: transparent !important;
}

/* 头部样式 - 玻璃拟态 */
.header-container {
    background: var(--glass-bg);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 24px;
    padding: 40px 30px;
    margin-bottom: 30px;
    box-shadow: var(--shadow-soft), var(--shadow-glow);
    text-align: center;
    position: relative;
    overflow: hidden;
}

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--primary-gradient);
}

.header-container h1 {
    font-size: 3em;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 12px;
    font-weight: 700;
}

.header-container h3 {
    font-size: 1.4em;
    color: #1a5f2a;
    margin-bottom: 10px;
    font-weight: 500;
}

.header-container p {
    font-size: 1.1em;
    color: #555;
}

/* 卡片样式 - 玻璃拟态 */
.card {
    background: var(--glass-bg);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: var(--shadow-soft);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-soft), 0 12px 40px rgba(45, 143, 78, 0.2);
}

.card-title {
    font-size: 1.3em;
    font-weight: 600;
    background: var(--primary-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 2px solid rgba(45, 143, 78, 0.2);
}

/* 按钮样式 - 渐变发光效果 */
.primary-btn {
    background: var(--primary-gradient) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 28px !important;
    font-size: 1.1em !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(45, 143, 78, 0.4) !important;
    position: relative;
    overflow: hidden;
}

.primary-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    transition: left 0.5s;
}

.primary-btn:hover::before {
    left: 100%;
}

.primary-btn:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 25px rgba(45, 143, 78, 0.5) !important;
}

.secondary-btn {
    background: rgba(255, 255, 255, 0.9) !important;
    color: #1a5f2a !important;
    border: 2px solid rgba(45, 143, 78, 0.3) !important;
    border-radius: 12px !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

.secondary-btn:hover {
    background: rgba(45, 143, 78, 0.1) !important;
    border-color: #2d8f4e !important;
    transform: translateY(-2px);
}

/* 结果框样式 - 玻璃拟态 */
.result-box {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 18px;
    border-left: 4px solid;
    border-image: var(--primary-gradient) 1;
    font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
    font-size: 0.95em;
    line-height: 1.7;
    color: #1a1a1a !important;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.05);
}

.result-box * {
    color: #1a1a1a !important;
}

.result-box pre, .result-box code {
    background: rgba(0, 0, 0, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
    color: #2d8f4e !important;
}

/* 标签页样式 */
.tabs-nav {
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 16px 16px 0 0;
    padding: 10px;
    gap: 8px;
}

.tab-item {
    border-radius: 12px !important;
    padding: 14px 28px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.tab-item.selected {
    background: var(--primary-gradient) !important;
    color: white !important;
    box-shadow: 0 4px 15px rgba(45, 143, 78, 0.3);
}

.tab-item:hover:not(.selected) {
    background: rgba(45, 143, 78, 0.1) !important;
}

/* 进度条样式 - 渐变动画 */
.progress-bar {
    height: 10px;
    border-radius: 5px;
    background: rgba(45, 143, 78, 0.1);
    overflow: hidden;
}

.progress-bar-fill {
    height: 100%;
    background: var(--primary-gradient);
    border-radius: 5px;
    transition: width 0.3s ease;
    position: relative;
}

.progress-bar-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    animation: shimmer 1.5s infinite;
}

/* 历史记录样式 */
.history-item {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(10px);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 10px;
    border-left: 4px solid;
    border-image: var(--primary-gradient) 1;
    transition: all 0.3s ease;
}

.history-item:hover {
    transform: translateX(5px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* 输入框样式 */
input[type="text"], textarea {
    background: rgba(255, 255, 255, 0.95) !important;
    border: 2px solid rgba(45, 143, 78, 0.2) !important;
    border-radius: 12px !important;
    padding: 14px !important;
    transition: all 0.3s ease !important;
}

input[type="text"]:focus, textarea:focus {
    border-color: #2d8f4e !important;
    box-shadow: 0 0 0 4px rgba(45, 143, 78, 0.1) !important;
}

/* 图像上传区域 */
.image-upload-area {
    border: 3px dashed rgba(45, 143, 78, 0.3);
    border-radius: 16px;
    padding: 30px;
    background: rgba(255, 255, 255, 0.5);
    transition: all 0.3s ease;
    cursor: pointer;
}

.image-upload-area:hover {
    border-color: #2d8f4e;
    background: rgba(45, 143, 78, 0.05);
}

/* 响应式设计 */
@media (max-width: 768px) {
    .header-container h1 {
        font-size: 2em;
    }
    
    .header-container h3 {
        font-size: 1.2em;
    }
    
    .card {
        padding: 18px;
        border-radius: 16px;
    }
    
    .primary-btn {
        width: 100%;
        padding: 16px !important;
    }
    
    .tab-item {
        padding: 10px 16px !important;
        font-size: 0.9em !important;
    }
}

/* 动画效果 */
@keyframes fadeIn {
    from { 
        opacity: 0; 
        transform: translateY(20px); 
    }
    to { 
        opacity: 1; 
        transform: translateY(0); 
    }
}

@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

@keyframes pulse {
    0%, 100% { 
        opacity: 1; 
        transform: scale(1);
    }
    50% { 
        opacity: 0.7; 
        transform: scale(0.98);
    }
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.fade-in {
    animation: fadeIn 0.5s ease-out;
}

.loading {
    animation: pulse 1.5s infinite;
}

.shimmer {
    animation: shimmer 2s infinite;
}

/* 页脚样式 */
.footer-container {
    text-align: center;
    padding: 30px;
    margin-top: 40px;
    background: var(--glass-bg);
    backdrop-filter: blur(15px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    color: #333;
}

.footer-container p {
    margin: 6px 0;
}

/* 状态指示器 - 发光效果 */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 8px 16px;
    border-radius: 25px;
    font-size: 0.95em;
    font-weight: 500;
}

.status-ready {
    background: rgba(45, 143, 78, 0.15);
    color: #1a5f2a;
    box-shadow: 0 0 20px rgba(45, 143, 78, 0.2);
}

.status-loading {
    background: rgba(255, 152, 0, 0.15);
    color: #e65100;
    animation: pulse 1.5s infinite;
}

.status-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: currentColor;
    box-shadow: 0 0 10px currentColor;
}

/* 特性标签 */
.feature-tag {
    display: inline-block;
    padding: 6px 14px;
    background: var(--primary-gradient);
    color: white;
    border-radius: 20px;
    font-size: 0.85em;
    font-weight: 500;
    margin: 4px;
}

/* 检测结果高亮 */
.detection-highlight {
    background: linear-gradient(135deg, rgba(45, 143, 78, 0.1), rgba(69, 179, 105, 0.1));
    border-radius: 10px;
    padding: 12px;
    margin: 8px 0;
    border-left: 4px solid #2d8f4e;
}

/* 滚动条样式 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #1a5f2a, #45b369);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #2d8f4e, #5cc47a);
}

/* Gradio 组件覆盖样式 */
.gr-button-primary {
    background: var(--primary-gradient) !important;
}

.gr-panel {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(15px) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
}

/* 文本框文字颜色修复 */
.gr-text-input, .gr-text-output, textarea {
    color: #1a1a1a !important;
    background: rgba(255, 255, 255, 0.98) !important;
}

.gr-text-input::placeholder, textarea::placeholder {
    color: #666 !important;
}

/* Markdown 内容样式 */
.markdown-text, .prose {
    color: #1a1a1a !important;
}

.markdown-text h1, .markdown-text h2, .markdown-text h3,
.prose h1, .prose h2, .prose h3 {
    color: #1a5f2a !important;
}

.markdown-text p, .prose p {
    color: #333 !important;
}

.markdown-text ul, .markdown-text ol,
.prose ul, .prose ol {
    color: #333 !important;
}

.markdown-text li, .prose li {
    color: #333 !important;
}

/* 图标动画 */
.icon-spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
"""


def create_app() -> gr.Blocks:
    """
    创建Gradio应用
    """
    app = WheatAgentWebApp()
    
    with gr.Blocks(
        title="WheatAgent - 小麦病害诊断智能体"
    ) as demo:
        gr.HTML("""
        <div class="header-container fade-in">
            <h1>🌾 WheatAgent</h1>
            <h3>基于多模态特征融合的小麦病害诊断智能体</h3>
            <p>融合视觉感知、语义理解和知识推理的智能诊断系统</p>
        </div>
        """)
        
        with gr.Tabs() as tabs:
            with gr.TabItem("📷 图像诊断", id="image_tab"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📤 上传小麦病害图像</div>')
                        
                        image_input = gr.Image(
                            label="上传图像",
                            type="numpy",
                            height=350,
                            show_label=False
                        )
                        
                        with gr.Row():
                            use_knowledge_cb = gr.Checkbox(
                                label="使用知识图谱增强",
                                value=True,
                                container=False
                            )
                            top_k_slider = gr.Slider(
                                label="返回结果数量",
                                minimum=1,
                                maximum=10,
                                value=3,
                                step=1,
                                container=False
                            )
                        
                        diagnose_btn = gr.Button(
                            "🔍 开始诊断",
                            variant="primary",
                            size="lg",
                            elem_classes=["primary-btn"]
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📋 诊断报告</div>')
                        
                        result_text = gr.Textbox(
                            label="诊断报告",
                            lines=18,
                            max_lines=25,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">🖼️ 检测结果可视化</div>')
                        
                        result_image = gr.Image(
                            label="检测结果",
                            type="pil",
                            height=350,
                            show_label=False
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📜 诊断历史</div>')
                        
                        history_text = gr.Textbox(
                            label="历史记录",
                            lines=12,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        clear_history_btn = gr.Button(
                            "🗑️ 清空历史",
                            variant="secondary",
                            elem_classes=["secondary-btn"]
                        )
                        
                        gr.HTML('</div>')
                
                diagnose_btn.click(
                    fn=app.diagnose_image,
                    inputs=[image_input, use_knowledge_cb, top_k_slider],
                    outputs=[result_text, result_image, history_text]
                )
                
                clear_history_btn.click(
                    fn=app.clear_history,
                    outputs=[history_text]
                )
            
            with gr.TabItem("📝 文本诊断", id="text_tab"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">✏️ 输入症状描述</div>')
                        
                        text_input = gr.Textbox(
                            label="症状描述",
                            placeholder="请描述小麦的症状，如：叶片出现黄色条纹、有白色霉层、穗部漂白等...",
                            lines=8,
                            show_label=False
                        )
                        
                        with gr.Row():
                            use_knowledge_text = gr.Checkbox(
                                label="使用知识图谱",
                                value=True,
                                container=False
                            )
                            top_k_text = gr.Slider(
                                label="返回结果数量",
                                minimum=1,
                                maximum=10,
                                value=3,
                                step=1,
                                container=False
                            )
                        
                        text_diagnose_btn = gr.Button(
                            "🔍 开始诊断",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📋 诊断结果</div>')
                        
                        text_result = gr.Textbox(
                            label="诊断报告",
                            lines=18,
                            max_lines=25,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📜 诊断历史</div>')
                        
                        text_history = gr.Textbox(
                            label="历史记录",
                            lines=12,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                
                text_diagnose_btn.click(
                    fn=app.diagnose_text,
                    inputs=[text_input, use_knowledge_text, top_k_text],
                    outputs=[text_result, text_history]
                )
            
            with gr.TabItem("📚 知识库", id="knowledge_tab"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📋 病害列表</div>')
                        
                        list_btn = gr.Button(
                            "📋 获取病害列表",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        disease_list = gr.Textbox(
                            label="病害列表",
                            lines=20,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">🔍 病害详情查询</div>')
                        
                        disease_name_input = gr.Textbox(
                            label="病害名称",
                            placeholder="输入病害名称，如：条锈病、白粉病、赤霉病",
                            show_label=False
                        )
                        
                        query_btn = gr.Button(
                            "🔍 查询详情",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        disease_detail = gr.Textbox(
                            label="详细信息",
                            lines=18,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📊 知识图谱统计</div>')
                        
                        stats_btn = gr.Button(
                            "📊 获取统计信息",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        stats_output = gr.Textbox(
                            label="统计信息",
                            lines=10,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                
                list_btn.click(
                    fn=app.get_disease_list,
                    outputs=[disease_list]
                )
                
                query_btn.click(
                    fn=app.get_disease_detail,
                    inputs=[disease_name_input],
                    outputs=[disease_detail]
                )
                
                stats_btn.click(
                    fn=app.get_knowledge_stats,
                    outputs=[stats_output]
                )
            
            with gr.TabItem("📦 批量诊断", id="batch_tab"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📤 批量上传图像</div>')
                        
                        batch_images = gr.Gallery(
                            label="上传多张图像",
                            type="numpy",
                            height=300,
                            show_label=False,
                            columns=3
                        )
                        
                        with gr.Row():
                            batch_use_knowledge = gr.Checkbox(
                                label="使用知识图谱增强",
                                value=True,
                                container=False
                            )
                            batch_top_k = gr.Slider(
                                label="返回结果数量",
                                minimum=1,
                                maximum=5,
                                value=3,
                                step=1,
                                container=False
                            )
                        
                        batch_diagnose_btn = gr.Button(
                            "🔍 批量诊断",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=2):
                        gr.HTML('<div class="card"><div class="card-title">📋 批量诊断报告</div>')
                        
                        batch_result = gr.Textbox(
                            label="诊断报告",
                            lines=25,
                            max_lines=35,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        with gr.Row():
                            export_txt_btn = gr.Button(
                                "📄 导出TXT",
                                variant="secondary",
                                elem_classes=["secondary-btn"]
                            )
                            export_json_btn = gr.Button(
                                "📋 导出JSON",
                                variant="secondary",
                                elem_classes=["secondary-btn"]
                            )
                        
                        export_status = gr.Textbox(
                            label="导出状态",
                            lines=2,
                            interactive=False,
                            show_label=False
                        )
                        
                        gr.HTML('</div>')
                
                batch_diagnose_btn.click(
                    fn=app.diagnose_batch,
                    inputs=[batch_images, batch_use_knowledge, batch_top_k],
                    outputs=[batch_result, export_status]
                )
                
                export_txt_btn.click(
                    fn=lambda x: app.export_report(x, "txt"),
                    inputs=[batch_result],
                    outputs=[export_status]
                )
                
                export_json_btn.click(
                    fn=lambda x: app.export_report(x, "json"),
                    inputs=[batch_result],
                    outputs=[export_status]
                )
            
            with gr.TabItem("⚙️ 系统状态", id="status_tab"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">🔧 引擎状态</div>')
                        
                        status_refresh_btn = gr.Button(
                            "🔄 刷新状态",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        system_status = gr.Textbox(
                            label="系统状态",
                            lines=10,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                    
                    with gr.Column(scale=1):
                        gr.HTML('<div class="card"><div class="card-title">📊 运行统计</div>')
                        
                        stats_refresh_btn = gr.Button(
                            "🔄 刷新统计",
                            variant="primary",
                            elem_classes=["primary-btn"]
                        )
                        
                        runtime_stats = gr.Textbox(
                            label="运行统计",
                            lines=10,
                            interactive=False,
                            show_label=False,
                            elem_classes=["result-box"]
                        )
                        
                        gr.HTML('</div>')
                
                status_refresh_btn.click(
                    fn=app.get_system_status,
                    outputs=[system_status]
                )
                
                stats_refresh_btn.click(
                    fn=app.get_knowledge_stats,
                    outputs=[runtime_stats]
                )
            
            with gr.TabItem("❓ 使用说明", id="help_tab"):
                gr.HTML("""
                <div class="card fade-in">
                    <div class="card-title">📖 WheatAgent 使用指南</div>
                    
                    <h3>📷 图像诊断</h3>
                    <ol>
                        <li>在"图像诊断"标签页上传小麦病害图像</li>
                        <li>可选择是否使用知识图谱增强诊断</li>
                        <li>点击"开始诊断"按钮</li>
                        <li>查看诊断结果和可视化检测框</li>
                    </ol>
                    
                    <h3>📦 批量诊断</h3>
                    <ol>
                        <li>在"批量诊断"标签页上传多张小麦病害图像</li>
                        <li>系统将自动对每张图像进行诊断</li>
                        <li>生成汇总报告，支持导出为TXT或JSON格式</li>
                    </ol>
                    
                    <h3>📝 文本诊断</h3>
                    <ol>
                        <li>在"文本诊断"标签页输入症状描述</li>
                        <li>尽可能详细地描述症状特征</li>
                        <li>点击"开始诊断"按钮</li>
                        <li>查看基于症状的诊断建议</li>
                    </ol>
                    
                    <h3>📚 知识库查询</h3>
                    <ul>
                        <li>查看系统中已知的所有小麦病害</li>
                        <li>查询特定病害的详细信息、防治方法等</li>
                        <li>查看知识图谱统计信息</li>
                    </ul>
                    
                    <h3>⚙️ 系统状态</h3>
                    <ul>
                        <li>实时查看各引擎加载状态</li>
                        <li>监控系统并发处理情况</li>
                        <li>查看知识图谱运行统计</li>
                    </ul>
                    
                    <h3>🎯 支持的病害类型</h3>
                    <p>系统支持17类常见小麦病害和虫害的识别与诊断，包括：</p>
                    <ul>
                        <li>条锈病、叶锈病、茎锈病</li>
                        <li>白粉病、赤霉病</li>
                        <li>蚜虫、茎蝇、螨虫</li>
                        <li>黑粉病、小麦爆发病等</li>
                    </ul>
                    
                    <h3>⚠️ 注意事项</h3>
                    <ul>
                        <li>图像质量会影响诊断准确性</li>
                        <li>建议在自然光下拍摄清晰的叶片图像</li>
                        <li>文本描述越详细，诊断结果越准确</li>
                        <li>批量诊断时建议每次不超过10张图像</li>
                    </ul>
                    
                    <h3>🔧 技术架构</h3>
                    <p>基于多模态特征融合架构，集成：</p>
                    <ul>
                        <li><strong>Qwen3-VL-4B-Instruct</strong>: 原生多模态大模型（4B参数，3GB显存优化）</li>
                        <li><strong>SerpensGate-YOLOv8</strong>: 动态蛇形卷积 + SPPELAN + STA</li>
                        <li><strong>Neo4j知识图谱</strong>: 农业知识存储与推理</li>
                        <li><strong>KAD-Former</strong>: 知识感知扩散Transformer融合</li>
                    </ul>
                    
                    <h3>🆕 v4.7 新特性</h3>
                    <ul>
                        <li>新增批量图像诊断功能</li>
                        <li>新增诊断报告导出功能（TXT/JSON）</li>
                        <li>新增系统状态实时监控</li>
                        <li>新增知识图谱统计信息展示</li>
                        <li>优化引擎懒加载机制</li>
                        <li>升级至Qwen3-VL-4B-Instruct原生多模态模型</li>
                    </ul>
                </div>
                """)
        
        gr.HTML("""
        <div class="footer-container">
            <p>🌾 WheatAgent v4.7 - 基于多模态特征融合的小麦病害诊断智能体</p>
            <p>Powered by Qwen3-VL-4B-Instruct + SerpensGate-YOLOv8 + Neo4j Knowledge Graph</p>
            <p>© 2026 IWDDA Project | 原生多模态架构 | 3GB显存优化</p>
        </div>
        """)
    
    return demo


def main():
    """启动 Web 应用（带预加载优化）"""
    print("=" * 60)
    print("🌾 WheatAgent Web 应用启动中...")
    print("=" * 60)
    
    demo = create_app()
    
    # 🚀 关键优化：启动后台线程预加载所有引擎
    print("\n🚀 启动引擎预加载（后台运行）...")
    engine_manager = LazyEngineManager()
    engine_manager.preload_all_engines()
    
    print("\n⏳ Web 服务启动中（引擎在后台加载）...")
    print("=" * 60)
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True,
        favicon_path=None,
        css=OPTIMIZED_CSS,
        theme=gr.themes.Soft(
            primary_hue="green",
            secondary_hue="emerald",
            neutral_hue="gray"
        )
    )


if __name__ == "__main__":
    main()
