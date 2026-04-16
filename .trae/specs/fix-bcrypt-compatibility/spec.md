# bcrypt 密码验证兼容性修复 Spec

## Why
bcrypt 库版本与 passlib 不兼容，导致用户登录时密码验证失败。bcrypt 4.1+ 版本移除了 `__about__` 属性，且 bcrypt 限制密码长度为 72 字节，需要修复兼容性问题。

## What Changes
- 修复 bcrypt 版本兼容性问题
- 添加密码长度截断处理
- 更新密码验证逻辑

## Impact
- Affected specs: 用户认证、登录功能
- Affected code: `src/web/backend/app/core/security.py`

## ADDED Requirements

### Requirement: 密码验证兼容性
系统 SHALL 正确处理 bcrypt 密码验证，兼容不同版本的 bcrypt 库。

#### Scenario: 登录成功
- **WHEN** 用户使用正确的用户名和密码登录
- **THEN** 系统应正确验证密码并返回登录成功

#### Scenario: 密码长度处理
- **WHEN** 密码超过 72 字节
- **THEN** 系统应自动截断并正常验证

## 错误详情

### 错误类型
库版本兼容性问题 (Library Version Compatibility)

### 错误信息
```
AttributeError: module 'bcrypt' has no attribute '__about__'
ValueError: password cannot be longer than 72 bytes
```

### 触发条件
1. 用户登录时进行密码验证
2. bcrypt 版本 >= 4.1.0
3. passlib 尝试读取 bcrypt 版本信息失败

### 根本原因
1. bcrypt 4.1+ 版本移除了 `__about__` 模块属性
2. bcrypt 限制密码长度为 72 字节，超过会抛出异常
