# PRD：健康检查端点

## 目标

给现有后端增加 `GET /health`，返回 JSON `{"status":"ok"}`，HTTP 200。

## 非目标

不改前端，不做认证，不改部署架构。

## 验收

1. 启动服务后 `curl -s localhost:<port>/health` 返回含 status=ok
2. 相关测试通过
3. wiki 如有后端路由变更则更新 L4B/L5（若项目已有 wiki）

## 约束

- 不改无关模块
- 测试必须真实跑通
