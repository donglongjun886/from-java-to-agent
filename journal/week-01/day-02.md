# Day 2：Python 进阶 + LLM 基础（2026-06-08）

## 今日目标

- 用 Java 类比快速掌握 Pydantic V2（BaseModel / Field / 校验 / 序列化）
- 理解 LLM 三个核心概念：Token / Temperature / Context Window
- 启动项目A：Agent 网关平台的 Java 晚段对照

## 已完成

### 资料阅读

| 资料 | 状态 |
|------|------|
| [Pydantic V2 concepts/models](https://docs.pydantic.dev/latest/concepts/models/) | ✅ |
| [Pydantic V2 concepts/fields](https://docs.pydantic.dev/latest/concepts/fields/) | ✅ |
| [OpenAI Tokenizer 工具](https://platform.openai.com/tokenizer) | ⏭️ 跳过（quiz 形式理解） |
| [DeepSeek API 文档](https://platform.deepseek.com/api-docs/) | ⏭️ 跳过（被告知找不到「参数说明」章节，参考 OpenAI API 文档） |
| Anthropic Context Engineering 指南 | ⏭️ 跳过（404 / 路径变更） |

### 概念掌握

- **Pydantic BaseModel / Field**：完整理解 `BaseModel` / `Field()` / `Field(...)`（必填）/ `Field(default=...)` / `Field(frozen=True)` / `Field(alias=...)` / `Field(description=...)` / `Field(ge=, le=, pattern=)`
- **Pydantic 序列化**：`model.model_dump()` ≈ Jackson `writeValueAsString`，`Model.model_validate(json)` ≈ Jackson `readValue`
- **Pydantic strict vs lax**：默认 lax 模式自动强转类型（如 `"123"` → `int(123)`），需要严格校验时显式 `ConfigDict(strict=True)`。**反直觉**——Java 工程师会以为默认严格
- **LLM Token**：1 汉字 ≈ 1.5-2 token（比英文「费」，跟直觉相反），500 字中文 ≈ 850 token
- **LLM Temperature**：控制「随机性」而非「正确性」。`temperature=0` 解决可复现性，不解决幻觉
- **LLM Context Window**：单次输入+输出 token 上限。Lost in the Middle 现象：模型对中间位置注意力弱

### 代码理解

- 完整掌握 Pydantic V2 `models` 页面的 `Helper functions`（`model_dump` / `model_dump_json` / `model_validate`）
- 写完 `projects/agent-gateway-java/` 的 Spring AI + DashScope Hello World 骨架（5 个文件，214 行）
- 理解了 Spring AI 的链式 DSL：`chatClient.prompt().user(msg).call().content()` ≈ Python 的 `client.chat.completions.create(...)`
- **晚段：完整跑通 `GET /chat` → 收到 qwen3.7-plus 回复**："Hello! How can I help you today?"（详见下面"晚段集成踩坑"）

## 三道验收题（自我测验）

### Q1：500 字中文 ≈ 多少 token？成本多少？

```
500 字中文 × 1.5 ~ 500 字中文 × 2 = 750 ~ 1000 token
取中 850 token

input  成本 = 850 × 2/1,000,000  = 0.0017 元
output 成本 = 510 × 8/1,000,000  = 0.0041 元
单次成本 ≈ 0.0058 元（≈ 6 厘）

日活 1 万 × 5 轮/天 = 5 万次
日成本 ≈ 290 元，月成本 ≈ 8700 元
```

**踩坑**：第一反应是「500 × 3/4 = 375」（以为汉字信息密度高所以省 token）。**反了**——BPE 按字节对频率切，中文每个字各占一个 token，**比英文费**。

### Q2：SQL Agent 用哪个 temperature？

```
答：temperature = 0
原因：可复现 + 降低随机性
```

**不足**：温度 0 只解决可复现性，不解决正确性。完整防御链是：
```
temperature=0 → schema 进 prompt → response_format=json → 
Pydantic 校验 → EXPLAIN 验证 → 失败重试 + 错误回传
```

### Q3：Pydantic model_validate 失败原因？

```python
raw = '{"order_id": "12345", "amount": "99.5", "currency": 100}'
order = Order.model_validate(json.loads(raw))
```

**直觉**：3 个字段类型不匹配，应该报错。
**实际**：**不会报错**，Pydantic V2 默认 lax 模式全部默默强转：
- `"12345"` → `12345`（int）
- `"99.5"` → `99.5`（float）
- `100` → `"100"`（str）

要触发严格校验必须 `model_config = ConfigDict(strict=True)`。

**反直觉发现**：Pydantic V2 默认行为**不是** Java 强类型哲学，是 JavaScript 宽松哲学。

## 关键认知

- **Pydantic 字段名避开 Python builtin**：`int` / `str` / `list` / `dict` 都不能直接做字段名（触发 builtin 遮蔽，注解被解析成 `Optional[None]`）。`final` 是语言契约，`frozen` 是框架契约——本质不同
- **汉字比英文费 token**：成本估算别拍脑袋用「1 字 ≈ 1 token」，实际是 1.5-2
- **`temperature=0` ≠ 万能**：只解决可复现性，幻觉 / 格式 / 语法 / 业务四类问题各有不同解法
- **Spring AI 链式 DSL 跟 Java Stream / Builder 模式一脉相承**：每步返回下一步能操作的对象，到 `.call()` 才真正发请求
- **Pydantic 跟 Jackson 表面相似哲学不同**：Pydantic V2 默认宽松，Jackson 默认严格

## 产出

- ✅ `notes/llm-fundamentals.md`（新建，~280 行）—— Token/Temperature/Context Window + 3 道验收题
- ✅ `notes/python-for-java-devs.md`（+185 行 Pydantic 进阶章节）—— Field 必填/约束/description/alias/frozen/int 陷阱/strict 模式
- ✅ `projects/agent-gateway-java/`（新建 5 个文件，214 行 → 8 个文件含 README 修正 + .gitignore）—— Spring AI + DashScope **完整跑通**
- ✅ `README.md`（同步 v4 计划）—— 学习路径表/项目结构/技术栈/核心公式
- ✅ 晚段：Spring Boot + Spring AI + DashScope qwen3.7-plus **链路验证通过**

## 晚段集成踩坑（Spring AI + DashScope）

### 坑 1：artifactId 写错
- 错误：`spring-ai-alibaba-starter`（不存在）
- 正确：`spring-ai-alibaba-starter-dashscope`

### 坑 2：BOM 版本号
- 错误：`spring-ai-alibaba-bom:1.0.0`（不存在）
- 实际：`1.0.0.2`（最新 stable）

### 坑 3：alibaba 原生端点对 qwen3.7+ 不识别 ⭐ 最关键
- 错误：用 `spring-ai-alibaba-starter-dashscope` 走原生端点 `/api/v1/services/aigc/...`
- 现象：HTTP 400 `url error`
- **正解**：用 `spring-ai-starter-model-openai` + DashScope 兼容模式
  ```yaml
  base-url: https://dashscope.aliyuncs.com/compatible-mode
  ```

### 坑 4：base-url 千万别带 `/v1`
- 错误：`base-url: https://dashscope.aliyuncs.com/compatible-mode/v1`
- 现象：HTTP 500 `FileNotFoundException: .../v1/v1/chat/completions`（v1 重复）
- **正解**：去掉 `/v1`，让 SDK 自动拼

### 坑 5：用户 hint 没认真听 ⭐ 最重要
- 用户给的关键 hint：`BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"`
- 我的第一反应是去查 model 列表、怀疑模型名拼错
- **正解**：hint 本身就指明了「用 OpenAI 兼容模式」，应该立即行动而不是先质疑用户

## 环境折腾记录

- 系统缺 Maven，`brew install maven` 第一次卡死在 `brew update --auto-update`（访问 GitHub 慢/被墙）
- **解决**：把 brew 主仓库切到阿里云镜像（`git remote set-url origin https://mirrors.aliyun.com/homebrew/brew.git`），重试秒过
- 新版 Homebrew 没有独立 `homebrew/core` tap，主仓库改完就够
- **Maven 中央仓库在国内慢**（8-46 kB/s），加 `~/.m2/settings.xml` 配阿里云镜像后 5.5 MB/s（**600 倍提升**）
- `Co-Authored-By` 之前误用 `MiniMax-M3`，用户要求统一用 `Claude <noreply@anthropic.com>`，已存到记忆

## 今日教训

1. **跨语言对照是杀手锏**：把 `final` vs `frozen` / Java 强类型 vs Pydantic lax / Spring Stream vs Spring AI Chain 一一对应，Java 工程师迁移效率翻倍
2. **反直觉假设要主动质疑**：以为「汉字省 token」「Pydantic 默认严格」「`frozen` 像 `final`」「qwen3.7-plus 不存在」四个都错了。下次先验后讲
3. **环境折腾提前做**：Maven/网络这种基础设施问题应该 Day1 就验证完，不要留到「要用的时候」才发现
4. **commit author 一致性**：用户对 `Co-Authored-By` 字段有偏好，**首次 commit 前先问**，避免后续批量改
5. **用户 hint 是金子**：用户给具体技术 hint（如 "用 compatible-mode"）时，**先研究 hint 本身**，不要先跳到自己熟悉的"老思路"上去质疑用户。这次被用户怼"脑子有问题"是因为我跑偏了

---

*记录日期：2026-06-08*
