# 系统错误处理和日志记录优化指南

## 1. 后端错误处理

### 1.1 全局异常处理器

后端已实现全局异常处理，建议添加以下优化：

```python
# app/main.py
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request, status
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.warning(f"请求验证失败：{exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"全局异常：{exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "detail": str(exc) if app.debug else "内部服务器错误"
        }
    )
```

### 1.2 HTTP 异常处理

```python
# app/api/v1/diagnosis.py
from fastapi import HTTPException, status

async def upload_image(...):
    """图像上传 API"""
    try:
        # 文件验证
        if not file.filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的文件格式，请上传 JPG、PNG 或 GIF 格式的图片"
            )
        
        # 文件大小检查
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置文件指针
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件大小超过 5MB 限制"
            )
        
        # ... 其他处理逻辑
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图像上传失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传失败：{str(e)}"
        )
```

### 1.3 超时处理

```python
# app/services/diagnosis.py
import asyncio
from fastapi import HTTPException, status

async def diagnose_image(self, image_path: str, symptoms: str = None):
    """图像诊断（带超时控制）"""
    try:
        # 设置总超时 30 秒
        async with asyncio.timeout(30):
            # 阶段 1: 视觉检测（10 秒）
            async with asyncio.timeout(10):
                vision_result = await self.vision_detect(image_path)
            
            # 阶段 2: 认知分析（15 秒）
            async with asyncio.timeout(15):
                cognition_result = await self.cognition_analyze(image_path)
            
            # 阶段 3: 融合决策（5 秒）
            async with asyncio.timeout(5):
                final_result = await self.fusion(vision_result, cognition_result)
            
            return final_result
            
    except asyncio.TimeoutError:
        logger.error("诊断超时")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="诊断超时，请稍后重试"
        )
```

## 2. 前端错误处理

### 2.1 全局错误处理

```typescript
// src/utils/errorHandler.ts
import { ElMessage } from 'element-plus'
import type { AxiosError } from 'axios'

/**
 * 全局错误处理器
 */
export function handleError(error: AxiosError) {
  // 网络错误
  if (!navigator.onLine) {
    ElMessage.error('网络连接已断开，请检查网络')
    return
  }
  
  // Axios 错误
  if (error.response) {
    const status = error.response.status
    
    switch (status) {
      case 400:
        ElMessage.error('请求参数错误')
        break
      case 401:
        ElMessage.error('未授权，请登录')
        // 清除 token 并跳转登录页
        localStorage.removeItem('token')
        window.location.href = '/login'
        break
      case 403:
        ElMessage.error('拒绝访问')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 422:
        ElMessage.error('数据验证失败')
        break
      case 500:
        ElMessage.error('服务器内部错误')
        break
      case 503:
        ElMessage.error('服务不可用')
        break
      default:
        ElMessage.error(`请求失败：${status}`)
    }
  } else if (error.request) {
    // 请求已发送但没有收到响应
    ElMessage.error('请求超时，请稍后重试')
  } else {
    // 其他错误
    ElMessage.error(`错误：${error.message}`)
  }
  
  // 记录错误日志（发送到监控服务）
  console.error('请求错误:', error)
}
```

### 2.2 组件级错误处理

```vue
<!-- src/views/Diagnosis.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadImage, diagnoseImage } from '@/api/diagnosis'
import { handleError } from '@/utils/errorHandler'

const uploading = ref(false)
const diagnosing = ref(false)
const error = ref<string | null>(null)

/**
 * 处理图片上传
 */
const handleUpload = async (file: File) => {
  uploading.value = true
  error.value = null
  
  try {
    // 上传文件
    const uploadResult = await uploadImage(file)
    
    // 开始诊断
    diagnosing.value = true
    const diagnosisResult = await diagnoseImage(uploadResult.image_url)
    
    // 显示结果
    ElMessage.success('诊断完成')
    
  } catch (err) {
    // 统一错误处理
    handleError(err as any)
    error.value = '诊断失败，请稍后重试'
  } finally {
    uploading.value = false
    diagnosing.value = false
  }
}
</script>

<template>
  <div>
    <!-- 错误提示 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      :closable="true"
      @close="error = null"
    />
    
    <!-- 其他内容 -->
  </div>
</template>
```

## 3. 日志记录优化

### 3.1 后端日志配置

```python
# app/core/logging_config.py
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

def setup_logging():
    """配置应用日志"""
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 日志文件名（按日期分割）
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # 文件处理器（按大小轮转）
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            ),
            # 控制台处理器
            logging.StreamHandler()
        ]
    )
    
    # 设置特定模块的日志级别
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)
    
    logger = logging.getLogger('app')
    logger.info("应用日志初始化完成")
    
    return logger
```

### 3.2 业务日志记录

```python
# app/services/diagnosis.py
import logging

logger = logging.getLogger(__name__)

async def diagnose_image(self, image_path: str, symptoms: str = None):
    """图像诊断（带详细日志）"""
    
    logger.info(f"开始图像诊断：{image_path}")
    
    try:
        # 步骤 1: 检查缓存
        logger.debug("检查诊断缓存...")
        cached = await cache_service.get_diagnosis(image_md5)
        if cached:
            logger.info(f"缓存命中：{cached['disease_name']}")
            return cached
        
        logger.debug("缓存未命中，开始 AI 诊断")
        
        # 步骤 2: 视觉检测
        logger.info("执行视觉检测...")
        vision_result = await vision_engine.detect(image_path)
        logger.info(f"视觉检测完成：{len(vision_result)} 个目标")
        
        # 步骤 3: 认知分析
        logger.info("执行认知分析...")
        cognition_result = await cognition_engine.analyze(image_path)
        logger.info("认知分析完成")
        
        # 步骤 4: 融合决策
        logger.info("执行融合决策...")
        final_result = await fusion_engine.fuse(vision_result, cognition_result)
        logger.info(f"融合完成：{final_result['disease_name']}")
        
        # 步骤 5: 缓存结果
        logger.debug("缓存诊断结果...")
        await cache_service.set_diagnosis(image_md5, final_result)
        
        logger.info(f"诊断完成：{final_result['disease_name']}")
        return final_result
        
    except Exception as e:
        logger.error(f"诊断失败：{e}", exc_info=True)
        raise
```

### 3.3 前端日志记录

```typescript
// src/utils/logger.ts
/**
 * 前端日志工具
 */
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3
}

const CURRENT_LEVEL = LOG_LEVELS.DEBUG // 生产环境可设置为 ERROR

export const logger = {
  debug(message: string, ...args: any[]) {
    if (CURRENT_LEVEL <= LOG_LEVELS.DEBUG) {
      console.debug(`[DEBUG] ${message}`, ...args)
    }
  },
  
  info(message: string, ...args: any[]) {
    if (CURRENT_LEVEL <= LOG_LEVELS.INFO) {
      console.info(`[INFO] ${message}`, ...args)
    }
  },
  
  warn(message: string, ...args: any[]) {
    if (CURRENT_LEVEL <= LOG_LEVELS.WARN) {
      console.warn(`[WARN] ${message}`, ...args)
    }
  },
  
  error(message: string, ...args: any[]) {
    if (CURRENT_LEVEL <= LOG_LEVELS.ERROR) {
      console.error(`[ERROR] ${message}`, ...args)
    }
  }
}

// 使用示例
logger.info('用户登录成功', userId)
logger.error('API 请求失败', error)
```

## 4. 监控和告警

### 4.1 性能监控

```python
# app/middleware/performance.py
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录请求耗时
        if process_time > 1.0:  # 超过 1 秒记录警告
            logger.warning(
                f"慢请求：{request.method} {request.url.path} - {process_time:.2f}s"
            )
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
```

### 4.2 错误监控

建议使用错误监控服务：
- Sentry: 开源错误追踪
- Bugsnag: 实时错误监控
- 阿里云 ARMS: 应用实时监控

## 5. 检查清单

- [x] 全局异常处理
- [x] HTTP 异常处理
- [x] 超时控制
- [x] 日志配置
- [x] 业务日志记录
- [x] 前端错误处理
- [x] 前端日志工具
- [ ] 性能监控中间件
- [ ] 错误监控服务集成
- [ ] 日志分析和告警
