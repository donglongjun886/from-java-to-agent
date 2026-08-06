# Job Intel Agent — AI岗位情报系统

## 定位

部署在阿里云，飞书Bot交互，VC投资组合 → 官网/公众号岗位采集 → 主动推送 + 对话查询。

## 数据链路

1. **VC投资组合采集**：红杉/高瓴/IDG等VC投资组合页 + 烯牛/IT桔子按赛道筛选 → 公司名/赛道/轮次/时间（结构化，高信噪比）
2. **实体链接**：公司名 → 官网域名
3. **Web Agent 岗位抓取**：Agent自主导航官网 + 公众号，提取岗位信息（标题/地点/JD）
4. **去重存储**：SQLite + ChromaDB（公司+标题语义相似度去重）
5. **飞书Bot交互**：主动推送（定时发现新岗位）+ 对话查询（自然语言检索）

## 核心Agent能力

| 能力 | 实现 |
|------|------|
| Web Agent 自主导航 | Browser Use / Playwright，理解页面语义找招聘页 |
| RAG检索 | 岗位向量化 → 语义检索 → 排序返回 |
| 记忆系统 | 短期=对话历史，长期=用户偏好画像（赛道/阶段/地点），情景=已读/跳过/感兴趣 |
| 主动推送 | 定时采集 → 新岗位发现 → 飞书消息推送 |

## 三层Evaluation

- **RAG检索**：NDCG/MRR + 用户反馈排序质量
- **Web Agent**：官网抓取成功率、信息准确率、覆盖率
- **记忆系统**：偏好提取准确率、记忆检索相关性

## 技术栈

- 采集：crawl4ai / firecrawl
- Web Agent：Browser Use + Playwright
- Agent框架：LangGraph
- 存储：SQLite + ChromaDB
- Bot：飞书开放平台 Webhook
- 部署：阿里云 + APScheduler定时任务

## 面试覆盖

- ✅ Web Agent前沿方向（2026差异化）
- ✅ Claude Code内核（记忆/压缩/去重/冲突，飞书Bot对话记忆系统）
- ✅ Evaluation（三层评估体系）
- ✅ 工程克制/边界（不爬需登录页、不搞CAPTCHA对抗、坦诚成功率）
- ✅ 性能tradeoff（离线vs实时、Agent导航token成本）
- ✅ 实际项目扛细节（自己天天用，真数字）

## 已有项目互补

```
agent-gateway       → Agent基础设施（编排+安全+可观测）
smart-report-agent  → 企业内部知识（封闭文档+RAG+权限）
job-intel-agent     → 外部市场情报（开放Web+自主采集+主动推送+记忆）
```

## 难点与边界

| 难点 | 策略 |
|------|------|
| 官网结构各异，成功率天花板 | 三级导航（sitemap→/careers路径→Agent自主导航），坦诚60-70% |
| Web Agent死循环/Context溢出 | 轮次熔断 + DOM裁剪 + 失败Case记录 |
| 融资≠招聘 | 弱信号聚合，用户最终判断 |
| 官网无招聘页 | 公众号作为补充信源 |

## 时间规划

| 阶段 | 时间 | 产出 |
|------|------|------|
| MVP闭环 | Day 1-3 | 预设30家公司 → Web Agent → SQLite → 飞书Bot对话 |
| 评估拿真数字 | Day 4-5 | 人工标注Ground Truth，成功率/耗时/Token消耗/检索命中率 |
| 面试防御 | Day 6-10 | 停止写代码，失败Case话术 + 技术复盘 |