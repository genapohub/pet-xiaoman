# pet_xiaoman_admin · B 端管理后台（Web）

门店后台（PRD §5.1 B001-B010）。Vue3 + Element Plus + Vite + Pinia（ADR-003）。

```bash
npm install
npm run dev     # 开发（/api 代理到 127.0.0.1:8000）
npm run build   # 构建产物 → 微信云托管静态托管（ADR-005）
```

- 布局骨架对齐 PRD §5.6.3 后台视觉总纲：Navbar 60px + Sider 220px + 主色 #0056D9
- 路由骨架已挂 B001 工作台占位，其余页面（B002-B010）按开发闭环逐页补齐
