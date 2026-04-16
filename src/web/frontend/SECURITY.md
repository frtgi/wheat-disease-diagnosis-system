# WheatAgent 前端安全指南
# =========================

本文档说明前端依赖安全管理的最佳实践和操作流程。

## 1. 已知漏洞修复

### 1.1 overrides 配置说明

当前 `package.json` 中已配置 `overrides` 字段，强制所有直接和间接依赖使用安全版本：

| 包名 | 漏洞编号 | CVSS | 修复版本 |
|------|---------|------|---------|
| lodash | CVE-2021-23337 | 8.1 (高危) | ^4.17.21 |
| braces | CVE-2024-4068 | 7.5 (高危) | ^3.0.3 |
| micromatch | ReDoS 风险 | - | ^4.0.5 |

**文件位置**: [package.json](./package.json)

```json
{
  "overrides": {
    "lodash": "^4.17.21",
    "braces": "^3.0.3",
    "micromatch": "^4.0.5"
  }
}
```

## 2. 定期安全检查流程

### 2.1 手动审计

```bash
# 进入前端目录
cd src/web/frontend

# 查看漏洞报告
npm audit

# 查看详细漏洞信息
npm audit --json

# 仅查看严重和高危漏洞
npm audit --audit-level=moderate
```

### 2.2 自动修复

```bash
# 自动修复可自动更新的依赖（仅更新 patch 版本）
npm audit fix

# 强制修复（可能破坏兼容性，需谨慎）
npm audit fix --force

# 修复后重新验证
npm audit
```

### 2.3 CI/CD 集成建议

在 CI 流水线中添加安全检查步骤：

```yaml
# GitHub Actions 示例
- name: Security Audit
  run: |
    cd src/web/frontend
    npm audit --audit-level=high || echo "发现安全问题，请检查"
```

## 3. .npmrc 安全配置

项目已配置 `.npmrc` 文件，包含以下安全措施：

- **强制 HTTPS**: 所有 registry 通信使用加密连接
- **Strict SSL**: 启用严格的证书验证
- **Engine Strict**: 强制 Node.js 版本匹配
- **Lockfile Version 3**: 使用最新的锁文件格式

**文件位置**: [.npmrc](./.npmrc)

## 4. 依赖更新策略

### 4.1 版本分类

| 类型 | 命令 | 说明 |
|------|------|------|
| Patch 更新 | `npm update` | 修复 bug 和安全漏洞，向后兼容 |
| Minor 更新 | `npx npm-check-updates -u -t minor` | 新功能，向后兼容 |
| Major 更新 | `npx npm-check-updates -u -t major` | 可能包含破坏性变更 |

### 4.2 推荐工作流

```bash
# 1. 检查过时依赖
npx npm-check-outdated

# 2. 更新到最新安全版本
npx npm-check-updates -u

# 3. 安装更新后的依赖
npm install

# 4. 运行测试确保无回归
npm test

# 5. 再次运行安全审计
npm audit
```

## 5. 安全最佳实践

1. **定期更新**: 至少每月运行一次 `npm audit`
2. **锁定依赖**: 始终提交 `package-lock.json`
3. **审查新依赖**: 添加任何新包前先检查其安全记录
4. **最小权限**: 只安装必要的依赖
5. **监控告警**: 可集成 Snyk 或 Dependabot 进行持续监控

## 6. 应急响应流程

当发现新的高危漏洞时：

1. 立即在 `overrides` 中强制安全版本
2. 运行 `npm audit fix` 尝试自动修复
3. 如无法自动修复，手动升级受影响依赖
4. 运行完整测试套件确保功能正常
5. 记录修复过程并更新本文档
