# Java 架构师面试复习提纲 v2.2

> 社招架构师面试知识域，按 P0/P1/P2 优先级分层。面试目标是「能用自己的话流畅讲出核心故事」，不是背书。

---

## 知识全景图

<div style="font-size:12px;line-height:1.6">

| 知识域 | 优先级 | 一句话核心 |
|--------|--------|-----------|
| 项目 STAR + 技术选型 | **P0** | 把你做过的最难决策讲成故事 |
| Java 并发底层原理 | **P0** | JMM→volatile→synchronized→AQS 一条线串到底 |
| Spring Framework 深度 | **P0** | IOC/AOP/循环依赖/事务传播，框架不是黑盒 |
| 微服务体系核心 | **P0** | Spring Cloud+Dubbo双线：分布式事务/锁/选型/SPI/灰度/压测/链路追踪 |
| 中台架构设计 | **P1** | 三明治分层/SPI扩展/策略兼容/商品中心/厚薄权衡 |
| MySQL 深度 | **P1** | 索引→锁→MVCC→日志→主从，一条链路 |
| Redis 深度 | **P1** | 底层数据结构→持久化→淘汰→集群→一致性 |
| 消息队列 | **P1** | RocketMQ（业务）+ Kafka（流），双线覆盖 |
| IO 模型 & Netty | **P1** | BIO→NIO→epoll→Netty Reactor，讲出演进 |
| 分布式理论 | **P1** | CAP→Raft→分布式ID，理论支撑选型 |
| 系统设计 & 算法 | **P1** | 5步法 + 核心题思路 + 秒杀完整走通示例 |
| JVM & 故障排查 | **P2** | G1/ZGC + 真实调优案例 + CMS→G1→ZGC演进脉络 |
| 操作系统 & 网络基础 | **P2** | TCP/虚拟内存/CPU缓存 + HTTP2/gRPC/WebSocket |
| 设计模式在框架中的应用 | **P2** | 每种模式讲出 Spring 中的应用 |
| 新趋势 & 速览 | **P2** | 虚拟线程/OTel/AI接入 |
| Java 基础体系 | **P2** | 集合/反射/泛型/异常，表格式速查 |
| 安全基础 | **P2** | JWT/OAuth2/SQL注入/XSS/CSRF |
| 系统稳定性 | **P1** | 降级限流熔断 + 监控告警 + 故障应急 + 灰度发布 + 依赖治理 |
| 容器化基础 | **P2** | Docker镜像分层 + K8s核心概念 + 优雅上下线 |
| Elasticsearch | **P2** | 倒排索引/写入流程/脑裂 |
| 技术项目管理（软素质） | **P0** | 需求冲突/排期风险/跨团队协作/故障复盘——架构师面必问 |

</div>

---

## P0：必考核心（面试必定问到的部分）

---

## 一、项目经历 & 技术选型（P0）

### 项目 STAR

准备 2 个最能体现技术深度的项目，每个能 3-5 分钟讲完。**建议组合**：一个体现架构设计与选型决策，一个体现深度问题解决（性能优化/线上故障/技术债治理）。

```
S（背景）：业务规模（QPS/DAU/数据量）+ 技术痛点
T（目标）：一句话说清楚要解决什么
A（行动）：候选方案 A vs B，为什么选 A？落地过程 + 踩过最大的坑
R（结果）：技术指标（优化前 XX→优化后 YY）+ 业务收益（成本降低 X%/性能提升 X 倍/支撑了 YY 业务增长）。
           架构师面试必须讲出「技术投入对业务的实际价值」
```

**3 层追问**（提前想好答案）：
- 「如果重新做，你会怎么改进？」（考察反思）
- 「这个方案有什么局限性？如果流量翻 10 倍哪里先崩？」（考察全局观）
- 「这个项目你最大的遗憾是什么？」（考察深度认知）

**架构演进**（如果项目涉及）：
```
单体（规模/痛点）→ 垂直拆分（拆分决策）→ 服务化（引入什么/解决什么）
→ 当前状态 + 如果今天从零开始你会怎么设计？
```

注意：面试官会特别关注**「你在这个项目中具体做了什么决策」**，不是「你们团队做了什么」。用「我主导了/我推动了/我决定」而不是「我们」。

### 技术选型 Trade-off

**核心认知**：架构师面试不考「怎么用」，考「为什么选这个而不是那个，代价是什么」。

准备 3 组最常被问的选型对比：

**选型心法（面试开场白）**：架构师的选型不是在真空中比技术指标，而是在「业务需求 + 团队能力 + 运维成本 + 社区生态」四个约束下做最优决策。不做性能最强的，做最适合当下的。

**分布式锁：Redis vs ZK vs etcd**

| 维度 | Redis(Redisson) | ZooKeeper | etcd |
|------|-----------------|-----------|------|
| 性能 | 高（内存） | 中（磁盘+网络） | 中 |
| 一致性 | 弱（主从切换锁丢失） | 强（ZAB） | 强（Raft） |
| 运维 | 低（已有Redis） | 中 | 中 |
| 可重入 | Hash + key(threadId) | 临时顺序节点 | 租约+Revision |

关键追问：*「Redis主从切换锁丢失怎么兜底？」* → 锁是性能优化，不是唯一防线；业务层用 DB 唯一索引/版本号做最终兜底。高层次认知：锁丢失的概率极低，真正要防的是**锁失效后的业务幂等**。

**MQ：RocketMQ vs Kafka**

| 维度 | RocketMQ | Kafka |
|------|----------|-------|
| 事务消息 | 原生支持（半消息+回查） | 应用层实现 |
| 吞吐量 | 十万级 | 百万级 |
| 适用 | 业务消息（订单/支付） | 流处理/日志/大数据 |
| 延迟 | 低延迟场景优化 | 批量处理 |
| 消费者 | 推/拉结合 | 拉模式 |

说清楚你的场景为什么选这个，不选另一个的原因。架构师的选型认知：RocketMQ 主打「可靠业务消息」，Kafka 主打「海量数据管道」。如果是电商交易链路选 RocketMQ，如果是日志/埋点/流计算选 Kafka。不纠结「谁更好」，纠结「谁更适合」。

**注册中心：Nacos vs Eureka vs Consul**

| 维度 | Nacos | Eureka | Consul |
|------|-------|--------|--------|
| AP/CP | 可切换（临时=AP，永久=CP） | 纯 AP | 可切换 |
| 配置中心 | 内置 | 无 | 有但简陋 |
| 国内生态 | 标配 | Netflix 已停维护 | 弱 |
| 健康检查 | TCP/HTTP/MySQL 自定义 | HTTP 心跳 | Script/TCP/HTTP |

**Nacos 选型理由**：注册中心+配置中心一体化，降低运维组件数量。临时实例走 AP（去中心化心跳检测，自动剔除故障节点），永久实例走 CP（Raft 一致性协议保证数据一致）。为什么不是 Eureka？Netflix 已停止维护（Spring Cloud Netflix 进入维护模式），且没有配置中心能力需要额外维护 Apollo/Nacos Config。为什么不是 Consul？国内文档和社区生态远不如 Nacos。

**Nacos 一致性取舍追问**：
- 临时实例：客户端 5s 心跳，服务端 15s 无心跳剔除，CAP 选 AP
- 永久实例：走 Raft 协议，CAP 选 CP，需要手动上下线
- 微服务注册场景用临时实例；DNS/F5 这类基础设施用永久实例
- 配置中心长轮询：客户端 hold 连接 30s，有变更立即返回，无变更返回 304

### 微服务拆分决策

不讲「订单服务/商品服务」这种业务维度，讲决策框架：

```
战略设计：子域划分（核心域/支撑域/通用域）→ 限界上下文（业务边界）
战术设计：聚合根（一致性边界）→ 领域事件（跨上下文通信）
落地维度：数据边界（独立数据库？跨库事务？）→ 团队边界（康威定律）→ 变更边界（不一起变的不要拆）
```

至少要能讲清楚：你是怎么识别聚合根的？跨限界上下文怎么通信（MQ/API/RPC）？有过拆分过度导致性能下降的反思案例更好。

**面试话术参考**：
> 「拆分的核心原则不是按业务功能拆，而是按**数据一致性边界**拆。同一个聚合根内部的强一致性需求放在一个服务内，跨聚合根的场景用最终一致性（MQ+本地消息表）解决。我们曾经把订单和支付拆成两个服务，结果退款场景的分布式事务复杂度远超收益，后来合并了。」

---

## 二、Java 并发底层原理（P0）🔥

> 这一章是 Java 工程师的**基本盘**。面试官默认你应该能把 JMM→volatile→synchronized→AQS→线程池 这条线讲清楚。不要只讲「怎么用」，要讲「底层做了什么」。

### 2.1 Java 内存模型（JMM）

**面试话术（30秒版）**：
> 「JMM 定义了共享变量在多线程间的访问规则，核心是 happens-before 原则。主内存是所有线程共享的，每个线程有自己的工作内存（CPU 缓存 + 寄存器），这就是可见性问题的根源。volatile 和 synchronized 本质上都是通过内存屏障指令来强制执行 happens-before 规则。」

**happens-before 核心规则**（不是全部，只记最常考的）：

| 规则 | 含义 | 面试怎么讲 |
|------|------|-----------|
| 程序次序 | 单线程内，前面的操作 happens-before 后面 | 基础认知 |
| volatile | volatile 写 happens-before 后续读 | **volatile 保证可见性的理论依据** |
| 锁 | unlock happens-before 后续 lock | synchronized 释放的变量对后续获取者可见 |
| 传递性 | A hb B, B hb C → A hb C | 结合上两条，解释为什么 volatile + synchronized 组合安全 |
| start/join | 线程 start hb 线程内操作；线程内操作 hb join 返回 | 线程生命周期保证 |

**追问：JMM 和 JVM 内存结构（堆/栈/方法区）的区别？**
- JMM 是**规范/抽象模型**，定义多线程下的内存访问规则
- JVM 内存结构是**具体实现**，定义运行时数据存储区域
- 面试中容易混，问清楚面试官要哪个

**追问：happens-before 和 as-if-serial 的区别？**
- as-if-serial：单线程内，无论怎么重排序，执行结果不变（给编译器的承诺）
- happens-before：跨线程的可见性保证（给程序员的承诺）
- 一句话：as-if-serial 保单线程正确，happens-before 保多线程正确

### 2.2 volatile

**面试话术（30秒版）**：
> 「volatile 两层语义：可见性 + 有序性，但**不保证原子性**。可见性靠写后立即刷新到主内存 + 读前从主内存加载实现。有序性靠内存屏障禁止指令重排序——volatile 写之前插 StoreStore 屏障，写之后插 StoreLoad 屏障；volatile 读之后插 LoadLoad 和 LoadStore 屏障。」

**记忆口诀**：volatile 轻量级同步，有可见、有序，无原子。

**DCL 单例为什么需要 volatile？**（高频面试题）

```
public class Singleton {
    private static volatile Singleton instance;  // ← 为什么加 volatile？

    public static Singleton getInstance() {
        if (instance == null) {                  // 第一次检查（性能优化）
            synchronized (Singleton.class) {
                if (instance == null) {          // 第二次检查（保证单例）
                    instance = new Singleton();   // ← 这里可能指令重排！
                }
            }
        }
        return instance;
    }
}
```

new Singleton() 的字节码三步：
1. 分配内存空间
2. 执行构造方法（初始化对象）
3. 将引用指向内存地址

2 和 3 可能被 JIT 重排序 → 另一个线程在第一次检查时看到非 null 但未初始化完成的对象 → **半初始化对象问题**。volatile 禁止 2 和 3 重排。

**追问：volatile 和 synchronized 的区别？**

| 维度 | volatile | synchronized |
|------|----------|--------------|
| 可见性 | 保证 | 保证 |
| 有序性 | 部分保证 | 保证（临界区内可重排，但不能逃逸） |
| 原子性 | 不保证 | 保证 |
| 性能 | 读写同普通变量 | 有锁开销（但 JDK6+ 优化后差距缩小） |
| 适用 | 状态标记 + DCL | 复合操作（i++/check-then-act） |

**追问：volatile 能保证 long/double 的原子性吗？**
- JVM 规范不保证 64 位变量的读写原子性，但商用 JVM（HotSpot）的 64 位操作实际是原子的，所以 volatile 的 long/double 没问题
- 保险起见：64 位变量多线程共享时加 volatile（JDK 规范建议）

### 2.3 synchronized 锁升级

**面试话术（30秒版）**：
> 「JDK6 之后 synchronized 做了锁升级优化，从无锁→偏向锁→轻量级锁→重量级锁，单向升级不可降级。偏向锁在 Mark Word 中记录线程 ID，同一线程重入无需 CAS；轻量级锁通过 CAS 将 Mark Word 指向栈中的 Lock Record，自旋等待；竞争激烈时膨胀为重量级锁，线程阻塞由 OS mutex 实现，走内核态切换。」

**Mark Word 结构**：根据锁状态不同，Mark Word 分别存储 hashCode、线程ID、指向 Lock Record 的指针、或指向 ObjectMonitor 的指针，由标志位区分（01=无锁/偏向锁、00=轻量级锁、10=重量级锁、11=GC标记）。

**锁升级路径**：

> **版本提示**：偏向锁在 JDK 15 已废弃（JEP 374），JDK 21 默认关闭。以下内容作为理解锁升级演进历史仍有价值，但面试时应主动提一句"偏向锁已被废弃"展示版本意识。

```
               有竞争(撤销偏向)
无锁 ──→ 偏向锁 ──→ 轻量级锁 ──(自旋失败/竞争加剧)──→ 重量级锁
  ↑          ↓ CAS替换ThreadID        ↓ CAS设置LockRecord指针
  │    同一线程重入（无需CAS）      自旋等待（自适应次数）
  │
  └── 不可降级（单个锁实例：批量重偏向是JVM类级别策略调整，非单个实例降级）
```

**面试深水区追问**：

*「什么时候撤销偏向锁？」*
- 偏向锁默认延迟 4 秒启动，发生竞争时到达安全点后检查原持有线程状态→撤销偏向→升级轻量级锁。批量重偏向：一个类的大量对象频繁撤销偏向，JVM 判定偏向此类对象不值得→epoch 递增→批量重偏向。

*「轻量级锁自旋多少次？什么情况膨胀？」*
- 不是固定次数，是**自适应自旋**：JVM 根据上次自旋成功率动态调整。自旋失败的判断：锁持有者正在运行→继续自旋；锁持有者已阻塞→直接膨胀。

*「synchronized 和 ReentrantLock 怎么选？」*

| 维度 | synchronized | ReentrantLock |
|------|-------------|---------------|
| 实现 | JVM 层面（C++ ObjectMonitor） | JDK 层面（AQS） |
| 锁释放 | 自动（代码块结束/异常） | 必须 finally 中 unlock |
| 高级功能 | 无 | 可中断、可超时、可公平、多条件、tryLock |
| 性能 | JDK6+ 优化后接近甚至超过 | JDK6 以前领先，现在差距很小 |
| 适用 | 常规互斥场景 | 需要高级特性或已知竞争激烈的场景 |

**JIT 对 synchronized 的优化**（加分项）：
- 锁消除（Lock Elision）：JIT 分析发现锁对象不可能被多线程访问（逃逸分析）→ 直接去掉同步
- 锁粗化（Lock Coarsening）：连续多次加锁解锁（如循环内的 synchronized）→ 合并为一次大锁

### 2.4 CAS 与原子类

**面试话术（30秒版）**：
> 「CAS 是 Compare And Swap，CPU 提供的原子指令（cmpxchg），多核需要加 lock 前缀锁总线或缓存行。Java 通过 Unsafe 类的 compareAndSwapInt 调用。CAS 的经典问题是 ABA——用版本号/时间戳解决。高并发场景下 AtomicLong 有性能瓶颈，用 LongAdder 分段累加更好。」

**CAS 底层实现**：
1. Unsafe.compareAndSwapInt → native 方法
2. 对应 x86 的 `lock cmpxchg` 指令（lock 前缀锁缓存行/总线，保证原子性）
3. 多核 CPU：lock 信号锁定缓存行（MESI 协议保证缓存一致性），旧 CPU 会锁总线

**ABA 问题与解决方案**：

| 问题 | 场景 | 方案 |
|------|------|------|
| ABA | 线程1：A→B→A，线程2 CAS 看到还是 A 以为没变 | AtomicStampedReference（版本号 int stamp） |
| 标记位 | 场景简化，只需标记「是否改过」 | AtomicMarkableReference（boolean 标记） |

**追问：ABA 什么场景下真正有影响？**
> 典型是链表栈的出栈操作：head→A→B→C，线程1想CAS将head从A改B，但线程2先把A和B都出栈后又把A放回去了。线程1看到的head还是A，但A.next已经变了。这种场景必须用 AtomicStampedReference。

**LongAdder vs AtomicLong**：

| 维度 | AtomicLong | LongAdder |
|------|-----------|-----------|
| 原理 | CAS 自旋 | 分段累加（base + Cell[]），低竞争直接 CAS base，高竞争分散到 Cell |
| 高并发 | 自旋严重，CPU 占用高 | 吞吐量高，空间换时间 |
| sum() | O(1) | 需要累加所有 Cell（非精确，非原子快照） |
| 适用 | 低竞争 | 高并发统计（QPS 计数器等） |

**原子类家族**（面试能列举即可）：
- 基本类型：AtomicInteger、AtomicLong、AtomicBoolean
- 数组：AtomicIntegerArray、AtomicLongArray、AtomicReferenceArray
- 引用：AtomicReference、AtomicStampedReference、AtomicMarkableReference
- 字段更新器：AtomicIntegerFieldUpdater（原子更新对象字段，减少对象创建）
- 累加器（JDK8）：LongAdder、DoubleAdder、LongAccumulator

### 2.5 AQS（AbstractQueuedSynchronizer）

> 这是 Java 并发包的灵魂。**面试官问一个 JUC 工具 = 在考你 AQS**。

**面试话术（30秒版）**：
> 「AQS 的核心是 int state 表示同步状态 + FIFO 等待队列（CLH 变种） + 模板方法模式。ReentrantLock、Semaphore、CountDownLatch、ReentrantReadWriteLock 全都是基于 AQS 实现的。它提供独占和共享两种模式，子类只需要实现 tryAcquire/tryRelease 或 tryAcquireShared/tryReleaseShared。」

**AQS 架构三要素**：

```
┌─────────────────────────────────┐
│           AQS 骨架              │
│  ┌─────────┐  ┌──────────────┐ │
│  │  state   │  │  CLH 队列    │ │
│  │ (int)    │  │  Node(head)  │ │
│  │ 0:未持有 │  │   → Node    │ │
│  │ 1:已持有 │  │   → Node   │ │
│  │ >1:重入  │  │   → ...     │ │
│  └─────────┘  └──────────────┘ │
│  模板方法：                     │
│  acquire/release (独占)         │
│  acquireShared/releaseShared    │
│  (共享)                         │
└─────────────────────────────────┘
```

**acquire 核心流程**（独占模式）：tryAcquire 快速尝试获取 → 失败则 CAS 入队尾 → 前驱是 head 才 tryAcquire，否则 park 等待 → 被唤醒后继续自旋。

**release 流程**：tryRelease 减少 state → state==0 时唤醒 head 的下一个有效节点。

**共享模式**（Semaphore / CountDownLatch / ReadLock）：
- acquireShared：tryAcquireShared >= 0 成功；< 0 入队等待
- releaseShared：tryReleaseShared 返回 true → doReleaseShared 唤醒后继 → 传播唤醒（共享模式一个释放可唤醒多个等待者）

**面试话术：用 AQS 讲清 4 个 JUC 工具**：

| 工具 | AQS实现 | state 含义 | 模式 |
|------|---------|-----------|------|
| ReentrantLock | Sync→FairSync/NonfairSync | 0=未持有，1=已持有，>1=重入次数 | 独占 |
| Semaphore | Sync→FairSync/NonfairSync | 剩余许可数 | 共享 |
| CountDownLatch | Sync（只实现共享） | 剩余未countDown数 | 共享 |
| ReentrantReadWriteLock | 内部维护读锁(共享)+写锁(独占)，state 高16位=读锁计数，低16位=写锁重入 | 双模式 |

**追问：CLH 队列和原生 CLH 的区别？**
- 原生 CLH 自旋在前驱节点的状态字段上；AQS 变种中前驱是 head 时自旋，否则 park 阻塞，减少 CPU 空转。

**追问：公平锁 vs 非公平锁的吞吐量差异为什么大？**
- 非公平锁：刚释放锁的线程可能再次获取（线程还在 CPU 运行，缓存是热的），减少一次上下文切换
- 公平锁：释放后必须唤醒队列中第一个等待线程 → 上下文切换（保存/恢复寄存器、刷新 TLB 等）→ 开销远大于一次 CAS
- **面试金句**：非公平锁的性能优势来自减少上下文切换，代价是可能产生线程饥饿。默认选非公平，只有对公平性有明确要求的场景（如支付排队）才用公平锁。

**面试高手策略**：当面试官问「讲讲 ReentrantLock」时，不要只讲用法。用 2 分钟串起这条线：
> 「ReentrantLock 基于 AQS 的独占模式，state 记录重入次数。默认用非公平锁，因为刚释放锁的线程可能还在 CPU 上，直接重入可以省一次上下文切换。底层是 CLH 变种队列，前驱是 head 的节点自旋尝试获取，其他 park 等待。Condition 本质上是将 AQS 队列和条件队列做节点转移。」

### 2.6 ConcurrentHashMap

**面试话术（30秒版）**：
> 「JDK7 用 Segment 分段锁（默认 16 段，不可扩容），每个 Segment 继承 ReentrantLock。JDK8 改为 CAS + synchronized 锁桶头节点，粒度从 Segment 降到单个桶。put 时桶为空用 CAS 设置，桶非空 synchronized 锁头节点。扩容支持多线程协助 transfer。size() 用 CounterCell 分段计数 + baseCount，比 JDK7 的 3 次不加锁统计优雅很多。」

**JDK7 vs JDK8 对比表**：

| 维度 | JDK7 | JDK8 |
|------|------|------|
| 数据结构 | Segment 数组 + HashEntry 链表 | Node 数组 + 链表/红黑树 |
| 锁粒度 | Segment 级别（默认 16 并发） | 桶头节点级别 |
| 锁机制 | ReentrantLock | CAS + synchronized |
| 并发度 | 固定（构造函数指定） | 动态（桶数量 = 数组长度） |
| 扩容 | 单线程扩容 Segment 内 | **多线程协助扩容** |
| size | 先 2 次不加锁，失败后全局加锁 | baseCount + CounterCell[]（类似 LongAdder） |
| 红黑树 | 无（纯链表） | 链表长度 >=8 且数组 >=64 时树化 |

**为什么 JDK8 用 synchronized 而不是 ReentrantLock？**（高频追问）
1. JDK8 对 synchronized 增加了锁升级优化（偏向→轻量级→重量级），低竞争时性能极好
2. synchronized 基于 JVM 实现，可以做更多 JIT 优化（锁消除/锁粗化/逃逸分析）
3. 大量内存碎片的场景下，ReentrantLock 创建的 AQS Node 对象可能导致 GC 压力
4. synchronized 代码更简洁，自动释放

**扩容机制（transfer）**：
1. 扩容时数组大小翻倍（2 的幂）
2. 多线程协助：每个线程用 CAS 领取 transferIndex 区间（stride 步长）
3. 节点迁移：原位置 i 或 i+n（n=原数组长度），因为 hash 多了一位（巧妙利用了 2 的幂）
4. 迁移中的桶加 ForwardingNode 标记（hash = MOVED = -1），读操作在此期间访问新数组
5. 最后一个完成 transfer 的线程负责检查并设置新数组

**追问：size() 怎么实现的？**
- JDK7：先不加锁 sum 2 次，如果连续 2 次结果相同返回，否则全局加锁 → 性能差
- JDK8：baseCount（无竞争时 CAS 更新） + CounterCell[]（有竞争时分段计数）
  - addCount 时：先 CAS baseCount，失败则发到 CounterCell（ThreadLocalRandom 探针定位 Cell）
  - size() 时：baseCount + sum(CounterCell) — 但这不是精确值，是**快照**，可能不准确
  - 面试时说：「不是精确值，是近似快照，符合 size() 的弱一致性语义设计」

**树化与退化**：
- 树化条件：链表长度 >= 8 **且** 数组长度 >= 64（链表短时优先扩容而非树化）
- 退化条件：树节点数 <= 6 时退化为链表
- 为什么阈值是 8：hash 离散良好的情况下链表长度为 8 的概率 < 千万分之一（泊松分布），大部分桶不会触发树化

### 2.7 ThreadLocal

**面试话术（30秒版）**：
> 「每个 Thread 内部维护一个 ThreadLocalMap，key 是 ThreadLocal 的弱引用，value 是我们存的值。key 用弱引用是为了在外部没有强引用时让 ThreadLocal 对象被 GC 回收，但 value 是强引用。线程池场景下线程复用，如果不用 remove()，key 被回收但 value 未清除，就会内存泄漏。最佳实践：finally 中调用 remove()。阿里开源的 TransmittableThreadLocal 解决了线程池场景的上下文传递问题。」

**内部结构与内存泄漏**：

```
Thread
  └── ThreadLocalMap (内部类)
        └── Entry[] (table)
              └── Entry extends WeakReference<ThreadLocal<?>>
                    ├── key: 弱引用指向 ThreadLocal 对象（可被 GC）
                    └── value: 强引用（不会被 GC）
```

**内存泄漏链路**：
1. 外部 ThreadLocal 强引用被置为 null → ThreadLocal 对象只有 ThreadLocalMap 中的弱引用
2. GC 回收 ThreadLocal 对象 → Entry 的 key 变为 null
3. value 仍被 Entry 强引用 → 只要线程存活，value 就不会被 GC → 内存泄漏
4. ThreadLocal 的 get/set/remove 会触发**启发式清理**（探测 null key 的 Entry 并清除），但不是 100% 可靠

**追问：ThreadLocal 的实际应用场景？**
- Spring 事务管理：TransactionSynchronizationManager 用 ThreadLocal 绑定数据库连接
- 链路追踪：TraceId 的传递（MDC 底层是 ThreadLocal）
- 线程级上下文隔离：用户登录信息、Request 上下文
- 日期格式化：SimpleDateFormat 线程不安全，用 ThreadLocal 给每个线程一个副本

**追问：InheritableThreadLocal 和 TransmittableThreadLocal 的区别？**
- InheritableThreadLocal：子线程创建时（new Thread）拷贝父线程值，**线程池复用场景失效**
- TransmittableThreadLocal（阿里 TTL）：在线程池的 submit/execute 时自动捕获上下文并在任务执行前设置，解决了线程池场景的核心痛点
- 面试金句：用 InheritableThreadLocal 的场景很少，生产环境基本都上 TTL

### 2.8 线程池

**面试话术（30秒版）**：
> 「线程池核心参数 7 个：corePoolSize、maxPoolSize、keepAliveTime、unit、workQueue、threadFactory、rejectedExecutionHandler。提交流程：先看核心线程是否满了 → 不满就创建核心线程，满了就入队 → 队满了看最大线程是否满了 → 不满创建非核心线程，满了就执行拒绝策略。动态线程池是加分亮点——运行时调整 core/max 参数，加上队列积压监控和水位线告警。」

**任务提交流程图**：

```
                    submit(task)
                         │
                         ▼
              corePoolSize 满了？
              ├─ 否 → 创建核心线程（即使有空闲线程）
              │
              └─ 是 → workQueue 满了？
                        ├─ 否 → 入队等待
                        │
                        └─ 是 → maxPoolSize 满了？
                                  ├─ 否 → 创建非核心线程
                                  │
                                  └─ 是 → 执行拒绝策略
```

**追问：核心线程数怎么定？**
- CPU 密集型：N+1（N = CPU 核数）
- IO 密集型：2N 或 N * (1 + 阻塞时间/计算时间)
- **架构师认知**：公式只是起点，真正的参数要**压测后确定**。先设定初值，逐步加压观察 CPU、RT、吞吐量曲线，找到拐点。最重要的是要可观测（监控线程池运行状态）。

**4 种拒绝策略**：

| 策略 | 行为 | 适用 |
|------|------|------|
| AbortPolicy（默认） | 抛 RejectedExecutionException | 需要感知拒绝的场景 |
| CallerRunsPolicy | 由调用方线程执行任务 | 不能丢任务，可借调压力反馈 |
| DiscardPolicy | 静默丢弃 | 允许丢的非核心任务 |
| DiscardOldestPolicy | 丢弃队列头部最旧的任务 | 优先处理最新任务 |

**动态线程池（加分亮点）**：

实施要点：
1. corePoolSize/maxPoolSize 运行时 set 生效（ThreadPoolExecutor 本身就支持）
2. 监控指标：当前线程数/活跃线程数/队列大小/已完成任务数/拒绝次数
3. 队列积压告警：队列大小 > 阈值 → 告警 → 人工或自动扩容
4. 水位线：安全水位（<50%）、预警水位（50-80%）、危险水位（>80%）

面试时说：
> 「线程池参数不是一成不变的。我主导搭建过动态线程池，核心是在线程池运行时采集指标做可视化，设置三级水位线告警。当队列积压超过预警水位时，自动或手动调大 maxPoolSize。同时利用 Sentinel 的线程池隔离能力，关键业务用独立线程池隔离。」

**追问：线程池 OOM 怎么排查？**
- 如果是堆 OOM：可能是无界队列（LinkedBlockingQueue 默认 Integer.MAX_VALUE）→ 改用有界队列
- 如果是线程数 OOM：maxPoolSize 没上限或不合理 → 限制最大线程数
- 典型错误：**Executors.newCachedThreadPool()** — maxPoolSize = Integer.MAX_VALUE，SynchronousQueue + 无上限线程 → 并发请求一多直接 OOM
- 面试金句：**《阿里巴巴开发手册》禁止用 Executors 创建线程池，必须用 ThreadPoolExecutor 显式指定参数**

### 2.9 CompletableFuture（高频加分项）

**面试话术（30秒版）**：
> 「CompletableFuture 是 JDK8 的异步编程核心，解决了 Future 的三大痛点：阻塞 get()、无法链式串联、异常处理割裂。核心方法是 thenApply（转换）、thenCompose（串联另一个异步任务）、thenCombine（合并两个结果）。默认用 ForkJoinPool.commonPool()，但**生产必须自定义线程池**隔离，避免阻塞任务占满公共池。」

**核心方法区分**（最多被问的两个）：

| 方法 | 输入 | 返回 | 类比 |
|------|------|------|------|
| `thenApply(Function)` | T → U | `CompletableFuture<U>` | map |
| `thenCompose(Function)` | T → `CompletableFuture<U>` | `CompletableFuture<U>` | flatMap |
| `thenCombine(other, BiFunction)` | 两个结果 → V | `CompletableFuture<V>` | zip |
| `thenAccept(Consumer)` | T → void | `CompletableFuture<Void>` | forEach |

**异常处理三兄弟**：

| 方法 | 能恢复吗 | 能获取正常结果吗 |
|------|---------|----------------|
| `exceptionally(Function)` | 能（返回默认值） | 不经过 |
| `whenComplete(BiConsumer)` | 不能 | **能**（result 和 ex 都传进来） |
| `handle(BiFunction)` | 能 | **能**（result 和 ex 都传进来） |

**面试追问：CompletableFuture 默认线程池是什么？有什么坑？**
- 默认是 `ForkJoinPool.commonPool()`，JDK8 默认线程数 = CPU 核数 - 1
- 如果有阻塞操作（数据库调用/HTTP 请求）跑在 commonPool 上，会把公共池线程全占满 → 其他 CompletableFuture、parallelStream 全部阻塞
- 解决方案：自定义线程池 `CompletableFuture.supplyAsync(() -> ..., executor)`

### 2.10 HashMap（附加高频考点）

**面试话术（30秒版）**：
> 「JDK7 数组+链表，头插法，并发扩容时可能产生环形链表导致死循环。JDK8 改成数组+链表+红黑树，尾插法，但并发 put 仍有数据覆盖风险。扩容后元素位置在原位置或原位置+oldCap，因为利用了高位 bit 的巧妙计算。树化阈值 8，退化阈值 6，中间差值缓冲防止反复树化和退化。」

**JDK7 vs JDK8 关键差异**：

| 维度 | JDK7 | JDK8 |
|------|------|------|
| 结构 | 数组 + 链表 | 数组 + 链表 + 红黑树 |
| 插入方式 | 头插法（并发死循环） | 尾插法 |
| hash扰动 | 4次移位异或 | 高16位异或低16位（1次） |
| 扩容计算 | rehash（重新计算位置） | hash & oldCap → 原位置或+oldCap |
| 扩容时机 | 先扩容再插入 | 先插入再扩容 |
| 为什么不用AVL | — | 红黑树插入最多旋转3次，AVL要logN次 |

**扩容机制深度**：
- 容量始终保持 2 的幂（为了 index = hash & (n-1) 的高效取模）
- loadFactor 默认 0.75：泊松分布和空间利用率的最优折衷
- JDK8 扩容后位置计算：hash & oldCap == 0 → 原位置；!= 0 → 原位置 + oldCap。不需要重新 hash

**追问：为什么转红黑树的阈值是 8？**
- 根据泊松分布，hash离散良好时链表长度达到8的概率约 0.00000006（< 千万分之一）
- 8 是一个极低概率的事件阈值，触发树化说明 hash 冲突严重，需要提升查询效率

**追问：为什么退化阈值是 6 而不是 7？**
- 留一个缓冲区间（7），防止元素数量在 7-8 之间反复增删导致频繁的树化/退化（性能开销）

**追问：HashMap 线程不安全的具体表现？**
- JDK7：并发 rehash 可能形成环形链表 → 下次 get 时死循环（CPU 100%）
- JDK8：尾插法解决环形链表，但并发 put 可能造成数据覆盖（两个线程同时 put 到同一个桶，互相覆盖）
- 结论：HashMap 在任何 JDK 版本都不是线程安全的，多线程场景用 ConcurrentHashMap

---

## 三、Spring Framework 深度原理（P0）

> Java 工程师不能只会用 Spring Boot Starter。面试官期待你能讲出 IOC 容器怎么初始化的、AOP 底层是怎么织入的、循环依赖怎么解决的。

### 3.1 IOC 容器

**面试话术（30秒版）**：
> 「Spring IOC 容器的初始化核心在 AbstractApplicationContext.refresh() 方法，13 个步骤。其中最关键的三步：obtainFreshBeanFactory（加载 BeanDefinition）、invokeBeanFactoryPostProcessors（执行 BeanFactory 后置处理器，如解析 @Configuration 和 @ComponentScan）、finishBeanFactoryInitialization（实例化所有非懒加载单例 Bean）。BeanFactory 是底层容器接口，ApplicationContext 在其基础上增加了事件发布、国际化等能力。」

**refresh() 核心步骤**（不背 13 步，记关键节点）：

| 步骤 | 方法 | 做了啥 |
|------|------|--------|
| 1 | obtainFreshBeanFactory | 解析 XML/注解，加载所有 BeanDefinition 到容器 |
| 2 | invokeBeanFactoryPostProcessors | 执行 BeanFactoryPostProcessor（如 ConfigurationClassPostProcessor 解析 @Configuration） |
| 3 | registerBeanPostProcessors | 注册 BeanPostProcessor（AOP 的代理创建靠这个时机注册的处理器） |
| 4 | finishBeanFactoryInitialization | **单例 Bean 的实例化入口**（非懒加载的都在这里完成） |

**追问：BeanFactory 和 ApplicationContext 的区别？**
- BeanFactory：懒加载，访问时才创建 Bean，是 Spring 最底层的 IoC 容器
- ApplicationContext：启动时预初始化所有非懒加载单例 Bean，增加了国际化/事件发布/资源加载等
- **选型**：基本上都用 ApplicationContext，只有资源极端受限（如 Applet/移动端）才考虑 BeanFactory

**追问：BeanFactoryPostProcessor 和 BeanPostProcessor 的区别？**
- BeanFactoryPostProcessor：操作 BeanDefinition（修改 Bean 元数据），在 Bean 实例化之前执行
- BeanPostProcessor：操作 Bean 实例（生成代理、属性赋值），在 Bean 初始化前后执行
- 记忆：一个有 Factory（管定义的），一个没 Factory（管实例的）

### 3.2 AOP 原理

**面试话术（30秒版）**：
> 「Spring AOP 默认用 JDK 动态代理和 CGLIB 两种方式。有接口用 JDK 动态代理（基于反射，创建实现接口的代理类），无接口用 CGLIB（基于继承，生成目标类的子类）。Spring Boot 2.x 后默认改为 CGLIB（因为注解驱动的开发模式代理目标类更常见）。JDK 代理通过 Proxy.newProxyInstance + InvocationHandler 实现，CGLIB 通过 Enhancer + MethodInterceptor 实现。」

**JDK 动态代理 vs CGLIB**：

| 维度 | JDK 动态代理 | CGLIB |
|------|-------------|-------|
| 机制 | 反射，运行时生成实现接口的代理类 | ASM 字节码操作，生成目标类的子类 |
| 前提 | 必须有接口 | 目标类不能是 final，方法不能是 final |
| 性能 | 创建快，执行略慢（反射） | 创建慢（字节码生成），执行快（直接调用） |
| Spring 默认 | Spring Boot 1.x | Spring Boot 2.x+（统一用 CGLIB） |
| 典型场景 | 基于接口的 Service 代理 | @Transactional 等注解切面 |

**追问：AspectJ 和 Spring AOP 的区别？**
- AspectJ：编译期/类加载期织入（LTW），功能完整，不依赖代理，需要特殊编译器
- Spring AOP：运行时织入（JDK/CGLIB 代理），只能拦截 Spring Bean 的方法，内部调用不触发（this.xxx() 不走代理）
- 面试金句：「Spring AOP 是轻量级 AOP 实现，覆盖 90% 场景。特殊需求如非 Spring Bean 的拦截、构造器切入、内部调用拦截，上 AspectJ LTW。」

**追问：事务失效的几种场景？**（高频）

| 场景 | 原因 |
|------|------|
| 方法非 public | CGLIB/JDK代理无法拦截非public方法 |
| 同类内部调用 | this.method() 不经过代理 → AOP 不生效 |
| 异常被 catch 了 | @Transactional 只对 RuntimeException/Error 回滚 |
| rollbackFor 未指定 | 受检异常默认不回滚 |
| 数据源没有事务管理器 | 多数据源场景配错 TransactionManager |
| 事务传播行为误配 | Propagation.NOT_SUPPORTED 会挂起当前事务 |

**面试话术**：
> 「最常见的失效场景是同类内部调用——this.xxx() 直接调用不走代理。解决方案有三种：一是把方法拆到另一个 Bean；二是注入自己（self-injection）；三是通过 AopContext.currentProxy() 获取当前代理对象再调用。」

### 3.3 循环依赖

**面试话术（30秒版）**：
> 「Spring 解决循环依赖靠**三级缓存**：singletonObjects（一级，成品 Bean）、earlySingletonObjects（二级，早期暴露的 Bean 引用）、singletonFactories（三级，ObjectFactory 可生成代理对象）。A 依赖 B，B 依赖 A：A 先实例化 → 把自己放入三级缓存 → 发现依赖 B → 创建 B → B 发现依赖 A → 从三级缓存获取 A 的引用 → B 创建完成 → A 注入 B → A 创建完成。核心：**提前暴露未完成的 Bean 引用，打破循环。**」

**三级缓存**：

| 缓存 | Map 名称 | 存什么 | 时机 |
|------|----------|--------|------|
| 一级 | singletonObjects | 完全初始化好的 Bean | Bean 创建完成 |
| 二级 | earlySingletonObjects | 早期引用（可能已生成代理） | 从三级缓存获取后升级到二级 |
| 三级 | singletonFactories | ObjectFactory（生成代理对象的工厂） | 实例化后、属性填充前放入 |

**关键追问**：

*「为什么需要三级缓存？两级不行吗？」*
- 两级缓存（singletonObjects + earlySingletonObjects）在**不需要 AOP 代理**的场景就够了
- 但如果有 AOP 代理：B 拿到 A 的引用时，A 此时还没完成初始化（BeanPostProcessor 还没执行），如果 B 持有的 A 不是代理对象，后续 A 生成代理后，B 持有的 A 就不是代理 → **状态不一致**
- 三级缓存的 singletonFactories 返回的可以是代理对象（通过 getEarlyBeanReference），在循环依赖场景下提前生成代理

*「构造器注入为什么不能解决循环依赖？」*
- Spring 解决循环依赖的前提是：**实例化 + 属性填充分离**（先用无参构造实例化，再填充属性）
- 构造器注入要求创建时必须提供依赖对象，而依赖对象又依赖当前对象 → 死锁
- 本质原因：三级缓存是在实例化完成但属性未填充时放入的，构造器注入没有这个「中间态」

*「哪些循环依赖 Spring 解决不了？」*
- 构造器注入的循环依赖（无法进入三级缓存的中间态）
- prototype 作用域的循环依赖（prototype 不会走三级缓存）
- @Async 注解的循环依赖（提前生成的代理对象类型不匹配）

### 3.4 Bean 生命周期

**面试话术（30秒版）**：
> 「Spring Bean 生命周期按三阶段记：出生（实例化，反射调构造方法）、长大（属性赋值 + Aware 回调 + @PostConstruct + InitializingBean + init-method）、成年（BeanPostProcessor 后置处理，AOP 代理在这里生成，最终放入 singletonObjects）。销毁时：@PreDestroy → DisposableBean.destroy → destroy-method。」

**核心流程**（精简版）：

```
1. 实例化 (createBeanInstance)
     └── 反射调构造方法（或工厂方法）创建对象
2. 属性填充 (populateBean)
     └── @Autowired/@Value 注入 + 依赖解析
3. 前置处理 (BeanPostProcessor.postProcessBeforeInitialization)
     └── @PostConstruct 在这里执行（CommonAnnotationBeanPostProcessor）
4. 初始化 (InitializingBean.afterPropertiesSet + init-method)
5. 后置处理 (BeanPostProcessor.postProcessAfterInitialization)
     └── ★ AOP 代理对象生成在这里（AbstractAutoProxyCreator）
6. 就绪（放入 singletonObjects）
7. 销毁 (@PreDestroy + DisposableBean.destroy + destroy-method)
```

**追问：@PostConstruct 和 InitializingBean 和 init-method 的执行顺序？**
- @PostConstruct → InitializingBean.afterPropertiesSet() → init-method
- 为什么是这个顺序：@PostConstruct 由 CommonAnnotationBeanPostProcessor 处理（在 before 阶段），afterPropertiesSet 和 init-method 由 AbstractAutowireCapableBeanFactory.invokeInitMethods 调用

**追问：FactoryBean 和 BeanFactory 的区别？**
- BeanFactory：IOC 容器，管理 Bean 的工厂
- FactoryBean：生产 Bean 的 Bean，getObject() 返回的才是最终 Bean。MyBatis 的 SqlSessionFactoryBean 就是典型
- 面试时说："FactoryBean 是解决复杂 Bean 创建的模式。MyBatis 的 SqlSessionFactoryBean 是典型——getObject() 返回的是 SqlSessionFactory 实例而非 FactoryBean 本身。默认 isSingleton()=true，getObject() 只调用一次；覆盖为 false 则每次返回不同实例。"

### 3.5 事务传播行为

**面试话术（30秒版）**：
> 「事务传播行为定义了事务方法之间嵌套时的行为策略。掌握 3 个最常见的就够了：REQUIRED（默认，有则用，无则建）适用于增删改但需要加入已有事务的场景。REQUIRES_NEW（挂起当前，新建事务）适用于独立记录日志、发送消息等不能回滚的操作。NESTED（嵌套子事务，savepoint 回滚）适用于批量处理中部分失败部分成功。REQUIRED > REQUIRES_NEW > NESTED 的选择顺序就是多数场景的需求优先级。」

**核心传播行为表**：

| 传播行为 | 当前有事务 | 当前无事务 | 典型场景 |
|----------|-----------|-----------|---------|
| **REQUIRED**（默认） | 加入 | 新建 | 增删改操作 |
| **REQUIRES_NEW** | 挂起当前→新建 | 新建 | 日志记录、发MQ消息（独立提交） |
| **NESTED** | 嵌套子事务（savepoint） | 新建 | 批量处理（部分失败不全部回滚） |
| SUPPORTS | 加入 | 无事务执行 | 读操作 |
| NOT_SUPPORTED | 挂起→无事务 | 无事务执行 | 不需要事务的操作 |
| MANDATORY | 加入 | 抛异常 | 强制要求调用方开启事务 |
| NEVER | 抛异常 | 无事务执行 | 强制无事务环境 |

**追问：REQUIRES_NEW 和 NESTED 的区别？**（高频）
- REQUIRES_NEW：完全独立的事务，提交回滚互不影响。外部事务回滚不影响内部，内部回滚也不影响外部
- NESTED：子事务通过 savepoint 回滚，外部事务回滚会连带子事务一起回滚
- 底层区别：REQUIRES_NEW 用的是独立数据库连接，NESTED 用的是 savepoint 机制
- **选型**：日志审计场景 REQUIRES_NEW（不管业务事务成败都得记录）；批量操作中批量项独立提交用 NESTED（外部失败会全回滚）

**追问：事务失效的场景？**（结合 3.2 AOP）
- 除了 AOP 的 6 种失效场景外，传播行为本身也可能导致「看起来失效」
- 比如：默认 REQUIRED 下，内部方法抛异常被 catch 了，框架不知道有异常所以不回滚 → 不是框架的 bug，是使用方式的问题
- 再比如：REQUIRES_NEW 在同类内部调用时，不会走代理，实际上还是用的同一个事务

---

## 四、微服务体系核心（P0）

### Spring Cloud 核心链路

```
Gateway（鉴权+限流+路由）→ Nacos（服务发现+配置）→ Sentinel（熔断降级）→ 微服务
```

每个节点准备一个异常场景的应对，而不是背配置参数。

**Gateway**：全局 Filter 设计（鉴权→日志→限流→灰度），Filter 执行顺序。**架构师层面**：API 网关选型（SCG vs Kong vs APISIX），什么时候需要独立网关、什么时候 SCG 就够了。

**Nacos**：
- 一致性取舍：临时实例（AP，自动剔除）vs 永久实例（CP，手动上下线），微服务用临时实例
- 配置中心长轮询：hold 连接 30s，有变更立即返回，无变更超时返回 304
- 注册中心挂了影响：已有本地缓存的服务不受影响，新启动的服务无法注册

**Sentinel**：
- 流控模式（直接/关联/链路）按业务场景选
- 熔断：慢调用比例（核心接口）vs 异常比例（明确异常）vs 异常数（低流量）
- 规则持久化到 Nacos，不依赖 Dashboard

### 分布式事务

| 方案 | 核心 | 适用 |
|------|------|------|
| Seata AT | undolog 自动回滚 | 一致性要求高、业务简单 |
| TCC | Try/Confirm/Cancel 三阶段 | 有资源锁定需求 |
| 最终一致性 | 本地消息表 + MQ + 定时补偿 + 对账 | **最常用** |
| Saga | 正向+逆向补偿编排 | 长事务链路 |

**TCC 三个异常场景**：
- 空回滚：Cancel 比 Try 先到（网络延迟或提前触发）→ 查操作流水，没有 Try 记录直接返回成功。核心：Cancel 不能因为没有 Try 就报错
- 防悬挂：Cancel 执行完后 Try 才到（Try 因网络延迟晚到）→ 检查有 Cancel 标记，拒绝执行 Try。核心：留空不等于可以拿
- 幂等：Try 因超时重试 → 唯一键（如 order_id + operation_type）防重。Confirm/Cancel 同样需要支持幂等

**下单场景 TCC 示例**：
- Try：冻结库存（预留，不是扣减）+ 创建预下单记录（状态=冻结中）
- Confirm：扣减冻结库存（真正减掉）→ 订单状态改为已确认
- Cancel：解冻库存（加回可用）→ 预下单状态改为已取消

**Seata AT 原理**：代理数据源，拦截 SQL → 解析前后镜像（UNDO_LOG）。一阶段分支事务提交并记录 UNDO_LOG；二阶段全局提交则异步删除 UNDO_LOG，全局回滚则根据前镜像生成补偿 SQL 一次性回滚。优点无侵入（业务代码零改动），缺点性能开销（前后镜像+全局锁）。

**选型核心**：大部分场景最终一致性就够了。最终一致性的落地关键：本地消息表 + MQ 发送 + 定时扫表补偿 + T+1 对账兜底。AT/TCC 的一致性收益要大于侵入性代价才值得用。高层次认知：好的架构设计应该通过业务边界划分和状态机设计来避免分布式事务，而不是引入更复杂的框架来处理它。

### 分布式锁

**Redis 分布式锁三层递进**：

| 层次 | 方案 | 特点 |
|------|------|------|
| 单实例 | `SET NX` + 过期时间 | 基础方案，进程 crash 锁丢失 |
| 看门狗 | Redisson（默认30s，每10s续期） | 解决锁提前过期问题 |
| 多节点 | **Redlock**（N 个独立 Redis，过半加锁成功） | 解决单点故障，但有争议 |

**Redlock 争议**（面试加分项）：Martin Kleppmann（DDIA 作者）指出 Redlock 依赖时钟同步假设——如果某个 Redis 节点时钟发生跳变，锁的安全性会被破坏。Redis 作者 Antirez 回应称时钟跳变概率极低且可通过 fencing token 兜底。工程中选择 Redisson 单实例 + 业务幂等兜底即可，真的需要强一致性用 ZK/etcd。

- 选型：性能优先用 Redis（默认选），一致性优先用 ZK（金融场景），K8s 生态用 etcd
- 兜底：锁只是性能优化，业务层 DB 唯一索引才是最后防线

### 线程池 & 并发（微服务场景）

- 参数设定：按压测结果调，不要只背公式
- **动态线程池**（加分亮点）：运行时调整 + 队列积压告警 + 水位线
- CompletableFuture 编排：thenApply/thenCombine/exceptionally，自定义线程池隔离

### 灰度发布

**面试话术**：
> 「灰度发布的核心是标签路由：在请求头或用户 ID 上打标，网关根据标签将流量路由到灰度服务实例。Nacos 元数据 + Spring Cloud LoadBalancer 可以实现：灰度实例打 version=canary 标签，网关/Feign 拦截器读请求标签→匹配对应版本的服务实例。发布流程：摘除实例→更新→验证→扩大灰度比例→全量。金丝雀发布的基本节奏：5%→观测→30%→观测→100%。」

关键要素：
- 标签路由：用户维度（userId hash）/ 请求头维度（x-version: canary）
- 注册中心元数据：Nacos 实例级别 metadata，LoadBalancer 根据元数据筛选
- 可观测：灰度实例的日志/指标必须能单独查看，快速判定异常
- 回滚：灰度期间出问题直接切回老版本实例，比数据库回滚快得多

### 全链路压测

**面试话术**：
> 「全链路压测的核心是流量染色+影子库。在请求头打压测标记（如 x-stress-test: true），中间件链路透传该标记。影子库的关键：MySQL 用影子表（同库不同表前缀）或影子库（独立库），Redis 用影子 key（加前缀区分），MQ 用影子 topic。核心难点不在工具，在于全链路透传和影子数据的隔离完备性。」

一句话：流量染色让压测流量走完整链路但不污染生产数据。

### 链路追踪（SkyWalking）

**面试话术**：
> 「SkyWalking 核心概念：Trace（一次完整请求链路，用全局 TraceId 串联）、Span（链路中的单个操作节点，如 HTTP 请求/DB 调用/MQ 发送）、上下文传播（通过 HTTP Header/MQ 元数据传递 TraceId + SpanId）。Java Agent 字节码增强自动埋点，对业务代码零侵入。排查问题时从一个慢 Trace 钻取到具体 Span，定位到具体的 SQL/接口调用。」

### Dubbo 核心

**Dubbo vs Spring Cloud 选型**：
- Dubbo：RPC 框架（服务间调用），单一长连接+Netty+NIO，序列化效率高，性能更强
- Spring Cloud：微服务全家桶，生态更全（Gateway+Config+Security），但 HTTP 协议开销大
- 实际项目可以混用：Dubbo 做 RPC 调用，Nacos 做服务发现，Sentinel 做熔断

**协议模型**：
- dubbo 协议（2.x 默认）：单一长连接+NIO+异步，适合小数据量高并发
- **Triple 协议（Dubbo 3.x）**：基于 gRPC，兼容 gRPC 生态，支持流式调用（Server Stream/Client Stream/Bidirectional Stream），适合云原生和跨语言场景

> **版本提示**：Dubbo 3.x 除 Triple 协议外，还引入了**应用级服务发现**（从接口级注册改为应用级，降低注册中心压力）和 Proxyless Service Mesh 支持。面试时主动提 3.x 演进是加分项。

**调用链路（一次完整 RPC）**：
```
Proxy → Cluster → LoadBalance → Filter Chain → Protocol → Exchanger → Transporter
```
- Proxy：代理层，封装调用细节；Cluster：集群容错（failover/failfast）；LoadBalance：负载均衡；Filter Chain：责任链（监控/鉴权/限流）；Protocol：协议层编解码；Exchanger：请求响应映射；Transporter：Netty 网络传输

**SPI 扩展机制**：
- JDK SPI：破坏性加载，一次性实例化所有实现（如所有 JDBC 驱动）
- Dubbo SPI：key-value 方式按需加载，`@SPI` 指定默认实现，`@Adaptive` 自动生成适配类，`ExtensionLoader.getExtensionLoader()` 获取扩展
- 这是 Dubbo 可插拔设计的灵魂——协议、注册中心、负载均衡、序列化全部通过 SPI 切换

**负载均衡**：
- Random：加权随机，默认
- RoundRobin：平滑加权轮询（Nginx 同款）
- LeastActive：选活跃数最小的节点（消费者本地计数器）
- ConsistentHash：相同参数到同一节点
- 预热权重：刚启动权重从 0 缓慢升到设定值，避免冷启动被压垮

**优雅下线**：
1. 注册中心摘除（不再接收新请求）
2. 等待已接收请求处理完
3. 协议层关闭（`dubbo.service.shutdown.wait`，默认 10s）
4. Netty 关闭
- K8s 场景需配合 `terminationGracePeriodSeconds`，确保 preStop hook 到 SIGTERM 之间留够时间

**服务治理**：
- 分组与版本：`group` 区分环境（dev/test/prod），`version` 做灰度路由
- 服务降级：`mock=force:return null` 强制降级，`mock=fail:return null` 失败后降级
- 本地存根（Stub）：消费者端在执行远程调用前后的拦截逻辑，可做参数验证/缓存等
- 路由规则：条件路由按参数/标签路由流量，实现灰度发布

---

## P1：高频深度（面试大概率追问的部分）

---

## 五、中台架构设计（P1 补充）

> 中台的本质不是「把所有业务逻辑收上来」，而是**识别可复用的能力并抽象**。面试考察的是你对「复用 vs 扩展」的平衡感和对「中台厚薄」的判断力。

### 5.1 中台三明治能力分层

**面试话术（30秒版）**：
> 「中台的建设我按三明治模型来做：底层是基础数据层，把各业务线的数据做统一建模，只提供只读查询能力不写业务数据；中间是通用能力层，把可复用的逻辑通过 SPI 暴露扩展点，业务线按自己的需求接入；顶层是业务流程编排层，用配置化 + 轻量流程引擎串联步骤，业务方配规则而不是写代码。」

| 层级 | 职责 | 关键设计 |
|------|------|---------|
| 基础数据层 | 统一数据模型（SPU/SKU/类目/属性），只提供只读查询 | 不写业务数据，数据主权在业务方 |
| 通用能力层 | SPI 扩展点 + 泛化调用，可复用逻辑收归中台 | 中台提供能力壳，业务方填实现 |
| 业务流程编排层 | 配置化规则 + 流程引擎串联步骤 | 业务方配规则，不写代码 |

### 5.2 复用 vs 扩展：SPI + 泛化调用 + 配置化

**面试话术（30秒版）**：
> 「复用和扩展是一体两面。核心原则是：通用流程归中台，具体实现归业务方。技术上用 SPI 接口定义能力契约，业务方提供实现类注册进来；泛化调用让中台不需要依赖业务方的 JAR 包就能调用；配置化让业务方通过配置中心动态调整行为，而不是硬编码 if-else。」

核心公式：**SPI 定义能力 + 泛化调用解耦依赖 + 配置化控制行为**

| 机制 | 解决的问题 | 类比 |
|------|-----------|------|
| SPI 扩展点 | 中台不写死业务逻辑，支持多业务线差异化接入 | JDK SPI / Dubbo SPI |
| 泛化调用 | 中台不依赖业务方的 JAR 包，运行时动态调用 | Dubbo 泛化调用 |
| 配置化 | 业务方通过配置中心改规则，不发布代码 | Nacos/Apollo 配置驱动 |

### 5.3 多业务线冲突兼容：策略模式 + 配置映射表

**面试话术（30秒版）**：
> 「多业务线在中台共用一个能力时，最容易出现的坑是写一堆 if (bizType == 'A') else if (bizType == 'B')。我的做法是用策略模式 + 配置映射表——业务类型与策略实现类的映射关系存在配置中心，中台根据业务标识动态路由到对应的策略实现，新增业务线时中台代码无需改动。」

| 错误做法 | 正确做法 |
|---------|---------|
| if/else 硬编码业务分支 | 策略模式 + 配置映射表 |
| 每接一个新业务线改中台代码 | 业务方提供 SPI 实现 + 配置中心注册 |
| 中台替业务方做决策 | 中台提供能力，业务方定义规则 |

### 5.4 商品中心举例

**面试话术（30秒版）**：
> 「商品中心对外的服务间 API 只提供查询能力——SPU/SKU 查询和类目树。为什么？因为新增修改删除走的是商品管理后台，不是给订单服务、营销服务调的。中台的核心理念是：写操作通过管理后台统一入口，查询能力通过 API 开放给各业务方复用。」

| 能力 | 中台侧 | 说明 |
|------|--------|------|
| SPU/SKU 查询 | 统一数据模型 + 标准化查询 API | 各业务线通过 API 查商品详情 |
| 类目树 | 统一类目管理 | 所有业务线复用同一套类目结构 |
| 属性模板 | 通用属性（品牌/规格）统一维护 | 行业特有属性由业务方扩展 |
| 写操作 | 走商品管理后台 | 不向订单/营销等服务开放写 API |

### 5.5 中台做得太厚或太薄的问题

**面试话术（30秒版）**：
> 「中台两个极端坑：太厚——业务逻辑全收，团队成瓶颈，本质是集中式单体；太薄——只给工具类，业务方不买账。判断标准：沉淀的是领域能力还是代码片段？前者值得做，后者只是仓库。」

| 问题 | 表现 | 根因 |
|------|------|------|
| 中台太厚 | 中台团队成瓶颈，业务方排队等排期 | 把中台当业务系统做，收太多写逻辑 |
| 中台太薄 | 业务方不买账，觉得中台没价值 | 只做工具/组件，没沉淀领域能力 |
| 合适的分寸 | 中台提供能力 + 业务方自助接入 | 能力抽象 + SPI扩展 + 配置化 |

判断要不要进中台的标准：**这个能力被 ≥ 2 个业务线需要，并且变化频率低（接口稳定），就可以进中台。只有一条业务线用的、或者天天改的东西，不放进中台。**

---

## 六、MySQL 深度（P1）

### 6.1 索引原理

**面试话术（30秒版）**：
> 「InnoDB 索引底层是 B+ 树，所有数据存在叶子节点，非叶子节点只存索引键。B+ 树相比 B 树的优势：叶子节点双向链表支持范围查询，非叶子节点不存数据使得单个节点能存更多索引 → 树更矮 → IO 次数更少。InnoDB 的主键索引是聚簇索引（叶子节点存完整行数据），二级索引叶子节点存主键值，所以二级索引查询需要回表。」

**B+ 树 vs B 树 vs 哈希索引**：

| 维度 | B+ 树 | B 树 | 哈希 |
|------|-------|------|------|
| 叶子节点 | 存完整数据 + 双向链表 | 非叶节点也存数据 | 数组+链表 |
| 范围查询 | 叶子链表直接遍历（优） | 需要中序遍历 | 不支持 |
| 等值查询 | logN | logN | O(1)（冲突少时） |
| 排序 | 叶子有序，天然支持 | 中序遍历 | 无序 |
| 磁盘IO | 少（树矮） | 较多 | 无（内存结构） |

**追问：为什么 InnoDB 用 B+ 树不用跳表（SkipList）？**
- B+ 树是为磁盘 IO 设计的：节点大小通常等于一个磁盘页（16KB），一次 IO 读取一个节点
- 跳表是为内存设计的：leveldb/Redis zset 用跳表，因为完全在内存中
- 跳表层级是概率性的，不能精确控制磁盘 IO 次数

**覆盖索引**：查询列全在索引中 → 不需要回表（Using index）。**最左前缀原则**：联合索引 (a,b,c)，查询条件必须从 a 开始匹配（a、a+b、a+b+c 走索引；b+c 不走）。

**追问：联合索引 (a,b,c) 的 where a=? and c=? 走索引吗？**
- 走 a 的索引，c 不走（因为 b 缺失打破了前缀匹配）
- 但比全表扫描好，因为索引下推（ICP，Index Condition Pushdown）可以在索引层先过滤 c 的条件再回表（MySQL 5.6+）

### 6.2 锁机制完整版（InnoDB RR）

**核心概念**：

| 锁类型 | 英文 | 含义 |
|--------|------|------|
| 共享锁 | S Lock | 允许读，不允写 |
| 排他锁 | X Lock | 不允读不允写 |
| 意向共享 | IS Lock | 表级，告知「有行被加 S 锁」 |
| 意向排他 | IX Lock | 表级，告知「有行被加 X 锁」 |
| 记录锁 | Record Lock | 锁索引记录（不锁间隙） |
| 间隙锁 | Gap Lock | 锁索引记录的间隙（左开右开） |
| 临键锁 | Next-Key Lock | Record Lock + Gap Lock（左开右闭） |

**口诀：等值命中→Record Lock，范围/未命中→Next-Key Lock**

| SQL | 条件 | 锁 |
|------|------|-----|
| SELECT | 普通查询 | 不加锁（快照读，MVCC） |
| SELECT FOR UPDATE | 主键等值命中 | Record Lock |
| SELECT FOR UPDATE | 普通索引等值命中 | Next-Key Lock（命中记录的 Next-Key + 间隙） |
| SELECT FOR UPDATE | 无索引 | 全表 Next-Key Lock（扫描全表加锁） |
| UPDATE | 主键范围 | Next-Key Lock（范围内行+间隙） |
| INSERT | — | 插入间隙的插入意向锁（等待间隙锁释放） |

**追问：什么情况会死锁？怎么排查？**
- 典型场景：两个事务各自的 UPDATE 锁住了对方需要的间隙。A 对 id=5 加锁，B 对 id=10 加锁，然后 A 想锁 id=10→等待 B，B 想锁 id=5→等待 A → 死锁
- 排查：SHOW ENGINE INNODB STATUS 中的 LATEST DETECTED DEADLOCK 段，有详细的锁等待图
- InnoDB 自动检测死锁：选择回滚修改行数最少（工作量最小）的事务，错误码 1213

**追问：意向锁的作用？**
- 没有意向锁的话：加表锁前需要遍历每一行检查是否有行锁 → O(n)
- 有了意向锁：加表锁前只需检查是否有 IX/IS 锁 → O(1)
- 意向锁不阻塞行锁，只和表锁互斥（IX 和 X 表锁互斥）

### 6.3 日志系统：redo log / undo log / binlog

**面试话术（30秒版）**：
> 「InnoDB 三种日志各有分工：redo log 保证 crash-safe（崩溃恢复），记录「对哪个数据页的什么位置做了什么修改」，是物理日志，循环写。undo log 保证事务回滚和 MVCC 读历史版本，记录「修改前的数据」，是逻辑日志。binlog 是 Server 层的逻辑日志，主从复制和数据恢复用，追加写。两阶段提交保证 redo log 和 binlog 的一致性。」

**三种日志对比**：

| 维度 | redo log | undo log | binlog |
|------|----------|----------|--------|
| 层次 | InnoDB 引擎层 | InnoDB 引擎层 | MySQL Server 层 |
| 内容 | 物理：对数据页的修改 | 逻辑：修改前数据 | 逻辑：SQL 语句或行数据变化 |
| 用途 | crash-safe 崩溃恢复 | 回滚 + MVCC | 主从复制 + 数据恢复 |
| 写入方式 | 循环写（ib_logfile） | 随机写（undo 表空间） | 追加写（binlog 文件） |
| 刷盘时机 | 事务提交时（innodb_flush_log_at_trx_commit） | 随 Buffer Pool Checkpoint（持久性由 Redo Log 保证） | 事务提交时（sync_binlog） |

**Binlog 三种格式**：

| 格式 | 记录内容 | 优点 | 缺点 | 默认 |
|------|---------|------|------|------|
| STATEMENT | SQL 语句 | 日志量小 | 非确定性函数（NOW/RAND）导致主从不一致 | 早期 |
| **ROW** | 行级变更（改前→改后） | 精确，主从一致 | 日志量大 | **5.7+ 默认** |
| MIXED | STATEMENT 为主，特殊情况切 ROW | 取两者之长 | 复杂度高 | — |

面试时说：生产环境一律 ROW 格式，STATEMENT 的非确定性函数问题是硬伤，ROW 的日志量大但现代磁盘 IO 扛得住。

**两阶段提交（2PC）**：
```
1. Prepare：写入 redo log（prepare 状态）
2. 写入 binlog
3. Commit：redo log 改为 commit 状态
```
为什么要两阶段：如果先写 redo log 后写 binlog → crash → 从库少了这条数据；如果先写 binlog 后写 redo log → crash → 从库多了这条数据。两阶段保证二者一致。

**追问：redo log 和 binlog 的刷盘时机怎么配置？**
- innodb_flush_log_at_trx_commit=1：每次提交刷盘（最安全，默认），=2 写 OS 缓存（每秒刷盘），=0 每秒刷盘
- sync_binlog=1：每次提交刷盘，=N 每 N 次提交刷盘
- 金融场景：两个都设 1（双 1 配置），牺牲性能保证数据安全

### 6.4 MVCC：RR vs RC 的 ReadView 差异

**面试话术（30秒版）**：
> 「RR 和 RC 的核心区别在于 ReadView 生成的时机：RR 级别在事务**第一次快照读**时生成 ReadView，之后复用同一个 → 保证可重复读。RC 级别在**每次快照读**时都重新生成 ReadView → 可以读到其他事务已提交的数据。当前读（SELECT FOR UPDATE/UPDATE/DELETE）不走 MVCC，直接读最新版本 + 加锁。」

**ReadView 判断逻辑**（用场景讲，不要背字段）：
```
事务 A(id=100) 开启 → 第一次查询时生成 ReadView（活跃事务列表 [100,101]）
→ 事务 B(id=101) 修改提交
→ A 再次查询：101 在活跃列表中 → 跳过 101 的版本 → 沿 undo 链找上一个版本 → 可重复读
```

**RR vs RC 完整对比**：

| 维度 | RR（可重复读） | RC（读已提交） |
|------|---------------|---------------|
| ReadView 生成 | 第一次快照读时生成 | 每次快照读重新生成 |
| 是否可重复读 | 是 | 否（读到最新提交版本） |
| 间隙锁 | 有（解决幻读） | 无（不解决幻读） |
| 半一致性读 | 不支持 | 支持（UPDATE 时对锁冲突的行读最新提交版本，减少等待） |
| 默认 | MySQL 默认 | Oracle/PostgreSQL 默认 |

**追问：RR 能完全解决幻读吗？**
- 快照读：能（MVCC + ReadView 复用保证一致）
- 当前读：不能。UPDATE/DELETE 的 WHERE 条件可能匹配到其他事务新插入的行（新插入的行没被锁住），但间隙锁会锁住范围防止 INSERT，所以实际上能解决大部分幻读
- 极端场景：事务 A 快照读 → 事务 B 插入并提交 → 事务 A **当前读** UPDATE → 会更新到 B 插入的行（幻读现象）。解决方案是：先 SELECT FOR UPDATE 锁住范围

### 6.5 主从复制

| 复制格式 | 优点 | 缺点 |
|----------|------|------|
| STATEMENT | binlog 小 | 部分函数/存储过程可能不一致 |
| ROW | 精确 | binlog 大（推荐） |
| MIXED | 自动选择 | 复杂 |

**面试话术（30秒版）**：
> 「主从复制三个线程：主库的 dump 线程推送 binlog → 从库的 IO 线程接收写入 relay log → 从库的 SQL 线程回放 relay log。半同步复制在从库收到 relay log 后给主库 ACK，主库再返回客户端。并行复制：MySQL 5.7 基于 group commit（LOGICAL_CLOCK），8.0 升级为 WRITESET——通过哈希判断行级冲突，粒度更细、回放效率显著提升。」

**追问：主从延迟怎么处理？**
- 业务层面：写完立即读 → 强制走主库（ShardingSphere 的 HintManager）
- 监控层面：pt-heartbeat 监测延迟秒数，超过阈值告警
- 架构层面：MGR（MySQL Group Replication）或自研中间件做读写分离的动态路由

**MySQL 8.0 加分特性**（面试中展示版本意识）：
- **Hash Join**：替代 5.7 的 BNL（Block Nested Loop），无索引 JOIN 性能大幅提升
- **窗口函数**：ROW_NUMBER/RANK/LEAD/LAG，报表类 SQL 可读性提升
- **CTE（WITH 语句）**：递归查询支持
- **降序索引**：`INDEX idx (a ASC, b DESC)` — 8.0 真正生效，5.7 解析但忽略

### 6.6 SQL 优化

**EXPLAIN 核心字段速查**：

| 字段 | 含义 | 关注点 |
|------|------|--------|
| type | 访问类型 | system > const > eq_ref > ref > range > index > **ALL**（尽量避免） |
| key | 实际使用的索引 | 是否命中预期索引 |
| key_len | 索引用到的字节数 | 判断走了几列 |
| rows | 预估扫描行数 | 越小越好 |
| Extra | 附加信息 | Using index（覆盖）> Using index condition（ICP）> Using where（回表过滤）> **Using filesort**（额外排序）> **Using temporary**（临时表） |

**常见优化套路**：

| 问题 | 方案 |
|------|------|
| filesort | 加索引覆盖 ORDER BY 列，或缩小结果集让内存排序扛住 |
| 深分页 `LIMIT 100000,20` | 延迟关联：先用子查询定位主键再回表，或记住上次 ID 用 `WHERE id > ? LIMIT 20` |
| COUNT 大表慢 | COUNT(*)≈COUNT(1)（InnoDB 无差别）；MyISAM 才有行数缓存；大表用 Redis 计数/估算 |
| JOIN 慢 | 小表驱动大表；确保被驱动表 JOIN 列有索引；MySQL 8.0 的 Hash Join 替代 BNL |
| 索引失效 | 函数/计算/隐式类型转换/LIKE '%xx'/OR 两边不统一 |

**索引失效速查**（高频）：

```sql
-- 假设索引 (name, age)
WHERE LEFT(name,3) = 'abc'   -- 函数，失效
WHERE name + '' = 'abc'      -- 计算，失效
WHERE name = 123             -- 类型转换（字符串列比整数），坑
WHERE name LIKE '%abc'       -- 前缀通配符，失效
WHERE name = 'a' OR age = 18 -- OR 两边不统一，失效（可拆成 UNION）
```

**面试时必须准备 1 个真实案例**：现象→EXPLAIN 定位（type/rows/Extra）→根因→改写→效果数据（必须量化）

### 6.7 分库分表 & 数据治理

分片键选法、跨分片问题。补充数据生命周期管理：冷热分离（按时间分表+定时归档）、异构数据同步（Canal→ES/ClickHouse，延迟一致性怎么处理）。MySQL 8.0+ 不可见索引（加分项，降序索引见 6.5 节）。

---

## 七、Redis 深度（P1）

### 7.1 数据结构底层

**面试话术（30秒版）**：
> 「Redis 五种基本类型的底层实现不是一一对应的。String 有三种编码：int（整数直接存在指针里）、embstr（≤44 字节的短字符串，一次 malloc）、raw（长字符串）。List 在 3.2 后统一为 quicklist（ziplist 组成的双向链表）。Hash/ZSet 小数据用紧凑编码（7.0 前 ziplist，7.0 后改用 listpack），Set 小数据用 intset（全整数集合）；数据量大了各自转为对应结构——Hash 转 dict，Set 转 dict，ZSet 转 skiplist+dict。这套编码转换机制叫 redisObject + encoding。」

**底层实现速查**：

| 数据类型 | 小数据量编码 | 大数据量编码 | 转换条件 |
|----------|-------------|-------------|---------|
| String | **int** / embstr（SDS） | raw（SDS） | int: 整数可转 long；embstr→raw: 长度>44字节或执行 APPEND |
| List | ziplist（3.2前）→ **quicklist**（3.2后统一，无大小切换） | linkedlist（3.2前，已废弃） | quicklist 是 ziplist 组成的双向链表，每个节点存一个 ziplist |
| Hash | **listpack**（7.0+）/ ziplist（7.0前） | hashtable（dict） | 字段数>512 或 单字段>64字节 |
| Set | **intset**（全整数集合） | hashtable（dict） | 元素>512 或 出现非整数元素 |
| ZSet | **listpack**（7.0+）/ ziplist（7.0前） | skiplist + dict | 元素>128 或 单元素>64字节 |

> **版本备注**：Redis 7.0 引入 listpack 逐步替代 ziplist（解决 ziplist 连锁更新问题）。当前 7.x 中 Hash/ZSet 小数据默认用 listpack，Set 小数据仍是 intset。面试以 ziplist 回答也可（多数公司还在 6.x），但主动提 listpack 是加分项。

**追问：SDS 相比 C 字符串的优势？**
- O(1) 获取长度（有 len 字段），C 字符串要 O(n) 遍历
- 二进制安全（不用 \0 判断结束，用 len）
- 预分配空间 + 惰性释放，减少内存重分配次数
- **这些设计概念上和 Java 的 StringBuilder 类似**，都是减少频繁内存分配

**追问：跳表（skiplist）为什么用在 ZSet？和红黑树比？**
- 跳表实现简单（比红黑树少很多代码）
- 范围查询：跳表直接走链表（O(logN) 定位起点 + O(M) 遍历），比红黑树中序遍历直观
- 平衡性：跳表是概率平衡（随机层数），不需要像红黑树那样复杂旋转
- ZSet 用 dict + skiplist 组合：dict 负责 O(1) 等值查询，skiplist 负责范围查询

**追问：渐进式 rehash？**
- Redis dict 扩容/缩容时不是一次性搬迁所有数据（可能阻塞主线程）
- 维护两个 hash 表（ht[0] 旧表，ht[1] 新表），rehashidx 标记当前进度
- 每次对字典的增删改查操作，都顺便搬几个桶（分摊到多次请求）
- 定时任务也会执行 rehash（serverCron 中的 dictRehashMilliseconds）
- 内存开销：rehash 期间两个表共存，内存翻倍，是大 key 场景的坑

### 7.2 持久化机制

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| RDB | 快照，fork 子进程 dump 全量数据 | 恢复快，文件小 | 可能丢数据（两次快照之间） |
| AOF | 追加写命令日志 | 数据安全（最多丢1秒） | 文件大，恢复慢 |
| 混合持久化(4.0+) | RDB 快照 + 快照后的 AOF 增量 | 取两者之长 | — |

**RDB 的 COW（写时复制）原理**：
- fork() 子进程，父子进程共享同一物理内存（页表标记只读）
- 父进程写数据时触发页异常 → 复制该内存页 → 修改副本 → 子进程始终读原始数据
- COW 的优势：fork 瞬间快（不复制内存），只有被修改的页才复制

**AOF 重写**：
- 不是读旧 AOF 文件，而是 fork 子进程扫描当前数据库状态 → 生成等价的 SET 命令 → 写入新 AOF 文件
- AOF 重写期间的写命令同时写到 AOF 缓冲和 AOF 重写缓冲 → 新 AOF 文件写完后再追加重写缓冲
- 目的：压缩 AOF 文件大小

**面试话术（30秒版）**：
> 「线上一般开混合持久化：RDB 保证恢复速度，AOF 保证数据安全。fork 子进程利用 COW 机制做快照，对主进程影响主要是 fork 瞬间的 CPU 开销和 COW 时的内存复制。如果内存很大（>10G），fork 可能卡顿几百毫秒到秒级。」

### 7.3 过期删除与内存淘汰

**过期删除策略（惰性+定期组合）**：

| 策略 | 时机 | 说明 |
|------|------|------|
| 惰性删除 | 访问 key 时 | 检查是否过期，过期则删。省 CPU 但可能堆积 |
| 定期删除 | serverCron 每 100ms | 随机抽 20 个 key 检查，过期比例 > 25% 则继续抽 |

两者结合：懒删除保证不浪费 CPU 检查不访问的 key，定期删除兜底防止过期 key 堆积。

**8 种内存淘汰策略**：

| 策略 | 范围 | 行为 |
|------|------|------|
| noeviction（默认） | — | 不淘汰，写操作报错 |
| allkeys-lru | 所有 key | 淘汰最近最少使用 |
| volatile-lru | 设了过期时间的 key | 同上 |
| allkeys-lfu（4.0+） | 所有 key | 淘汰最不经常使用 |
| volatile-lfu（4.0+） | 设了过期时间的 key | 同上 |
| allkeys-random | 所有 key | 随机淘汰 |
| volatile-random | 设了过期时间的 key | 同上 |
| volatile-ttl | 设了过期时间的 key | 淘汰最早过期的 |

**LFU vs LRU**：
- LRU：只看最近访问时间，无法区分冷热（一次批量访问就变成热 key）
- LFU：看访问频率，counter 用对数增长（不是简单+1），而且有衰减（随时间减少）。更接近真实的热度

**面试话术**：
> 「缓存场景默认推荐 allkeys-lru。如果担心热点数据被误淘汰，4.0 以上用 allkeys-lfu 更精确。注意 noeviction 是默认值但不适用于缓存场景——缓存满了新增会报错，不符合预期。」

### 7.4 集群方案

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 主从 | 一主多从，读写分离 | 简单 | 手动故障转移，写单点 |
| 哨兵 | 监控主节点，自动故障转移 | 高可用 | 写仍是单点，水平扩容有限 |
| Cluster | 16384 个 slot 分片，多主多从 | 水平扩展 | 跨 slot 操作受限，客户端需支持 |

**Cluster 核心机制**：

- **Slot 分配**：CRC16(key) % 16384，每个节点负责一部分 slot
- **MOVED vs ASK**：MOVED 是 slot 永久迁移到其他节点，ASK 是 slot 正在迁移中（临时）
- **Gossip 协议**：节点间交换状态信息（PING/PONG/MEET），最终一致性
- **故障转移**：节点 PFAIL（主观下线）→ 半数以上主节点确认 → FAIL → 从节点发起选举（类似 Raft 的 epoch 机制）

**追问：为什么是 16384 个 slot？**
- 16384 = 2^14，对于 1000 个节点规模足够细粒度
- 心跳消息中携带 slot 位图（16384 bits = 2KB），如果 65535 则是 8KB，浪费网络带宽
- CRC16 是 16 位的，65535 才是上限，Redis 刻意选 16384

**追问：集群模式下批量操作怎么处理？**
- 跨 slot 的 mget/mset 不支持，需要业务侧按 slot 分组（用 hash tag {key} 强制分配到同一 slot）
- Pipeline 仍然可以发多个命令到不同节点
- 事务（MULTI/EXEC）也要求所有 key 在同一 slot

### 7.4.5 主从复制原理

**全量同步**：从库首次连接发 PSYNC → 主库 BGSAVE 生成 RDB 发给从库 → 快照期间的写命令记在 replication buffer，快照发完后再补发追平。

**增量同步**：主库维护 repl-backlog 环形缓冲区（默认 1MB），记录写命令和 offset。从库断连重连后发 PSYNC + offset，offset 还在 backlog 里就增量补发，不在就退化全量同步。

**追问：什么会导致退化全量？** backlog 太小或断连太久，offset 被新命令覆盖。默认 1MB 线上大概率不够，需要调大。

**面试话术（30秒版）**：
> 「Redis 主从复制分全量和增量。全量靠 RDB 快照，增量靠 repl-backlog 按 offset 续传。关键点是 backlog 默认 1MB 线上不够用，短断连就退化全量同步，需要根据写入量调大。」

### 7.5 缓存一致性

**面试话术（30秒版）**：
> 「缓存一致性的经典问题是「先删缓存再更新 DB」和「先更新 DB 再删缓存」都不完美。最常用的方案是**延迟双删**：先删缓存 → 更新 DB → 延迟若干毫秒 → 再删缓存。延迟时间经验值取业务读请求的典型耗时。兜底靠缓存过期时间 + 订阅 binlog（Canal）异步更新缓存。架构师认知：强一致性不上缓存，缓存就是为最终一致性而生的。」

**方案对比**：

| 方案 | 问题 | 适用 |
|------|------|------|
| 先删缓存→更新DB | 更新DB期间有读请求把旧数据写回缓存 | — |
| 先更新DB→删缓存 | 删缓存失败导致缓存是脏数据 | 多数场景 |
| 延迟双删 | 第二次删除的延迟不好定 | 要求较高一致性 |
| Canal订阅binlog | 架构复杂度高 | 核心链路强需求 |
| TTL兜底 | 最长不一致时间=TTL | **任何方案都需要的底线** |

### 7.6 缓存三问题

**1. 缓存穿透**（查不存在的数据，绕过缓存直击 DB）

| 方案 | 原理 | 适用 |
|------|------|------|
| **布隆过滤器** | 所有 key 哈希后存 bitmap，查前先问布隆 | key 空间可控，有误判率 |
| **空值缓存** | 查不到也缓存 null，短 TTL | key 空间无限或布隆维护成本高 |

面试说：先用布隆过滤掉大部分非法 key，极端情况布隆误判时空值缓存兜底。

**2. 缓存击穿**（热点 key 过期瞬间，大量请求打到 DB）

| 方案 | 原理 | 适用 |
|------|------|------|
| **互斥锁** | 查不到缓存时加锁，持锁线程查 DB 写缓存，其他等待 | 一致性优先 |
| **逻辑过期** | 不删缓存，value 带过期时间戳；读时发现过期先返回旧值，异步更新 | 可用性优先 |

**3. 缓存雪崩**（大量 key 同时过期，或 Redis 宕机）

- TTL 加随机值（基础 TTL ± 随机偏移），性价比最高
- 多级缓存（本地 Caffeine + 远程 Redis），Redis 挂了本地还能扛
- 限流降级兜底，保证 DB 不被瞬间冲垮

### 7.7 Redis Pipeline、事务、大Key、热Key

**Pipeline（管道）**：批量发送命令→批量接收响应，减少 RTT。不是原子操作，只是网络优化。

**事务（MULTI/EXEC/WATCH）**：不支持回滚（语法错整个事务失败，运行时错只有错的那条失败）。WATCH 实现 CAS 乐观锁。

**Lua 脚本**：原子执行，减少网络往返，替代事务的常用方案。

**大Key**：String >10KB 或集合元素 >1万。危害→阻塞（DEL 大集合会卡主线程）、带宽打满、数据倾斜。排查→`redis-cli --bigkeys`/`MEMORY USAGE key`。删除→`UNLINK`（4.0+异步删）或分批删（`HSCAN` + `HDEL`）。

**热Key**：单 key QPS 极高把某个节点 CPU 打满。发现→`redis-cli --hotkeys`/客户端统计。解决→本地缓存/读写分离/热 key 多副本分散到不同节点。

---

## 八、消息队列深度（P1）

### 8.1 Kafka 架构

**面试话术（30秒版）**：
> 「Kafka 的核心设计是高吞吐，三个关键技术点：顺序写磁盘 + PageCache + 零拷贝（sendfile）实现高性能；分区实现并行处理；ISR 机制平衡可靠性和可用性。消费者拉模式避免推送压力，offset 由消费者自行管理。Kafka 定位是分布式日志系统/流数据管道，不是通用消息中间件。」

**核心概念**：

| 概念 | 说明 |
|------|------|
| Topic | 逻辑消息分类 |
| Partition | 物理分区，每个分区是有序的不可变日志，一个分区对应一个目录 |
| Segment | 分区内按大小(默认1G)或时间分段，.log存消息/.index偏移索引/.timeindex时间索引 |
| ISR | In-Sync Replicas，与 Leader 保持同步的副本集合 |
| HW/LEO | High Watermark(消费者可见的最大offset) / Log End Offset(写入的最大offset) |
| Controller | Kafka 集群的大脑，负责分区 leader 选举等工作，由 ZK/KRaft 协调选举 |

**追问：Kafka 为什么吞吐量高？**
1. **顺序写磁盘**：append-only 日志，避免了磁盘的随机写
2. **PageCache**：利用 OS 页缓存，读写都走内存
3. **零拷贝（sendfile）**：数据从磁盘→PageCache→网卡，不经过用户态
4. **批量处理**：Producer 攒一批再发，Consumer 拉一批再消费
5. **分区并行**：不同分区可在不同 Broker 上并行处理
6. 面试金句：「Kafka 把磁盘当成了消息队列，但用的是顺序读写 + PageCache，实际上更接近内存性能」

**ISR 机制**：
- Leader 维护 ISR 列表（同步中的副本）
- Follower 落后太多（replica.lag.time.max.ms，默认30s） → 踢出 ISR
- 生产者 acks=all（-1）时，必须所有 ISR 写入成功才确认
- 好处：Leader 挂了可以在 ISR 中选新 Leader（数据不会丢或丢很少）
- 追问：acks 三个级别？
  - 0：不等确认，可能丢消息
  - 1：Leader 写入即确认
  - -1/all：所有 ISR 写入才确认（最可靠，延迟最高）

**追问：Kafka rebalance 的过程与问题？**

- rebalance 触发条件：消费者加入/离开、topic 分区数变更、消费者超时未发心跳
- 过程：coordinator 通知所有消费者重新分配分区
- 问题：rebalance 期间所有消费者暂停消费 → **STW（Stop-The-World）**
- 优化：使用增量重分配协议（Cooperative Rebalancing, Kafka 2.4+），只重新分配有变化的分区
- 面试时说：「Kafka 的重平衡是老生常谈的痛点，生产环境要配置合理的 session.timeout.ms 和 heartbeat.interval.ms，避免误触发」

### 8.2 RocketMQ 架构

**架构角色**：NameServer（无状态路由，类似 Nacos 的简化版，不选举不持久化）→ Broker（主从）→ Producer/Consumer

**追问：RocketMQ 的 NameServer 和 Kafka 的 ZK 有何不同？**
- NameServer 极度简单：无状态、不选举、不持久化，节点间不通信
- 这是 RocketMQ 的架构哲学：用简单组件替代复杂组件，运维友好
- ZK 自身就是一个分布式系统（有选举/持久化/JVM 开销），Kafka 3.3+ 用 KRaft(Kafka Raft) 替代 ZK 依赖（4.0 计划彻底移除 ZK 支持）

**事务消息**（RocketMQ 独有能力）：
1. 发送半消息（half message，对消费者不可见）
2. 执行本地事务
3. 发送 commit/rollback → Broker 标记半消息可见/删除
4. Broker 回查（check）：长时间未收到二次确认 → 回调 Producer 的 checkLocalTransaction 接口

**顺序消息**：
- 同一业务 ID（订单号）的消息发到同一 MessageQueue → 同一消费者线程顺序消费
- Producer 端用 MessageQueueSelector，Consume 端用 MessageListenerOrderly（加锁保证同一队列单线程消费）

**消息重试与死信队列**：
- 消费失败返回 RECONSUME_LATER → 进重试队列 %RETRY%consumerGroup
- 重试间隔：10s/30s/1m/2m/3m/4m/5m/6m/7m/8m/9m/10m/20m/30m/1h/2h（默认16次）
- 超过最大重试次数 → 进死信队列 %DLQ%consumerGroup → 人工处理
- 面试时说：死信不是bug，是兜底机制。死信消息需要告警+人工介入

**存储模型**：
- CommitLog：所有消息顺序写入一个文件（顺序写保证高性能），每个文件默认1G
- ConsumerQueue：按 Topic+Queue 维度索引，存消息在 CommitLog 的 offset+size+tagCode
- 消费时先查 ConsumerQueue 拿到 offset，再读 CommitLog → 两次IO但顺序读很快
- 对比 Kafka：Kafka 按分区独立存储，RocketMQ 所有分区共享 CommitLog

**延迟消息**：
- **4.x**：不支持任意时间延迟，只支持预设的18个级别：1s/5s/10s/30s/1m/2m/3m/4m/5m/6m/7m/8m/9m/10m/20m/30m/1h/2h
- **5.x**：引入**定时消息（Timer Message）**，支持任意延迟时间，基于时间轮算法实现
- 订单超时关单的典型场景

> **版本提示**：RocketMQ 5.x 还新增了 **Pop 消费模式**（消费者按需 Pop 消息，替代传统 Push/Pull）、**Proxy 代理层**（支持 gRPC 协议和多语言 SDK）、**Controller 模式 HA**（替代传统 Master-Slave 切换）。以上描述以 4.x 为主，面试时应了解 5.x 演进。

**消费者 Rebalance**（客户端驱动）：
- 触发条件：消费者数量变化、Topic 配置变化
- 过程：每个消费者定时拉取 Topic 路由信息和同一消费组的消费者列表，在**客户端独立计算**自己应消费哪些 Queue。与 Kafka 的 GroupCoordinator 驱动模式不同。
- 注意：Rebalance 期间短暂暂停消费（类似 Kafka 的 STW）

### 8.3 消息可靠性三种语义

| 语义 | 含义 | 实现方式 |
|------|------|---------|
| at most once | 最多一次，可能丢 | acks=0，异步发送 |
| **at least once** | 至少一次，可能重复 | acks=all + 同步发送 + 消费端幂等 |
| exactly once | 精确一次，不丢不重 | Kafka 幂等 Producer + 事务（或业务层幂等） |

面试时说：
> 「大多数业务场景 at least once + 消费者幂等就够了。exactly once 的代价很高（需要事务支持 + 性能下降），不是所有场景都值得。幂等可以通过业务唯一键 + DB 唯一索引 + Redis Set NX 实现。」

### 8.4 Kafka vs RocketMQ 选型对比（高频）

| 维度 | Kafka | RocketMQ |
|------|-------|----------|
| 定位 | 流数据管道、大数据生态 | 业务消息中间件 |
| 事务消息 | 需事务 API（性能开销大） | 原生半消息+回查，简洁 |
| 延迟消息 | 不原生支持 | 4.x 固定18级 / 5.x 任意时间 |
| 顺序消息 | 分区内有序 | 分区内有序 + MessageListenerOrderly |
| 吞吐量 | 百万级（批量+顺序写） | 十万级 |
| 生态 | Connect + Streams + ksqlDB | 阿里云商业版 + 中文社区 |
| 运维 | 较重（但 KRaft 已移除 ZK 依赖） | NameServer 极简 |

面试时说：「如果是电商交易链路（订单/支付），用 RocketMQ 的事务消息和延迟消息更合适；如果是日志/埋点/流计算，用 Kafka 的大数据生态。不纠结谁更好，纠结谁更适合当前场景。」

### 8.5 消息堆积处理

**面试话术**：
> 「消息堆积的核心思路是增加并行度，而不是简单加机器。手段包括：增加消费者数量（但受分区数限制，Kafka 分区数要 >= 消费者数）、批量消费、降级非核心逻辑、临时跳过堆积的非核心消息、紧急修复消费慢的代码性能瓶颈。关键是要有消费延迟的监控告警，不要等堆积了才发现。」

### 8.6 RocketMQ 可靠性

**三环节**：生产（同步+重试）→ Broker（同步刷盘+主从复制）→ 消费（手动ack+幂等+重试）

**幂等**：业务唯一键 → DB 唯一索引 → Redis Set NX

---

## 九、IO 模型 & Netty（P1）🔥

### 9.1 BIO / NIO / AIO

**面试话术（30秒版）**：
> 「BIO 一个连接一个线程，accept 和 read 都阻塞 → 连接多了线程切换开销无法承受。NIO 引入 Channel + Buffer + Selector 的 Reactor 模式，一个 Selector 线程管理多个 Channel，只有就绪的 Channel 才处理。AIO 更进一步——读写操作也异步，操作系统完成后再回调通知，但 Linux 上 AIO 不成熟，用的很少。Java 生态主力是 NIO + Netty。」

**三种模型对比**：

| 模型 | 连接/线程关系 | 阻塞点 | Java 实现 | 适用 |
|------|-------------|--------|-----------|------|
| BIO | 1:1 | accept + read 都阻塞 | ServerSocket | 低连接数、长连接少量场景 |
| NIO | M:1 | 只有 select 阻塞 | Selector + SocketChannel | 高并发连接、短连接 |
| AIO | M:0（回调） | 完全不阻塞 | AsynchronousChannel | Windows（IOCP），Linux 不成熟 |

### 9.2 select / poll / epoll

> 这是面试会深入追问的 OS 底层知识。

**面试话术（30秒版）**：
> 「select 和 poll 每次调用都要把 fd 集合从用户态拷贝到内核态，内核遍历所有 fd 检查就绪状态 → O(n)。epoll 用 epoll_ctl 注册 fd（红黑树管理），事件就绪后通过回调把 fd 加入就绪链表 → epoll_wait 直接取就绪链表 → O(1)。epoll 解决了两个核心问题：不需要每次传入全部 fd 集合 + 不需要遍历全部 fd 找就绪的。LT（水平触发）和 ET（边缘触发）的区别在于：LT 没读完会一直通知，ET 只通知一次 → 必须读到 EAGAIN。」

**演进对比**：

| 维度 | select | poll | epoll |
|------|--------|------|-------|
| 数据结构 | 位图（bitmap） | 数组（pollfd） | 红黑树 + 就绪链表 |
| fd 上限 | 1024（编译时常量 FD_SETSIZE） | 无上限 | 无上限 |
| 内核/用户拷贝 | 每次 select 传入全部 fd | 每次 poll 传入全部 fd | epoll_ctl 一次性注册 |
| 就绪检查 | 遍历全部 fd → O(n) | 遍历全部 fd → O(n) | 事件回调 + 就绪链表 → O(1) |
| 触发方式 | LT（水平触发） | LT | **LT + ET** |

**epoll 深入追问**：

*「epoll 的 ET 模式下为什么要非阻塞 IO？」*
- ET 要求一次读到返回 EAGAIN 为止，如果 socket 是阻塞的，在数据没到来时会阻塞住 → 无法处理其他就绪的 fd
- 必须设非阻塞 + 循环读/写直到 EAGAIN

### 9.3 Netty 核心概念

**面试话术（30秒版）**：
> 「Netty 是基于 NIO 的高性能网络框架，核心是 Reactor 模式——Boss EventLoopGroup 负责 accept 连接，Worker EventLoopGroup 负责读写。每个 Channel 绑定到一个 EventLoop 线程（线程安全不用加锁）。Pipeline 是 Handler 的双向链表，inbound 和 outbound 分开处理。ByteBuf 是 Netty 自己实现的字节容器——读写指针分离（无需 flip），支持池化和零拷贝。」

**Netty 核心组件**：

| 组件 | 作用 | 面试记忆点 |
|------|------|-----------|
| EventLoopGroup | 线程池，Boss 负责连接，Worker 负责 IO | 每个 Channel 绑定一个 EventLoop 线程 |
| ChannelPipeline | Handler 双向链表 | Inbound 从 head→tail，Outbound 从 tail→head |
| ByteBuf | 字节容器 | 读写索引分离 + 池化 + 零拷贝 |
| ChannelFuture | 异步结果 | addListener 回调，不阻塞 |

**Reactor 线程模型**：

| 模式 | 结构 | 适用 |
|------|------|------|
| 单 Reactor 单线程 | 一个线程 accept + read + write | 低负载 |
| 单 Reactor 多线程 | 一个 Reactor 线程 + 线程池处理业务 | 中等负载 |
| **主从 Reactor 多线程** | Boss 线程池 accept + Worker 线程池 read/write | **Netty 默认，高并发标配** |

**ByteBuf 要点**：
- 读写指针分离（readerIndex / writerIndex），比 ByteBuffer 的 flip 操作更清晰
- 池化（PooledByteBufAllocator）：减少 GC 压力，对象复用
- 零拷贝：CompositeByteBuf（组合多个 Buffer 不用复制）、Slice（切片共享同一内存）、FileRegion（transferTo → sendfile 系统调用）
- 直接内存 vs 堆内存：DirectBuffer 避免 Java 堆和 Native 堆的数据拷贝，但分配/回收成本高

**追问：Netty 怎么解决 TCP 粘包/拆包？**
- 粘包原因：TCP 是流式协议，没有消息边界；发送端 Nagle 算法合并小包；接收端来不及读取堆积
- Netty 方案：FixedLengthFrameDecoder（定长）、LineBasedFrameDecoder（换行符）、DelimiterBasedFrameDecoder（自定义分隔符）、**LengthFieldBasedFrameDecoder**（最通用，长度字段前置）
- 面试时说：「生产环境最常用 LengthFieldBasedFrameDecoder，协议设计时在消息头带 body 长度。」

**追问：Netty 的心跳机制？**
- IdleStateHandler：readerIdleTime / writerIdleTime / allIdleTime
- 超时触发 IdleStateEvent → userEventTriggered 处理 → 关闭连接或发心跳包
- 面试时说：「Netty 的心跳不是内置的 keep-alive，而是应用层自己实现的。IdleStateHandler 只是帮你检测空闲，具体怎么处理（关连接/发心跳）要自己写在 userEventTriggered 里。」

---

## 十、分布式理论（P1）

### 10.1 CAP 与 BASE

**面试话术（30秒版）**：
> 「CAP 理论是分布式系统的经典约束：C（一致性）、A（可用性）、P（分区容错）三者最多同时满足两个。实际工程中 P 是必须选的（网络分区不可避免），所以核心决策是 CP 还是 AP——一致性优先（金融支付场景）选 CP，可用性优先（社交/电商）选 AP。BASE 是对 CAP 的工程妥协：Basically Available（基本可用）+ Soft state（软状态/中间态）+ Eventually consistent（最终一致）。」

**面试中怎么举例子**：
- CP 系统：ZooKeeper、etcd、HBase（一致性优先，网络分区牺牲可用性）
- AP 系统：Eureka、Cassandra、DynamoDB（可用性优先，允许临时不一致）
- Nacos 的巧妙之处：临时实例走 AP，永久实例走 CP → 一个组件同时满足两类需求

### 10.2 Raft 一致性协议

**面试话术（30秒版）**：
> 「Raft 把一致性拆成三个子问题：Leader 选举（term + 随机超时，先到先得）、日志复制（Leader 向 Follower 同步日志，多数确认即提交）、安全性（新 Leader 的日志必须包含所有已提交的 entry——通过选举限制实现）。Leader 通过心跳（AppendEntries RPC）维持权威，Follower 超时没有收到心跳就转为 Candidate 发起选举。」

**Raft 三阶段**：

| 阶段 | 子问题 | 核心保证 |
|------|--------|---------|
| Leader 选举 | 选出一个 Leader | 随机超时减少冲突，term 递增，同一个 term 只能投一票 |
| 日志复制 | 复制日志到多数节点 | 日志从头匹配（prevLogIndex/prevLogTerm 校验） |
| 安全性 | 已提交的日志不丢失 | 选举限制（Candidate 的日志不能比多数节点旧） |

**追问：Raft 和 Paxos 的区别？**
- Paxos 难以理解和实现，Raft 以可理解性为首要目标
- Paxos 是单值共识，Multi-Paxos 才支持多值；Raft 原生支持日志序列
- 实际工程：etcd（Raft）、TiKV（Raft）、Chubby（Paxos）、ZooKeeper（ZAB，类 Paxos）
- 面试时不要说「Raft 更简单所以好」，要说「Raft 把一致性过程分解成更清晰的子问题，降低了实现出错的可能性」

### 10.3 分布式 ID

| 方案 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| 数据库自增 | AUTO_INCREMENT | 简单 | 性能瓶颈，不适合分布式 |
| UUID | 随机生成 | 无依赖 | 字符串长，B+树索引不友好 |
| **雪花算法** | 时间戳+机器ID+序列号 | 趋势递增，高性能 | **时钟回拨**需要处理 |
| 号段模式 | DB 批量分配 ID 区间 | 趋势递增，可定制 | 依赖 DB |
| Redis incr | 单线程自增 | 简单递增 | 依赖 Redis |

**雪花算法深度**：
```
结构：符号位(1bit) + 时间戳(41bit) + 机器ID(10bit) + 序列号(12bit)
优点：趋势递增（索引友好）、本地生成（无网络开销）、高性能
核心问题：时钟回拨（NTP 同步导致时间倒退）
```

**时钟回拨解决方案**：
1. 回拨时间短（<阈值）：等待时间追上再生成
2. 回拨时间长：报警 + 切换备用机器 ID
3. 美团 Leaf：雪花算法 + ZK 持久化时间戳，回拨时对比 + 拒绝服务或等待
4. 面试时说：「完整的雪花算法实现至少要考虑时钟回拨的兜底策略，这是面试官期待的架构师思维。」

**追问：号段模式（Leaf-segment）的双 buffer 优化？**
- 双 buffer：当前号段用完前提前异步加载下一个号段，避免号段用完后同步等待 DB
- 动态步长：根据消费速度动态调整每次申请的号段大小（消费快→多申，消费慢→少申）

### 10.4 分布式锁（延展）

已在 P0 技术选型中详细讨论，这里补充**红锁（Redlock）** 认知：
- Redlock 是 Redis 作者提出的多节点分布式锁方案，试图解决单节点锁不可靠的问题
- 争议：Martin Kleppmann（《数据密集型应用系统设计》作者）指出 Redlock 依赖时钟同步假设，时钟跳变会破坏安全性
- 面试时说：「学术界对 Redlock 有争议，工程中我的选择是 Redisson 单节点锁 + 业务幂等兜底。如果你真的需要强一致性的分布式锁，用 ZK 或 etcd。」

---

## 十一、系统设计 & 算法（P1）

### 系统设计 5 步法

1. **需求澄清**：主动问 QPS/数据量/一致性/可用性要求
2. **数据模型**：核心表+索引+是否分库分表
3. **核心链路**：接入层→业务层→数据层
4. **高可用**：限流/熔断/降级 + 数据一致性保证
5. **边界与演进**：瓶颈在哪？QPS 涨 100 倍哪里先出问题？

**常见题型**：秒杀/高并发架构、实时排行榜、分布式 ID 生成器、配置中心、短链系统、Feed流、IM系统

**短链系统**：
- 核心：ID 生成（雪花/号段）→ Base62 编码 → 短码
- 读写比极高：Redis 缓存短码→长链映射，读写分离
- 过期策略：定期清理 + Lazy 删除

**实时排行榜**：
- Redis ZSet：ZINCRBY 实时更新分数，ZREVRANGE 获取 TopN
- 大用户量：分段排行榜（前 100 名实时 + 其余定时算），二级缓存
- 同分处理：分数相同时按时间戳排序

**Feed 流系统**：
- 推模式（小V）：发布时推到所有粉丝的收件箱（读快写慢）
- 拉模式（大V）：读时从关注列表拉取（读慢写快）
- 推拉结合：大V 用拉，普通用户用推。核心是冷热分离

**IM/即时通讯**：
- 单聊：客户端A → 服务端 → 客户端B（WebSocket + MQ 异步落库）
- 群聊：发 MQ → 消费端分发 → 批量写入每个人的收件箱
- 已读未读：每条消息记录已读水位线
- 在线状态：心跳 + Redis 存储在线状态

### 秒杀系统完整走通示例

以下用 5 步法完整走通一个秒杀系统的设计，面试时可按此结构讲：

**第 1 步：需求澄清**

- QPS 预估：日常几百 → 秒杀瞬间几十万（缓存热点读 + 库存扣减写）
- 一致性要求：库存不能超卖（强一致），订单可异步（最终一致）
- 可用性：秒杀期间允许部分降级（如推荐模块关闭），但下单核心链路必须可用

**第 2 步：数据模型**

```sql
-- 库存表（热点数据，放 Redis）
CREATE TABLE seckill_stock (
    sku_id BIGINT PRIMARY KEY,
    total_stock INT,       -- 总库存
    available_stock INT,   -- 可用库存
    version INT            -- 乐观锁版本号
);

-- 订单表（异步写入，分库分表按 user_id）
CREATE TABLE seckill_order (
    order_id BIGINT,
    user_id BIGINT,
    sku_id BIGINT,
    status TINYINT,        -- 0=已创建 1=已支付 2=已取消
    create_time DATETIME,
    PRIMARY KEY (order_id),
    KEY idx_user_sku (user_id, sku_id)  -- 防重复下单
);
```

**第 3 步：核心链路**

```
客户端 → CDN（静态资源）→ 网关（鉴权+限流+防刷，验证码/答题）
  → 秒杀服务 → Redis DECR 扣库存（原子操作，库存<0 直接拒绝）
  → MQ 异步发单 → 订单服务消费 MQ 写入 DB
  → 客户端轮询/WebSocket 推送下单结果
```

**第 4 步：高可用**

| 层级 | 策略 | 说明 |
|------|------|------|
| 前端 | 限流 + 验证码 + 答题 | 分散用户请求节奏，过滤机器人 |
| 网关 | 令牌桶/QPS 限流 | 超过阈值的请求直接返回「活动火爆」 |
| 业务 | Redis DECR 预扣库存 | 原子操作，扣到 0 后直接返回售罄，后端零压力 |
| 异步 | MQ 削峰填谷 | 下单请求入队，订单服务按自己节奏消费 |
| 降级 | 非核心功能关闭 | 推荐/购物车等服务降级，释放资源给秒杀链路 |
| 兜底 | 对账（Redis vs DB 库存） | 定时任务比对，发现差异人工介入 |

**第 5 步：演进（QPS 涨 100 倍）**

```
当前：单 Redis + 单 MQ + 单 DB
  ↓
瓶颈：Redis 单节点热点 → 分库存（多个库存 key，用户 hash 到不同 key）
  ↓
瓶颈：Redis Cluster → 每个分片存一部分库存 key
  ↓
瓶颈：机房带宽/延迟 → 异地多活（多个机房各自有库存，用户就近访问）
```

面试时说：每一步演进都讲清楚「上一阶段哪里先崩」和「为什么选这个解法」。

### 算法（3 道核心，其余口述）

| 题目 | 思路 | 关键 |
|------|------|------|
| LRU 缓存 | 双向链表+HashMap | 双向链表 O(1) 删除中间节点 |
| 生产者-消费者 | BlockingQueue+线程池 | 队列满/消费者异常的处理 |
| DCL 单例 | volatile+双重检查+synchronized | volatile 防半初始化对象 |

其余（滑动窗口/单调栈/BFS/堆排序/一致性哈希/限流器）口述能讲思路即可，不必手写。

---

## P2：扩展加分（面试拉开差距的部分）

---

## 十二、JVM & 故障排查（P2）

### GC 选型

| GC | 场景 | 核心 |
|----|------|------|
| G1 | 4G-32G，JDK 9+ 默认 | Region化+混合回收，无碎片 |
| ZGC | >32G，STW<1ms（亚毫秒级） | 染色指针+读屏障，JDK 15+ 生产可用（JDK 17 LTS 推荐） |

**GC 演进脉络（面试时讲出这个就比背参数强）**：
> 「GC 的演进本质是"降低 STW"和"支撑更大内存"这两个需求的博弈。CMS 是第一款并发 GC，但碎片问题严重（并发清除无整理），极端情况退化为 Serial Old 导致长时间 STW，JDK 14 已移除。G1 用 Region 化 + 复制算法解决碎片问题，但单次 Mixed GC 仍有几十到几百毫秒停顿。ZGC 更进一步：染色指针 + 读屏障让并发整理与用户线程几乎同时进行，STW < 1ms，能支撑 TB 级堆。**选型口诀：4G 以下随便选，4-32G 上 G1，32G 以上或对延迟极端敏感上 ZGC。**」

### 类加载与内存模型

**面试话术（30秒版）**：
> 「类加载分三步：加载（读取 class 字节流）、链接（验证 + 准备 + 解析）、初始化（执行 clinit）。双亲委派机制要求加载请求先委托父加载器，防止核心类被篡改。破坏双亲委派的典型场景：JDBC（SPI 机制，Bootstrap ClassLoader 委托 Thread Context ClassLoader）、Tomcat（多个 WebApp 隔离，先自己加载）、OSGi（网状加载图）。」

**追问：对象的内存布局？**
- 对象头（Mark Word 8字节 + Klass Pointer 4/8字节）+ 实例数据 + 对齐填充（8字节对齐）
- 压缩指针（-XX:+UseCompressedOops）：64 位 JVM 将对象引用从 8 字节压缩到 4 字节，可节省大量内存
- 压缩指针生效需堆 < 32G（4字节偏移 * 8字节对齐 = 32G 寻址空间）

### 调优案例

准备 1 个真实经历：现象（Full GC 频繁+数据）→ jstat/jmap/Arthas→根因→优化+效果数据

### 线上故障排查 SOP

面试官问「你们出了线上故障怎么排查」时，不要罗列工具，讲核心决策：

```
1. 止血决策（恢复第一）→ 重启/回滚/降级/切流量？为什么选这个策略？
2. 定位决策（保留现场+找根因）→ jstack/jmap/Arthas 看什么指标？链路追踪定位哪个 Span？
3. 防范决策（避免复发）→ 监控告警补了什么？架构上做了什么改造？
```

**CPU 飙高排查流程**（高频实战场）：
```
1. top -Hp PID → 找到 CPU 最高的线程 TID（转 16 进制）
2. jstack PID | grep -A 20 线程16进制ID → 定位到具体代码行
3. 常见根因：死循环、频繁 FullGC、正则回溯、JSON 序列化大对象
```

**OOM 排查流程**：
```
1. -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=xxx → 自动 dump
2. jmap -dump:live,format=b,file=heap.bin PID → 手动 dump
3. MAT/JProfiler 分析：Dominator Tree + Leak Suspects + Histogram
4. 常见根因：ThreadLocal 没 remove/静态集合膨胀/大对象/堆外内存泄漏
```

**死锁排查**：jstack PID 底部自动输出 Found 1 deadlock + 详细锁等待图

准备 1 个真实排查案例（CPU 飙高/OOM/慢请求/死锁/内存泄漏），按这 3 步讲清楚你的决策。

---

## 十三、操作系统 & 网络基础（P2）

> 社招不会像校招那样手写代码，但底层原理会被问到。目标是能用 Java 工程师的类比讲清楚关键概念。

### 13.1 操作系统

**进程 vs 线程**：

| 维度 | 进程 | 线程 |
|------|------|------|
| 资源 | 独立内存空间 | 共享进程内存空间 |
| 通信 | IPC（管道/消息队列/共享内存/socket） | 共享变量（需同步） |
| 切换开销 | 大（页表/TLB/缓存都要刷新） | 小（同一地址空间） |
| 崩溃影响 | 一个进程崩溃不影响其他 | 一个线程崩溃可能拖垮整个进程 |

**虚拟内存**：每个进程独立的虚拟地址空间，靠页表映射到物理内存。TLB 是页表的高速缓存，缺页中断从磁盘加载页面。

**伪共享（False Sharing）**：两个线程修改同一缓存行（64字节）的不同变量，MESI 协议导致缓存行频繁失效。Java 解决：`@sun.misc.Contended` 注解或手动填充。Disruptor RingBuffer、CHM CounterCell 都用此技术。

**上下文切换**：触发：时间片耗尽/IO阻塞/锁等待。开销：寄存器/TLB/缓存刷新，一次约 1-10 微秒。

### 13.2 网络基础

**TCP 三次握手 & 四次挥手**：

**三次握手（连接建立）**：
```
Client → Server: SYN(seq=x)              "我想连接"
Server → Client: SYN(seq=y) + ACK(x+1)   "收到，我也准备好"
Client → Server: ACK(y+1)                "确认"
```

追问：「为什么三次而不是两次？」→ TCP 是全双工协议，需要双方都确认发送和接收能力正常。两次握手的话服务端无法确认客户端的接收能力。

**四次挥手（连接断开）**：
```
Client → Server: FIN(seq=x)              "我没数据了，想断开"
Server → Client: ACK(x+1)                "收到"（Server 可能还有数据要发）
Server → Client: FIN(seq=y) + ACK(x+1)   "我也没数据了"
Client → Server: ACK(y+1)                "确认"
Client: TIME_WAIT 2MSL
```

追问：「为什么要 TIME_WAIT 状态（2MSL）？」→ 两个原因：1) 保证最后一个 ACK 到达服务端（如果 ACK 丢了，服务端会重发 FIN）；2) 让旧连接的所有报文在网络中消失（新连接不会被旧报文干扰）。

**TCP 可靠传输**：序列号 + 确认应答（延迟ACK） + 滑动窗口（流量控制） + 拥塞控制（慢启动/拥塞避免/快速重传/快速恢复）

**HTTP vs HTTPS**：

| 维度 | HTTP | HTTPS |
|------|------|-------|
| 加密 | 无（明文） | TLS 加密 |
| 端口 | 80 | 443 |
| 握手 | TCP 3次 | TCP 3次 + TLS 握手 + 证书验证（1-2 RTT） |

**TLS 握手**（简单版）：
```
1. Client Hello：支持的加密套件 + 随机数1
2. Server Hello：选择的加密套件 + 随机数2 + 证书（含公钥）
3. Client：验证证书 → 生成预主密钥 → 用公钥加密发给 Server
4. 双方用 随机数1+随机数2+预主密钥 → 计算会话密钥 → 对称加密通信
```

追问：「TLS 1.2 vs TLS 1.3 的握手效率？」→ TLS 1.3：1-RTT（减掉了一次往返），还支持 0-RTT 恢复（之前连接过的可以直接发数据）。去掉不安全算法（RSA密钥交换）→ 只留 ECDHE 系列的密钥协商。

**DNS & CDN**：

DNS 查询过程（简洁版）：浏览器 DNS 缓存 → OS DNS 缓存 → 本地 DNS 服务器（递归查询）→ 根域名服务器 → 顶级域名服务器 → 权威域名服务器 → 返回 IP

CDN 原理：DNS 返回 CDN 边缘节点 IP（不是源站 IP）→ 用户访问边缘节点 → 命中返回 → 未命中回源站获取 → 缓存（更新时推荐 URL 带版本号/Digest）。

**HTTP/2 核心特性**：
- 多路复用（Multiplexing）：单 TCP 连接上并发传输多个请求-响应，解决 HTTP/1.1 的队头阻塞
- 头部压缩（HPACK）：请求头字典压缩，减少带宽
- Server Push：服务器可主动推送资源（CSS/JS）给客户端，减少往返
- 二进制分帧：不再是文本协议，解析更高效

**gRPC**：
- 基于 Protobuf（二进制序列化，比 JSON 体积小 3-10 倍）+ HTTP/2（多路复用）
- 四种服务类型：Unary（一应一答）、Server Streaming、Client Streaming、Bidirectional Streaming
- 适用场景：微服务间高性能通信（跨语言、强类型、有 IDL 约束）
- 面试时说：「gRPC 解决的是微服务间高性能通信问题——Protobuf 比 JSON 省带宽，HTTP/2 多路复用减少连接数，IDL 自动生成客户端代码消除手写 SDK 的开发成本。」

**WebSocket**：
- 全双工通信：通过 HTTP Upgrade 握手从 HTTP 升级到 WebSocket 协议
- 与 HTTP 短连接的对比：HTTP 每次请求都要建连+传头，WebSocket 一次握手后持续通信
- 适用：实时推送（IM消息、股价、协同编辑）、服务端主动通知
- 面试时说：「WebSocket 解决的是"服务端主动推"的需求。HTTP/2 的 Server Push 只能推静态资源，WebSocket 才是真正的双向实时通道。」

---

## 十四、设计模式在框架中的应用（P2）

> 面试官问「你在项目中用过哪些设计模式」→ 最好的回答是讲**设计模式在框架中的应用**，体现你对框架不只是使用者，而是理解其设计哲学。

| 模式 | Spring 中的应用 | 一句话 |
|------|----------------|--------|
| **单例** | Bean 默认 scope=singleton | IOC 容器统一管理实例 |
| **工厂** | BeanFactory、FactoryBean | 封装复杂对象创建 |
| **代理** | AOP（JDK/CGLIB 动态代理） | 无侵入增强功能 |
| **模板方法** | JdbcTemplate、RestTemplate | 固定流程，子类差异化步骤 |
| **策略** | InstantiationStrategy | 运行时选择算法 |
| **观察者** | ApplicationListener 事件机制 | 解耦组件间依赖 |
| **责任链** | Filter Chain、Interceptor Chain | 多个处理器串行处理 |

**面试话术（挑 3-4 个讲）**：
> 「Spring 中最经典的设计模式应用有三：一是**代理模式**实现 AOP——动态代理对 Bean 做无侵入增强；二是**模板方法模式**——JdbcTemplate 把连接管理/异常处理固定在父类模板方法里，SQL 执行留给回调；三是**观察者模式**——ApplicationListener 实现组件间解耦通信。MyBatis 的插件机制是典型的**责任链模式**——多个 Interceptor 串联拦截 Executor/StatementHandler。」
>
> 「做架构时自己也会主动运用设计模式，比如策略模式组织业务规则引擎、模板方法抽象批处理流程。但原则是**面向抽象设计，不要为了模式而模式**。」

---

## 十五、新趋势速览（P2）

### 虚拟线程（JDK 21，高频新考点）

M:N 映射，IO 密集型可开数万线程，写同步代码达异步性能。局限：
- `synchronized` 块会 **pin 住载体线程（carrier thread pinning）**，导致虚拟线程退化为平台线程，JDK 24（JEP 491）才解决此问题
- ThreadLocal 开销（百万级虚拟线程时可用 ScopedValue 替代，JDK 20+ 孵化）
- CPU 密集型任务不需要虚拟线程（本来就该跑满）

### 其他（知道即可，不展开）

- **可观测性**：OpenTelemetry 统一标准（Traces/Metrics/Logs 三大信号统一模型），OTel Collector 负责采集→处理→导出
- **AI 集成**（差异化谈资，2-3 句话）：Agent 通过 Function Calling/MCP 对接现有微服务体系；AI Gateway 模式统一管理多模型 API Key/限流/计费；LLM 可观测性关注 Token 用量/延迟分布/成本归因

---

## 十六、Java 基础体系（P2）

> 面试中容易被当"默认应该会"来问的 Java 基础，表格式速查足够。

| 知识点 | 核心要点 | 一句话面试 |
|--------|---------|-----------|
| ArrayList vs LinkedList | 数组（O(1)随机访问）vs 双向链表（O(1)头尾插入），ArrayList 默认容量 10，扩容 1.5 倍 | 读多用 ArrayList，频繁头尾增删用 LinkedList |
| TreeMap | 红黑树实现，key 有序（自然序或 Comparator），put/get/remove O(logN) | 需要排序的映射场景；HashMap 无序，LinkedHashMap 按插入序 |
| 反射 | Class.forName / getDeclaredMethod / setAccessible，Spring IOC 和动态代理的基础 | 框架的"万能钥匙"——运行时拿类的元信息并操作，性能低于直接调用 |
| 泛型类型擦除 | 编译后 List\<String\> 和 List\<Integer\> 都是 List，桥接方法保证多态 | 编译期检查 + 运行期擦除，获取泛型参数靠反射 |
| 异常体系 | checked（必须 try-catch 或 throws，如 IOException）vs unchecked（RuntimeException，如 NPE） | Spring 事务只回滚 unchecked；checked 需要 rollbackFor 指定 |

---

## 十七、安全基础（P2）

**JWT（JSON Web Token）**：
- 结构：Header（算法）.Payload（声明数据）.Signature（签名），三段 Base64 编码
- 无状态认证：服务端不需存 session，只需验证签名 → 水平扩展友好
- vs Session：JWT 省服务端存储，分布式友好；Session 可控性强（可强制踢人），单体友好
- 注意：Payload 仅 Base64 编码非加密，敏感数据不要放 JWT；token 泄漏后难以吊销（靠短有效期 + 黑名单）

**OAuth2**（社招只记两个）：
- **授权码模式**（最安全）：用户授权 → 拿 code → 后端用 code+Secret 换 token。token 不在浏览器暴露
- **客户端凭证模式**：客户端 ID+Secret 直接换 token。适用于服务间调用（M2M），不涉及用户

**常见 Web 漏洞**：

| 漏洞 | 原理 | 防御 |
|------|------|------|
| SQL 注入 | 用户输入拼接到 SQL（`' OR '1'='1`） | PreparedStatement 参数化查询，MyBatis 用 #{} 而非 ${} |
| XSS | 恶意脚本注入页面，窃取 cookie/劫持操作 | 输出编码（HTML 转义）、CSP 头 |
| CSRF | 伪造用户请求（利用已登录态） | CSRF Token（服务端验证）、SameSite Cookie（Lax/Strict） |

---

## 十八、容器化基础（P2）

**Docker 核心概念**：
- 镜像分层：每层是只读文件系统（FROM + RUN + COPY 各自一层），层复用节省磁盘和拉取时间
- 写 Dockerfile 经验：先拷依赖描述文件（pom.xml/requirements.txt）再 RUN 安装依赖，利用层缓存

**K8s 核心概念速查**：

| 资源 | 一句话 | Java 类比 |
|------|--------|----------|
| Pod | 最小调度单元，可含多个容器共享网络/存储 | 进程组 |
| Service | 固定虚拟 IP（ClusterIP），负载均衡到 Pod | nginx upstream |
| Deployment | 声明期望副本数，滚动更新/回滚 | 发布系统 |

**Java 应用在 K8s 的优雅上下线**：
- 下线顺序：kubectl delete → preStop hook(sleep 10s 等待 Endpoint 摘除) → SIGTERM → Spring graceful shutdown(优雅关闭) → 进程退出
- 关键：preStop 的 sleep 要等 Service 的 Endpoint 切走（通常 5-10s）；Spring 要开 graceful shutdown（server.shutdown=graceful，spring.lifecycle.timeout-per-shutdown-phase=30s）
- 上线：readiness probe 就绪后才接入流量（初始延迟给 JVM 预热时间）

---

## 十九、Elasticsearch（P2）

**倒排索引原理**：
- Term Dictionary（排序的 term 列表，二分查找定位）→ Posting List（包含该 term 的文档 ID 列表 + 词频/位置）
- 与正排索引对比：正排是「文档→词」，倒排是「词→文档」。搜索引擎用倒排实现 O(1) 关键词检索
- Posting List 压缩：FOR（Frame of Reference）+ RBM（Roaring Bitmap），大幅减少内存占用

**写入流程**：
```
写入请求 → 写入内存 buffer + translog（WAL，防丢失）
  → refresh（默认1s）：buffer 写入 segment（可搜索，不可修改）
  → flush（默认30分钟/translog达512MB阈值）：segment 提交到磁盘 + translog 清空
```
关键点：数据写了但没 refresh → 搜索不到（near real-time = 1s 延迟）。

**脑裂问题**：
- 现象：集群中多个节点认为自己是 master，导致数据不一致
- 核心配置：`discovery.zen.minimum_master_nodes` = N/2 + 1（7.x 前）
- ES 7.x+ 用新的集群协调算法，不再需要手动配置此参数
- 面试时说：「脑裂的根本原因是网络分区导致 master 失联。旧版本靠 minimum_master_nodes 防止少数派选主；新版本直接用 Raft-like 协议，自动保证 master 唯一。」

---

## 二十、技术项目管理 & 软素质（P0）

> 高级工程师及以上常考。面试官要的不是"会写代码"，而是"能扛项目、能推事情、能带人"。每节控制在15-20分钟口述量，配合一个真实案例。

### 20.1 多方需求冲突处理

**核心思路**：资源有限是常态。处理冲突不是"谁声音大听谁的"，而是**建立一套可复用的决策框架**，让业务方信服、让老板放心。

**实操框架（四步法）**：

```
第一步：统一价值标尺 → 用 RICE 模型量化（Reach覆盖面 × Impact影响度 × Confidence把握度）/ Effort投入
第二步：拉齐决策人 → 双周排期会上拉 PD + 技术 + 老板一同定唯一优先级，未被排入的明确告知取舍
第三步：防火墙机制 → 需求统一进 TAPD/Jira 收件箱，PO+技术+PM 三方打分，商业价值≥7且成本≤3才准入当前迭代
第四步：有条件说"是" → 拒绝一句话需求时：追问价值 → 给替代方案 → 接受但需缓冲或砍范围
```

**案例（电商场景）**：

商品详情页改造，同期三个业务方提需求：运营要加秒杀标签、商家后台要改发布流程、数据要埋点升级。拉排期会，用 RICE 打分展示——秒杀标签 Reach 高（大促临近）、Effort 低（前端改组件），排第一；商家后台影响面大但需要2个迭代，拆为两期先上最小可用版；埋点推后一个月但承诺不影响日常报表。关键动作：量化决策依据让老板看到，对未排入需求给了明确时间预期。

**关键细节**：
- 排期会是"决策会"不是"通报会"——会上产出明确优先级排序，不留含糊空间
- 目标对齐比赶进度更重要：对齐"给谁用、解决啥"，可减少约50%后期需求变更

---

### 20.2 排期与风险管控

**核心思路**：排期不是拍脑袋，而是一套**估算→预留→跟踪→预警→应对**的闭环。

**估时方法论**：

| 方法 | 适用场景 | 要点 |
|------|---------|------|
| 三点估算法 | 不确定性高的需求 | (乐观+4×最可能+悲观)/6 |
| 类比估算 | 有相似历史项目 | 参考上次耗时×复杂度系数 |
| WBS拆解 | 大型项目 | 拆到每个子任务≤3人天，责任到人 |

**Buffer 管理**：
- 强制预留15%缓冲（20人天留3天）
- 消耗达到50% → 拉leader评审砍需求
- 倒排期项目：拆 P0（必须）/P1（尽量）/P2（buffer）三层

**风险预案矩阵**：

```
风险类型      识别信号                    预案
人员风险      核心开发请假/离职           关键模块≥2人熟悉、文档可交接
依赖风险      下游团队排期无法对齐         提前摸清对方OKR、准备Mock降级
技术风险      新技术/组件首次使用          提前做POC验证
业务风险      需求评审后发现遗漏           拉测试一起参与需求评审、测试用例前置
```

**里程碑管理**：
- 设3-5个关键里程碑（方案评审→联调通过→提测→预发验证→上线）
- 每个里程碑设检查清单，不通过不进入下一阶段
- 每日站会汇报"有没有阻塞、离里程碑还有多远"，而非"做了什么"

**案例（电商场景）**：

大促秒杀重构项目，20人天排期留3天 buffer。第5天发现 Redis 集群容量评估有误（buffer 消耗40%），立即触发战情室——三方评审后砍掉"活动分享有礼"功能（释放2人天），集中攻坚 Redis 热点 Key（本地缓存+拆Key）。核心秒杀链路按时上线，砍掉的功能推到下个迭代。

---

### 20.3 跨团队协作冲突

**核心思路**：跨团队协作的本质不是"沟通技巧"，而是**利益对齐 + 机制保障 + 向上借力**。

**四类典型冲突应对**：

| 冲突类型 | 应对策略 | 兜底方案 |
|---------|---------|---------|
| 依赖团队延期 | 立项前摸清对方季度OKR，把你的需求包装成他的KPI | 准备Mock降级方案，不等对方 |
| 接口契约变更 | 联调前搞契约对齐会，双方签字确认，变更走审批 | 拉双方leader进群，拿数据说话 |
| 线上责任归属 | 先止血再定位最后归因，复盘拿日志/时间线说话 | 不吵架，调用链截图+日志说话 |
| 多产品方打架 | 确定唯一需求方，让产品间先对齐，技术不站队 | 给出可行性+成本对比，让产品决策 |

**推动不配合同事的策略**：
1. 利益绑定：搞清楚对方的 KPI，把需求变成帮他完成 KPI
2. 公开透明：共享表格写明责任人/截止日/进度，抄送双方 leader
3. 降低对方负担：主动出初版方案，对方缺资源时主动补位
4. 先私下对齐再开正式会：正式会上反对你成本远高于私下沟通
5. 向上借力不是告状：跟 leader 汇报聚焦"项目有风险、需要协调资源"，不是"XX 不配合"

**案例（电商场景）**：

履约系统对接即时配送服务商。对方接口文档延期一周半，处理方式：① 第一时间升级风险到双方 TL，明确告知对上线日的影响；② 跟我方产品确认是否接受先上顺丰同城、达达后续再加（产品同意砍范围）；③ 跟服务商用 Mock Server 模拟对方接口，我方先完成内部联调。最终核心功能按时上线。

---

### 20.4 技术债与业务需求的平衡

**核心思路**：技术债不是坏东西，坏的是"没有计划地欠、没有纪律地还"。

**技术债四级管理**：

| 级别 | 定义 | 处理策略 | 例子 |
|------|------|---------|------|
| P0 致命债 | 马上要炸，影响线上 | 立即修复，不受迭代约束 | 连接泄漏、缓存穿透打挂DB |
| P1 高危债 | 迟早炸，效率严重受阻 | 下个迭代必须带 | 核心模块无单测、SQL无索引 |
| P2 慢性债 | 拖累效率不致命 | 每迭代带1-2个，搭车重构 | 重复代码、魔法数字 |
| P3 良性债 | 战略性欠债，有计划 | 登记看板，设偿还截止日 | 为上线先用简单方案 |

**争取重构排期的四个话术（用业务语言）**：
1. 翻译成效："订单查询从2秒降到200毫秒，投诉减少XX%"
2. 亮故障数据："这个模块近3个月线上故障4次，每次影响XX笔订单"
3. 算 ROI："投入3天重构，之后每个需求省1天，两个月回本"
4. 搭车重构：改支付模块顺带优化数据表设计，不单独要排期

**"搭车重构"策略（最实用）**：
- 每个迭代20%容量用于技术优化，且必须跟当前业务功能关联
- 红线：不搞大面积重写，做局部的外科手术式重构

**案例（电商场景）**：

商品中心库存扣减逻辑——800行单体方法，每次改都要回归测试。没有单独要排期，等"预售库存扣减"需求时搭车重构。用策略模式拆成独立策略类（普通/预售/秒杀），新需求用新架构实现，老逻辑逐步迁移。业务需求按时上线，后续库存需求开发效率提升约40%。

---

### 20.5 线上问题处理与复盘文化

**核心思路**：面试官要听的不是"我们做了复盘"，而是**你具体怎么应急、怎么定级、怎么推动改进落地**。

**应急响应流程**：

```
故障发现 → 5分钟响应确认 → 拉故障群（明确指挥官）
  → 分级定级（P0/P1/P2）→ P0/P1 立即通知TL/总监
  → 先止血（回滚/降级/开关），再定位根因
  → 恢复后保留现场（至少1台机器不重启，留日志/Dump）
  → 24小时内出第一版故障报告
```

**故障定级**：

| 级别 | 标准 | 响应要求 | 举例 |
|------|------|---------|------|
| P0 | 核心链路不可用、资损、数据泄露 | 5分钟/30分钟恢复 | 下单失败、扣款未到账 |
| P1 | 部分用户受影响、次要功能不可用 | 15分钟/2小时恢复 | 优惠券领取失败 |
| P2 | 边缘功能异常 | 1小时响应 | 后台报表延迟 |

**复盘核心原则**（阿里/京东文化）：
- 基于事实和日志时间线，不做主观推测
- 5 Why 追问根因：为什么会出？→ 为什么没发现？→ 为什么测试没覆盖？→ 为什么设计没考虑？→ 为什么流程没卡控？
- 产出 ToDo：每条改进措施明确负责人、截止日、验收标准
- 跟踪闭环：下次迭代回顾会第一个环节检查上次复盘改进项落地情况

**案例（电商场景）**：

大促库存超卖复盘。表象：秒杀库存扣到负数。时间线还原：DB 扣库存用了 `where num >= ?`，但高并发下 Redis 缓存与 DB 不一致，多请求同时通过 Redis 校验。5 Why 追问后根因：库存模块是公共 util 类，不属于任何业务域 code review 范围，方案缺陷无人发现。改进措施：① 库存扣减统一收口到库存中心，禁止各业务直操库存表（1周）；② 扣减改 Lua 脚本原子操作（2周）；③ 核心模块设 Code Owner，变更必须 Owner 审批（立即生效）。

---

### 20.6 综合场景串讲模板（5分钟版）

被问"讲一个你主导的最复杂的项目"时，用这个结构：

```
1. 背景（30秒）：项目目标、规模、涉及团队数
2. 核心挑战（30秒）：最大的1-2个难点
3. 我的决策（2分钟）：用了什么方法论、做了什么取舍、为什么
4. 踩过的坑（1分钟）：出了什么问题、怎么应对
5. 结果与复盘（1分钟）：上线数据、经验沉淀、如果再做的改进
```

**关键提醒**：讲决策时突出"我"——"我判断核心风险是XX，所以我主动做了XX"。面试官听的不是项目有多牛，而是你在其中的角色和判断力。

---

## 二十一、系统稳定性（P1）

> 架构师面试的「系统稳定性」不是在考某个工具怎么配，而是在考**全局稳定性视角**：从流量入口到数据落盘，从日常运维到故障应急，你有没有一套完整的思路。以下按 5 个子话题展开，每个话题 15-20 分钟面试口述量。

### 21.1 服务降级策略（熔断、限流、降级）

**面试话术（30秒总起）**：
> 「系统稳定性的第一道防线是流量防护，核心三板斧是限流、熔断、降级。限流保护自己不被冲垮，熔断保护自己不被下游故障拖死，降级在资源不足时丢掉非核心功能保核心链路。我们的线上策略是：接入层网关做全局限流，服务层对下游依赖做熔断，业务层对非核心功能做降级开关。三层各司其职，逐级兜底。」

**限流**

| 策略 | 原理 | 适用 |
|------|------|------|
| 令牌桶 | 固定速率放令牌，请求拿令牌；桶满允许突发 | 网关层、秒杀 |
| 滑动窗口 | 统计过去 N 秒请求数，超过阈值拒绝 | 精确 QPS 控制 |
| 漏桶 | 请求进桶匀速流出，超过容量丢弃 | 需平滑流量的场景 |
| 自适应 | 根据 CPU/RT 动态调整阈值 | 无法精确预估容量的场景 |

**熔断 — 三态模型**（必须能画出）：

```
闭合(Closed) → [失败率 > 阈值] → 打开(Open) → [冷却时间到] → 半开(Half-Open)
    ↑                                                              ↓ 试探成功 → 闭合
    └──────────────────────────────────────────────────────────────┘ 试探失败 → 打开
```

Sentinel 三种熔断策略：**慢调用比例**（核心接口，P999 为阈值）、**异常比例**（下游明确报错）、**异常数**（低流量接口）。

**降级三层递进**（美团"战狼"项目实践）：

| 层级 | 触发条件 | 操作 |
|------|---------|------|
| 1 级 | 负载 > 预警水位 | 关闭非核心功能（动态皮肤、推荐） |
| 2 级 | 负载继续上升 | 本地缓存替代实时计算 |
| 3 级 | 濒临崩溃 | 低优请求返回友好提示页 |

**案例（可讲）**：2022 年美团双 11，通过智能流量削峰将 80% 优惠券查询引流至边缘节点（CDN + 本地缓存），核心数据库 QPS 稳定在 5 万/秒内。关键设计是把压力分散到离用户更近的节点。

---

### 21.2 监控告警体系

**面试话术（30秒总起）**：
> 「可观测性 = Metrics + Tracing + Logging 三位一体。Metrics 告诉你『出问题了』，Tracing 告诉你『哪个环节出的』，Logging 告诉你『为什么出』。线上用 Prometheus + SkyWalking + ELK 这套组合。」

**黄金指标（Golden Signals）**：

| 指标 | 告警示例 |
|------|---------|
| 延迟 | P99 > 500ms |
| 流量 | QPS 突降 50% 或突增 200% |
| 错误 | 错误率 > 1% |
| 饱和度 | CPU > 80%、线程池队列 > 80% |

**告警降噪三维度**：分级（P0 电话/P1 30min/P2 次日）、收敛（同一根因聚为一条）、抑制（灰度期间抑制对应告警）。

**链路追踪基本功**：TraceId 全链路透传（HTTP Header/MQ 元数据）→ 慢 Trace 钻取到耗时最长的 Span → 定位具体 SQL/接口。

**案例（可讲）**：阿里双 11 场景，ARMS 鹰眼全链路追踪 + Isolation Forest 异常检测 + Sentinel 自动限流。2023 年双 11 把一次订单超时故障的 MTTR 从 45 分钟压缩到 8 分钟。

---

### 21.3 故障应急响应

**面试话术（30秒总起）**：
> 「大厂通用应急标准是 **1-5-10**：1 分钟发现、5 分钟响应（定位到大致原因）、10 分钟止损。核心原则：**先止损，后根因**——不要在生产环境排查根因，先把业务拉回来。」

**故障全生命周期**：发生 → 发现 → 响应 → 定界 → 定位 → 止损 → 恢复

**止损三板斧**（必须脱口而出）：

| 手段 | 适用 | 关键 |
|------|------|------|
| 回滚 | 变更引起（占 70% 线上故障） | 5 分钟内完成 |
| 降级 | 非核心功能拖垮核心链路 | 开关提前埋好 |
| 切流 | 单机房/单集群故障 | 依赖多活能力 |

辅助手段：限流（保护过载服务）、扩容（HPA 加机器）、重启（内存泄漏速效药）、隔离（踢掉异常节点）。

**应急协作 SOP**：建群拉人 → 通报进展（每 15 分钟） → 决策升级（10 分钟升 TL、30 分钟升总监） → 恢复后验证业务指标回正。

**复盘产出三类 Action**：技术改进（补超时/补幂等）、流程改进（强制走灰度）、监控补全（覆盖盲区）。复盘文档要素：时间线 + 5 Why + 影响量化 + 责任人 + Deadline。

**案例（可讲）**：2025/7 美团外卖订单突破历史峰值触发限流保护，部分地区短时异常。官方回应"触发限流保护，非系统崩溃"——限流在关键时刻起了保护作用。应对：优惠券延期 + 商家评分不受影响回溯。典型「先止损（限流），后安抚（补偿）」。

---

### 21.4 灰度发布与回滚

**面试话术（30秒总起）**：
> 「灰度发布的核心是**全链路标签路由**——从接入层到中间件层，灰度标记全链路透传。发布节奏：5% → 观测 30 分钟 → 30% → 观测 → 100%。每次发布必须保证**可灰度、可监控、可回滚**三个能力同时具备。」

**全链路灰度四层**：

| 层级 | 机制 |
|------|------|
| 接入层 | Nginx/网关按 Cookie/Header 分流 |
| 网关层 | Gateway GlobalFilter 读灰度标记路由 |
| 服务层 | Nacos 元数据 + LoadBalancer 选灰度实例 |
| 中间件层 | 流量染色透传到 MQ/DB 影子队列/表 |

**关键细节**：
- 按用户 ID hash 优于按比例随机（同一用户始终同一版本）
- 灰度标记必须全链路透传（Feign 拦截器 + Dubbo Filter），防流量"逃逸"
- 回滚预案：保留最近 3 版本、配置一键回退、Schema 向前兼容（先加列不删列）

**案例（可讲）**：字节跳动推荐系统 Python→Java 迁移。1% 内部用户金丝雀 + 双写对比验证 72h → 按用户等级分层放量（10% → 30% → 100%）。零故障迁移，日均请求能力提升 2 倍。关键设计：金丝雀阶段做**正确性验证**（双写对比），灰度阶段做**性能验证**（逐步放量）。

---

### 21.5 依赖治理（强弱依赖、超时控制、重试策略）

**面试话术（30秒总起）**：
> 「依赖治理回答三个问题：这个依赖死了我的服务会怎样？（强弱依赖）、我等它多久算超时？（超时控制）、失败了要不要再试？（重试策略）。美团依赖治理已覆盖 500+ 服务、2 万+ 接口和 8000+ 下游依赖。」

**强弱依赖识别**：

| 类型 | 策略 |
|------|------|
| 强依赖（失败→核心流程阻断） | 超时配短、重试配少（1-2 次）、冗余部署 |
| 弱依赖（失败→不影响核心） | 熔断 + 降级（兜底数据/跳过） |

识别方法：代码走查（有 try-catch 兜底 = 弱依赖）、故障注入（注入故障观察行为）、流量回放（自动化分析）。

**超时控制**：连接超时 1-3s，读取超时取 P999 + buffer。铁律：**所有下游超时之和 < 上游调用方超时**，否则上层超时了下层还在跑。

**重试铁律**：
1. 只有**幂等**接口才重试
2. 设**最大重试比例**（≤15%），防重试风暴
3. 不同层不重复重试（网关重试了，服务层就别再试）

**备份请求**：超 P90 耗时未返回时发起第二次调用，谁先返回用谁，可大幅降 P999。

**案例（可讲）**：大众点评账号服务——Redis 主缓存抖动时自动切换至内部缓存 Cellar 降级。典型「弱依赖熔断 + 降级」组合。核心教训：有兜底才叫弱依赖，没有兜底默认是强依赖。

---

### 21.6 稳定性总览（面试总结用）

```
                    事前预防
                  ┌──────────┐
                  │ 架构评审   │
                  │ 容量规划   │ ←─ 事后改进反哺事前
                  │ 压测演练   │         ↑
                  └─────┬────┘         │
                        ↓              │
         ┌──────────────────────────────┤
         │       事中处理               │
         │  发现(监控) → 响应(SOP)     │
         │  → 定界 → 定位 → 止损       │
         │  三板斧：回滚/降级/切流      │
         └──────────────┬───────────────┤
                        ↓              │
                  ┌──────────┐         │
                  │ 事后复盘   │ ───────┘
                  │ 5Why根因   │
                  │ 改进落地   │
                  └──────────┘
```

**一句话总结**：系统稳定性不是某个工具或配置，而是「预防 → 发现 → 止损 → 复盘 → 改进 → 再预防」的**持续闭环**。


---

## 二十二、性能优化实战（P1）

> **交叉引用**：本节讲排查框架和方法论。具体技术细节见 [六、MySQL 深度](#) 的 SQL 优化、[十二、JVM & 故障排查](#) 的调优案例。
>
> **面试策略**：首答只讲方法论（22.1）+ 1个你最熟的案例作为主干，其余子话题是追问展开的备查材料。

### 22.1 性能优化的方法论

#### 核心思路

**"建立基线 -> 瓶颈定位 -> 分层优化 -> 验证闭环，绝不靠猜。"**

#### 关键细节

**1. 建立基线**
优化前必须用数据说话，至少知道当前系统长什么样。
- 接口维度：P50/P90/P99 延迟、QPS、错误率
- 资源维度：CPU 使用率、堆内存/非堆内存、GC 频率和耗时、线程数
- 数据维度：慢 SQL TOP 10、缓存命中率、DB 连接池使用率

不要一上来说"这个接口慢"，要说"P99 从日常 200ms 恶化到 2.3s，出现在 20:00-21:00 高峰时段"。

**2. 瓶颈定位**
核心原则：**逐层缩小嫌疑范围，每一步用数据验证。**
- 先看系统全局（CPU/内存/GC/线程），判断是大类问题
- 再追具体链路（trace/日志），定位到方法级别
- 最后看代码细节（参数/返回值），锁定根因

**3. 分层优化**
| 层级 | 典型瓶颈 | 优化手段 | 收益量级 |
|------|---------|---------|---------|
| 客户端/前端 | 重复请求、大报文 | 节流防抖、按需加载、CDN | 50%+ |
| 网关层 | 未过滤的无效流量 | 限流、鉴权前置、静态化 | 拦截 90%+ 无效流量 |
| 应用层 | 锁竞争、N+1 查询、大对象 | 异步化、并行化、缓存 | 数倍-数十倍 |
| 中间件层 | 慢 SQL、Redis 大 key、MQ 积压 | 索引优化、拆分大 key、扩分区 | 数倍-百倍 |
| 基础设施层 | 网络抖动、磁盘 IO 瓶颈 | 升级 SSD、扩容、就近部署 | 线性提升 |

**4. 验证闭环**
- 优化后回到"建立基线"那套指标体系，对比前后数据
- 压测验证：在预发环境按生产流量 1.5 倍压测，确认不退化
- 灰度上线：先 10% 流量验证，观察 30 分钟无异常再全量

#### 可讲案例

**得物商品详情页 QPS 优化（虚构框架，真实思路）**
- 基线：大促期间商品详情 P99 达到 1.8s，QPS 峰值 8000
- 定位：trace 发现 80% 耗时在查询价格服务（串行调了 3 个下游）+ Redis 热点 key 过期后击穿
- 优化：价格查询改为 CompletableFuture 并行 + Caffeine 本地缓存兜底 + 热点 key 永不过期
- 验证：预发压测 QPS 15000 下 P99 稳定在 280ms，上线后大促零故障

---

### 22.2 常见性能瓶颈定位工具和方法

#### 核心思路

**"工欲善其事，不必全都会，但核心三板斧必须熟练：Arthas（在线诊断）、JVM 监控（趋势分析）、EXPLAIN（SQL 分析）。"**

### 工具矩阵（按使用频率排序）

| 工具 | 定位 | 核心能力 | 一句话口诀 |
|------|------|---------|-----------|
| **Arthas** | 在线诊断首选 | trace/watch/tt/dashboard/profiler | 无须重启，线上秒级定位 |
| **JVM 监控** | 趋势+告警 | Prometheus + Grafana / 阿里 ARMS | 看趋势看异常，不是看完就完 |
| **GC 日志** | GC 问题定位 | `-Xloggc` + GCViewer 分析 | GC 频率和暂停时间是金指标 |
| **jstack/jmap/jstat** | JDK 自带三件套 | 线程/堆内存/GC 统计 | 没有 Arthas 时的底线能力 |
| **MAT** | 堆 dump 分析 | 支配树、泄漏嫌疑报告、OQL | 内存泄漏终极大招 |
| **EXPLAIN** | SQL 诊断 | type/key/rows/Extra | 每条慢 SQL 必先 explain |

#### 关键细节

**Arthas 三板斧（面试必须能讲出来）**

```bash
# 1. dashboard -- 全局健康检查
dashboard
# 看：CPU 哪个线程高、GC 频率、堆内存曲线

# 2. trace -- 追踪方法调用链，定位最慢节点
trace com.xxx.controller.OrderController getDetail '#cost > 100' -n 5
# 输出示例：1200ms → 1195ms 在 OrderServiceImpl.getOrderById()
# 继续 trace 下一层，直到锁定根因

# 3. watch -- 观测方法入参/返回值/异常
watch com.xxx.service.OrderServiceImpl getOrderById "{params,returnObj}" -x 2
# 看：参数是否符合预期、返回值是否过大、异常信息
```

**偶发慢请求的终极武器 -- tt (Time Tunnel)**
```bash
tt -t com.xxx.controller.OrderController getDetail   # 记录所有调用
tt -l                                                   # 列出记录
tt -i 1008 -p                                           # 用当时的参数重放
```
适用场景：每天只出现 3-5 次的偶发超时，无法稳定复现。先 tt 守株待兔，捕获到后再重放复现。

**JVM 监控关注的三张图**
1. GC 频率图：正常的锯齿状（Young GC 后回落），如果 Full GC 后不回落 -> 内存泄漏
2. 堆内存趋势：Old 区持续增长不回落 -> 泄漏信号；频繁尖峰 -> 大对象分配问题
3. 线程状态分布：大量 BLOCKED -> 锁竞争；大量 WAITING -> 线程池耗尽或死锁

#### 可讲案例

**CPU 100% + 接口超时排查（字节真实案例改编）**
- 现象：某天下午开始 CPU 持续 100%，接口大面积超时
- 排查：`dashboard` 发现单线程占 85% CPU -> `thread -n 1` 定位到 LogAspect 里的正则匹配 -> `watch` 发现某个第三方回调传来 100KB+ JSON 字符串，触发了正则回溯爆炸
- 止血：`mc` + `retransform` 热更新，将正则替换为 `split()`，CPU 立即降回正常
- 根除：发布正式版，增加超长字符串（>2000 字符）截断保护

---

### 22.3 接口慢的排查思路

#### 核心思路

**"从外到内，逐层排除：网络 -> 应用 -> 中间件 -> DB/缓存 -> 下游服务。"**

### 排查框架（5 层漏斗）

**第一层：网络（30 秒排除）**
- 看客户端到服务端的 RTT（ping/curl 测延迟）
- 看是否有 SSL 握手开销（长链接复用情况）
- 排除：网络问题通常在 50ms 以内，除非跨机房/跨国

**第二层：应用层 -- 代码逻辑（核心排查区）**
- Arthas trace 从 Controller 入口开始，逐层追踪
- 重点关注：循环中的 DB/Redis/RPC 调用（N+1 问题）、大对象序列化、复杂的正则/JSON 解析
- 大概率问题出在这一层（占 70% 以上的慢接口根因）

**第三层：中间件 -- 连接池/线程池**
- DB 连接池：`druid` 监控台看活跃连接数，如果长期打满 -> 连接池太小或慢 SQL 太多
- 线程池：看 activeCount/queueSize，如果队列积压严重 -> 下游慢或线程数不够
- Redis 连接池：`lettuce` 默认连接数通常够用，但注意不要和业务线程共用一个 event loop

**第四层：DB/缓存**
- DB：`show full processlist` 看当前执行中的慢 SQL，关注 State 列（Sending data / Creating sort index 等）
- Redis：`slowlog get 100` 看慢命令，关注大 key（`redis-cli --bigkeys`）

**第五层：下游服务**
- 看调用链（如 Skywalking/Zipkin）中下游耗时的占比
- 超时配置是否合理（不要设 30s，电商场景 2-3s 足够，超时即失败快速降级）

### 关键技巧

**"3 个不要"原则**
1. 不要上来就加缓存 -- 先搞清楚慢在哪
2. 不要上来就改 JVM 参数 -- 90% 的慢不是 GC 问题
3. 不要只看平均值 -- P99 才有意义，平均值掩盖毛刺

**快速定位口诀**
> dashboard 看全局 -> trace 追链路 -> watch 看细节 -> 偶发 tt 守株待兔

#### 可讲案例

**接口从 2s 优化到 200ms（循环中远程调用）**
- 现象：某运营后台接口响应 2s+
- trace：发现 `refreshSomeThings()` 耗时 1700ms，进一步 trace 发现一个 HTTP 请求耗时约 100ms，但这个方法被调了 17 次
- 根因：在 for 循环中串行调用了 17 次远程服务，每次 100-200ms
- 优化：合并为批量接口 + CompletableFuture 并行 + 无依赖的调用全部异步
- 结果：2s -> 200ms 以内

---

### 22.4 SQL 优化实战

#### 核心思路

**"每条慢 SQL 必须走完这套 SOP：抓 SQL -> EXPLAIN -> 分析索引 -> 改写或加索引 -> 验证。"**

### SOP 详解

**Step 1：发现慢 SQL**
```sql
-- 开启慢查询日志（生产标配）
SET GLOBAL slow_query_log = ON;
SET GLOBAL long_query_time = 0.5;  -- 500ms
SET GLOBAL log_queries_not_using_indexes = ON;

-- 实时查看正在执行的慢查询
SHOW FULL PROCESSLIST;
```
分析工具优先级：`pt-query-digest`（Percona Toolkit）> `mysqldumpslow` > 直接翻日志。

**Step 2：EXPLAIN -- 关注四个字段**
| 字段 | 含义 | 红线 |
|------|------|------|
| **type** | 访问类型 | 出现 ALL（全表扫描）或 index（全索引扫描）必须优化 |
| **key** | 实际使用的索引 | NULL = 没走索引，立即排查 |
| **rows** | 预估扫描行数 | 实际只需 10 行但扫描 10 万行 -> 索引不合理 |
| **Extra** | 额外操作 | Using filesort / Using temporary 需要关注 |

**Step 3：索引设计与优化**
```
联合索引黄金法则：等值在前，范围在中，排序在后
```
示例：`WHERE status = 1 AND create_time > '2025-01-01' ORDER BY update_time DESC`
最优索引：`(status, create_time, update_time)` -- 等值、范围、排序按序排列。

**Step 4：三大经典优化模式**
| 问题 | 改写前 | 改写后 | 原理 |
|------|--------|--------|------|
| 深翻页 | `LIMIT 100000, 20` | `WHERE id > 上次最大id LIMIT 20` | 避免扫描后丢弃 |
| 索引失效 | `WHERE DATE(create_time) = '...'` | `WHERE create_time >= '...' AND create_time < '...'` | 函数导致索引失效 |
| 隐式转换 | `WHERE phone = 13800138000` (phone 为 varchar) | `WHERE phone = '13800138000'` | 类型转换导致全表扫描 |

**Step 5：大表优化路径（渐进式）**
```
单表优化（索引/SQL） -> 垂直拆分（拆大字段） -> 水平拆分（分库分表） -> 冷热分离（归档）
```
不要一上来就分库分表。千万级单表，索引设计合理的话，大部分查询在 50ms 以内。

#### 可讲案例

**订单表深翻页优化（淘天交易订单表案例）**
- 背景：运营后台订单列表，按创建时间倒序，翻到第 1000 页时耗时 2s+
- SQL：`SELECT * FROM tcorder WHERE buyer_id = ? ORDER BY create_time DESC LIMIT 10000, 20`
- EXPLAIN 结果：type=ref, rows=10020, Extra=Using filesort（多字段排序无法利用索引）
- 根因：LIMIT 大偏移量要扫描 10000+ 行然后丢弃，且 create_time 排序触发了 filesort
- 优化两步走：
  1. 去掉多余的 `order_id` 排序，让排序字段能被单个索引完全覆盖
  2. 改用游标分页：`WHERE create_time < '上次最后一条的时间' ORDER BY create_time DESC LIMIT 20`
- 结果：2s+ -> 30ms

---

### 22.5 JVM 调优实战

#### 核心思路

**"JVM 调优的核心不是背参数，而是会看 GC 日志 + 堆 Dump，用数据驱动力而不是经验主义。"**

### 高频问题速查

**Q1：GC 频率过高怎么办？（Young GC 十几秒一次）**

大概率是**年轻代太小**或**对象分配速率太高**。
- 先看 GC 日志中 Young GC 前后的 Eden 区大小：如果 Eden 很快填满 -> 年轻代太小
- 再看代码：是否有高频创建临时对象的地方（如 for 循环 new 对象、字符串拼接）
- 优先调代码（减少对象创建），其次调参数（增大年轻代）
- G1 下不要手动设 `-Xmn`，让 JVM 自适应，只设 `-XX:MaxGCPauseMillis=200` 目标

**Q2：Full GC 频繁怎么排查？**

三大排查方向：
1. **晋升失败**：对象过早从年轻代晋升到老年代 -> 看 Survivor 区是否太小（GC 日志中 `Desired survivor size`）
2. **大对象直接分配**：`-XX:PretenureSizeThreshold` 没有设或代码分配了大数组 -> MAT 看支配树
3. **元空间不足**：动态生成类太多（CGLIB 代理/动态语言）-> `-XX:MaxMetaspaceSize=256m`

**Q3：内存泄漏怎么查？**

```
jmap -dump:format=b,file=/tmp/heap.hprof <pid> -> MAT 分析 -> Leak Suspects Report
```
MAT 关键操作：
- **Dominator Tree**：按 Retained Heap 排序，看谁占的最多
- **Path to GC Roots** -> Exclude Weak References：看谁在强引用着这个对象
- 常见泄漏源：ThreadLocal 没 remove、静态集合不断 add、未关闭的流/连接、监听器未注销

### GC 选择速查

| 场景 | 推荐 | 理由 |
|------|------|------|
| JDK8 高并发 API | CMS / G1 | CMS 用 -XX:CMSInitiatingOccupancyFraction=75 |
| JDK11+ 高并发 API | G1（默认） | 设 `-XX:MaxGCPauseMillis=200` 即可 |
| JDK11+ 大堆+极低延迟 | ZGC | 亚毫秒级暂停，JDK17+ 生产可用 |
| 批处理/离线计算 | Parallel GC | 吞吐量优先 |

### 真实可讲案例

**案例 1：Survivor 区过小导致对象过早晋升（vivo 频道服务案例）**
- 现象：高峰期 Full GC 每天 8 次，每次 2-3 秒，影响可用性
- 排查：看 GC 日志发现 Survivor 区仅 10-30M（自适应策略导致），大对象直接晋升老年代
- 解决：`-XX:-UseAdaptiveSizePolicy -XX:SurvivorRatio=8`，固定 Eden 和 S 区比例
- 结果：Full GC 从 8 次/天 -> 1.5 次/天

**案例 2：Dubbo FutureAdapter + Jackson ThreadLocal 内存泄漏（vivo 案例）**
- 现象：Full GC 每天 120 次，每次耗时 500ms+
- 排查：堆 Dump 分析发现三个问题叠加：
  1. Dubbo 异步调用 FutureAdapter 引用未及时释放，堆积在老年代
  2. Jackson BufferRecycler 的 ThreadLocal 中持有 char[65536]，复用率极低
  3. 晋升年龄阈值 MaxTenuringThreshold=6 偏小
- 解决：关 Jackson ThreadLocal buffer 复用 + MaxTenuringThreshold 调为 15 + 改用本地缓存替代 Dubbo 异步引用
- 结果：Full GC 从 120 次/天 -> 30 次/天

**案例 3：K8s 环境 GC 线程数陷阱**
- 现象：G1 下年轻代 GC 暂停达到 1869ms，远超预期
- 根因：K8s Pod 限制 4 核，但 JVM 看到宿主机 72 核，GC 并行线程 = 72 * 5/8 = 48 个，48 个线程抢 4 个核
- 解决：`-XX:ParallelGCThreads=4`
- 结果：暂停降到 50ms 以内

---

### 22.6 缓存与异步化对性能的提升

#### 核心思路

**"缓存解决读性能，异步解决写性能。什么时候用、用在哪一级，取决于数据特征和业务容忍度。"**

### 缓存决策框架

**判断三步法：**
1. 这个数据**读多写少**吗？ -> 是，值得缓存（商品详情是，库存不是）
2. 能容忍**多少毫秒的数据不一致**？ -> 决定了 TTL 和更新策略
3. QPS 有多高？ -> 过万考虑本地缓存，几千用 Redis 就够了

**多级缓存架构（按需引入，不追求复杂）**

```
L0: CDN/浏览器缓存（静态资源）
L1: Caffeine 本地缓存（热点数据，微秒级）
L2: Redis 分布式缓存（全量数据，毫秒级）
L3: 数据库（兜底）
```

**关键设计原则：**
- L1 TTL 必须比 L2 短（如 L1 5 分钟、L2 30 分钟），保证数据不一致窗口可控
- 更新时先更新 DB，再删缓存（Cache Aside 模式），不推荐先删缓存后更新 DB
- 热 key 防击穿用"单飞锁"：同一 key 只允许一个线程回源，其余等结果

### 异步化决策框架

**什么时候用异步？**
- 操作**不需要用户立刻看到结果** -> 发通知、写日志、同步到 ES、数据统计
- 操作**需要削峰填谷** -> 秒杀下单、批量导入
- 操作**可并行化** -> 组合查询（商品+价格+库存并行调）

**什么时候不要异步？**
- 用户需要立刻看到结果的强一致性场景
- 还没有想好失败补偿机制

**异步化三层递进**

| 层级 | 场景 | 技术手段 |
|------|------|---------|
| **方法级异步** | 单个耗时操作不阻塞主流程 | `@Async` + 自定义线程池 |
| **编排级并行** | 多个独立下游服务调用 | `CompletableFuture.allOf()` |
| **系统级削峰** | 瞬时洪峰写入 | MQ（RocketMQ/Kafka）|

#### 可讲案例

**案例 1：缓存击穿防护 -- CompletableFuture 单飞锁**
- 场景：商品详情热点 key 在 Redis 过期瞬间，每秒几千个请求穿透到 DB
- 方案：`ConcurrentHashMap` + `CompletableFuture`，同一个 key 只有一个线程去查 DB 并回填缓存，其他线程等同一个 Future 的结果
- 关键代码思路：`map.computeIfAbsent(key, k -> supplyAsync(() -> loadFromDB()).whenComplete((v, e) -> map.remove(k)))`
- 效果：击穿线程数从几千 -> 1，DB 压力立即降下来

**案例 2：下单链路异步化 -- MQ 削峰**
- 场景：秒杀活动 0 点瞬间 5 万 QPS 下单请求打到 DB
- 方案：Redis Lua 原子预扣库存 -> 返回"排队中" -> 发 MQ -> 异步消费创建订单落库
- 效果：前端响应从 500ms -> 50ms，DB 写入 QPS 从万级 -> 百级

**案例 3：接口耗时优化 -- 并行调用下游**
- 场景：商品详情接口需要调 3 个下游服务（商品资料、价格、库存），串行总耗时 450ms
- 方案：CompletableFuture 并行 + `orTimeout(3s)` 防止其中一个服务慢拖垮全局 + CircuitBreaker 熔断
- 效果：450ms -> 150ms（取最大耗时 + 少量编排开销）

---

### 22.7 压测与容量评估（首答首选案例）

#### 核心思路

**"压测不是跑个 JMeter 脚本看 QPS 就行。核心三件事：建模型准确、压测环境不污染生产数据、结果能指导容量规划。"**

### 压测方案设计四要素

**1. 压测模型 -- 不是瞎跑流量**

基于线上真实流量建模，不是随便设个 QPS 往上加。
- **流量漏斗**：100 人进首页 -> 50 人看商品 -> 10 人下单 -> 5 人付款，比例要对
- **数据分布**：不是所有商品都热门，80% 流量打在 20% 的热点商品上（二八原则）
- **压测 QPS 公式**：`目标 QPS = 日常峰值 × 大促系数(3-5x) × 安全余量(1.2x)`

**2. 数据隔离 -- 生产压测不倒灌**

| 方案 | 原理 | 适用场景 |
|------|------|---------|
| 影子库 | 独立压测数据库实例 | 金融级、高安全要求 |
| 影子表 | 同一库中加前缀（如 `test_`）的表 | 电商交易场景（更常用） |
| 流量染色 | 请求头携带压测标记全链路透传 | 必须做的标配 |

关键：压测标记必须在 HTTP header、Dubbo 隐式参数、MQ 消息、异步线程中**全链路透传**，不能出现 RPC 调用时丢标记导致压测数据写入真实库。

**3. 压测执行 -- 递进式施压**

```
基准测试（10% 目标 QPS） -> 爬坡测试（10% -> 50% -> 80% -> 100%） -> 摸高测试（往上加直到出现瓶颈） -> 稳定性测试（100% 跑 30 分钟）
```
不要一上来就全量，逐步施压才能看清系统在哪个水位开始劣化。

**4. 压测分析 -- 看什么指标**
- 核心：P99 延迟 vs QPS 曲线 -- 拐点就是瓶颈水位
- 辅助：CPU、内存、GC、DB 连接数、Redis 命中率、MQ 积压
- 业务正确性：压测期间错误率是否为 0、是否有数据泄漏到生产

### 容量评估

- **单机容量**：压测拐点对应的单机 QPS（比如某接口单机 500 QPS 后 P99 开始飙升）
- **集群容量** = 单机容量 × 机器数 × 0.8（留 20% 冗余应对单机故障）
- **扩容阈值**：当实际 QPS 达到集群容量的 60% 时触发扩容告警

#### 可讲案例

**大促前全链路压测发现连接池瓶颈**
- 背景：某电商大促前做全链路压测，目标 QPS 2 万
- 压测过程：QPS 跑到 1.2 万时 P99 开始劣化，1.5 万时大面积超时
- 排查：数据库连接池 50 个全部打满，且一半连接处于 Sending data 状态超过 2s
- 根因：某慢 SQL 在大流量下被放大，占着连接不释放，导致其他请求排队等连接
- 解决：优化慢 SQL + 连接池扩到 200 + 增加超时熔断（2s 没拿到结果就降级）
- 再压：2 万 QPS 稳定，P99 350ms
- 大促当天：实际峰值 1.8 万 QPS，零故障

---

### 22.8 附录：追问及应答思路

---

## 二十三、技术领导力与团队协作（P0）

> **面试策略**：7个子话题中选2-3个你最熟的准备即可，通常只会被问到1-2个。重点准备 23.1（带新人）+ 23.2（推决策）+ 23.5（资源不足），这三个最高频。

> 高级工程师及以上常考。面试官要的不是"会管人"，而是"能带人、能推事、能建影响力"。

### 23.1 如何带新人/初中级工程师

**面试可能怎么问**：你带过新人吗？你是怎么带的？有没有带不出来的案例？

#### 核心思路

带新人不是"分配任务+检查结果"，而是**建立安全成长环境 + 递进式挑战 + 及时反馈**三步循环。

用一句话讲就是：**让新人在有保护的情况下，做刚好「跳一跳够得着」的事情，然后给具体反馈，而不是给结论。**

#### 关键细节

**任务拆解的"阶梯设计"**：不会直接把一个完整需求扔给新人，而是按难度梯度分配：

```
文档任务(熟悉流程) → Bug修复(熟悉代码) → 独立小功能(建立信心) → 跨模块开发(扩大视野) → 负责一个项目(独立owner)
```

每一级完成，复盘一次，才能进入下一级。跳级大概率出事。

**Code Review 对新人不是挑错，是教学**。对新人代码的审查重点和资深开发完全不同：

| 审查重点 | 对新人的做法 |
|---------|------------|
| 编码规范 | 重点检查，但用"引导式反馈"——"这个场景我们用 try-with-resources 更安全，因为…"，不要说"你怎么又忘关流了" |
| 逻辑正确性 | 关注边界条件、异常处理，新人最常漏的就是这些 |
| 设计合理性 | 不强求最优解，先保证正确，再给一个优化方向让他自己改 |

**成长路径规划的核心是"因材施教"**。入职第一个月做好三件事：

1. **手绘一轮团队技术架构图**——看他对系统的全局理解到哪层
2. **每天记录三个"为什么"**——为什么这样设计、为什么选这个技术、为什么流程长这样
3. **第一迭代在核心链路留下代码痕迹**——实战是最好的融入方式

每周至少一次一对一深度沟通，不是聊"进度怎么样"，而是"你遇到的最困惑的事情是什么"、"你觉得自己哪方面进步最快"。

### 1.3 真实可讲的案例

**电商场景**：带了两个应届生，一快一慢。快的那个两周就开始出活，但 CR 时发现代码风格跳跃、异常处理缺失，就让他在每个 PR 里自己先列 checklist（边界条件/异常场景/日志），改了三个月后不再出这类问题。慢的那个写业务逻辑没问题，但一碰到线上报警就慌——带他做了一个季度的线上问题复盘（每次他先独立分析、再对答案），半年后可以独立值班。

**另一个案例（反面）**：一个中级工程师，独立负责促销模块。任务拆得太细，每个卡都替他定了方案，结果半年后他还是"你给我方案我来实现"，没有自己做决策的能力。后来调整做法：给他一个需求后，要求他自己先出两个可选方案，讲清优缺点，再由我帮他理决策逻辑，逐步建立判断力。

### 1.4 面试口述话术（1分钟版）

> 我带过5个以上初中级工程师。我的方法分三步：第一，任务拆解用阶梯设计，从文档/Bug修复到独立功能再到项目owner，不跳级；第二，代码评审对新人用引导式反馈，讲"为什么"而不是挑刺；第三，每周一次一对一，问的不是进度，是困惑和成长。有一个典型例子：两个应届生一快一慢，快的规范差就强制PR自检，慢的分析弱就带他一个季度线上问题复盘，最后都能独立值班。

---

### 23.2 如何推动技术决策落地

**面试可能怎么问**：你推过一个大家不认可的技术方案吗？跨团队推技术决策，别人不听你的怎么办？

#### 核心思路

推动技术决策不是靠"我是 Leader 所以听我的"，而是靠**先建立共识（为什么必须做）→ 再给方案（怎么做）→ 拉决策人一起拍板**。最忌讳的是自己闷头写了个方案，然后去说服所有人。

#### 关键细节

**别人不听你的，通常有三个原因，需要对症下药**：

| 原因 | 表现 | 应对 |
|------|------|------|
| 不信任你的判断 | "你这个方案靠谱吗？" | 用数据说话，不空谈概念。性能测试结果、线上故障数据、历史踩坑记录，拿出来坐实 |
| 目标不一致 | "我自己的需求都做不完" | 把你的需求包装成帮对方完成 KPI——做过一次"履约系统要求交易团队改接口"，不是直接提需求，而是说"改了这个接口，你们交易超时的告警会少 30%" |
| 缺乏上下文 | "你说的有道理，但我理解不了" | 不抛概念图，画一张交互时序图，所有人围绕同一张图讨论，消解 70% 沟通偏差 |

**跨团队推动的五个关键动作**：
1. **立项前对齐**：先摸清对方团队本季度的 OKR，提前私下聊，别在正式会上突袭
2. **把你的需求翻译成对方的指标**：不说"我要改接口"，说"改完你们这个模块的 RT 能降 200ms"
3. **主动降低对方的参与成本**：我先出初版方案和接口草案，对方只需要 review
4. **公开透明+双方 leader 周知**：共享文档写明责任人/截止日，每周晾晒进度
5. **向上借力不是告状**：跟老板汇报聚焦"项目有风险、需要协调"，不是"XX 团队不配合"

**用"先讲 Why 再讲 How"替代强行命令**。美团干嘉伟带团队时，安排人去标杆城市参观，先让大家亲眼看到"破地方也能做出高业绩"，内心产生冲击后再讲方法。推动有争议的技术决策同理——先带大家看线上故障数据、看用户投诉、看性能瓶颈现场，达成"必须改"的共识之后，再讨论方案。

### 2.3 真实可讲的案例

**电商场景（跨团队推中间件升级）**：要推 Redis Cluster 升级替换单机版。业务团队第一反应是"别动我们线上"。

做法分四步：(1) 先拿业务团队的线上监控数据，展示最近三个月因 Redis 单机故障导致的业务影响（共 3 次，影响订单约 2000 笔），用业务语言说清"不改的风险"；(2) 在灰度环境先跑通全链路，提前做了回滚预案（一键切回单机）；(3) 选择业务低峰期、从边缘服务开始灰度，一周无异常才切核心服务；(4) 每切一个服务，发一份迁移报告给对应业务方（迁移前性能 vs 迁移后性能）。最终零故障完成迁移。

### 2.4 面试口述话术（1分钟版）

> 跨团队推技术方案，我的核心原则是"先讲为什么改，再讨论怎么改"。有一次推 Redis Cluster 升级被业务团队拒绝，我没有硬推，而是先拿他们自己的监控数据说明不改的风险（三个月 3 次故障影响 2000 笔订单），然后在灰度环境跑通全链路、做好回滚预案，最后从低峰期边缘服务起步，切一个发一份迁移报告。零故障完成。关键心法是：让别人从对抗变成同盟，靠的是用他听得懂的语言说清楚对他有什么好处。

---

### 23.3 代码评审文化与技术规范建设

**面试可能怎么问**：你们团队有代码评审吗？是怎么做的？你从零建立过 CR 流程吗？

#### 核心思路

从零建 CR 文化和规范，核心路径是：**先上工具自动化拦截低级问题 → 再定流程（分级评审）→ 最后培养文化（引导式反馈）**。关键认知：人肉评审的重点在设计和逻辑，格式和规范交给机器。不要一上来就追求完美评审，先动起来，再迭代。

#### 关键细节

**分四阶段推进**：

**阶段一：先上工具，别让人做机器的事**

引入 SonarQube/P3C 插件 + CI 自动检查。提交代码时自动扫描，不通过直接阻断合并。这一步不依赖人的自觉，效果立竿见影。

**阶段二：分级评审机制**

不是所有代码都需要同等强度的评审：

| 级别 | 适用场景 | 评审要求 |
|------|---------|---------|
| L1 严格 | 支付/资金/安全敏感 | 架构师 + 2 位资深开发，24h 内审完 |
| L2 标准 | 业务逻辑/新功能 | 1 位同组高阶 + 1 位交叉评审，48h 内 |
| L3 轻量 | 后台管理/内部工具 | 1 位同级开发，96h 内 |

**阶段三：建立评审者的 Checklist**

每个评审者逐项检查：设计是否合理、边界条件是否考虑、SQL 是否有性能问题、异常处理是否完备、日志是否够定位问题。不用全记住，但必须过一遍。

**阶段四：培养文化**

- 用"建议"替代"批评"："这里用 try-with-resources 更安全" 而非 "怎么又忘关流了"
- 推行"1+1 反馈"：每条改进建议必须搭配一个优点
- Leader 必须以身作则参与 CR，不搞"我有特权不被人审"
- 把评审工作量纳入迭代容量规划（一般占开发工时的 8-12%）

**PR 的原子性要求**：一个 PR 只做一件事，不超过 400 行。太大直接打回拆分。这是提升评审效率最关键的一条规则。

### 3.3 真实可讲的案例

**电商场景（从零建 CR 流程）**：接手一个 5 人小组，之前没有 CR 文化，上线靠自测，线上故障频发。

做法：(1) 先上 P3C 插件 + SonarQube，提交时自动扫描，不通过不能合代码——这一步零阻力，因为是机器检查；(2) 定规则：所有 PR 必须至少 1 人 Approve 才能合并，核心模块至少 2 人；(3) 我带头每天花 30 分钟做 CR，每个 PR 评论不少于 3 条，而且每条评论都附上"为什么"的解释；(4) 每周复盘会上展示这周的 CR 数据，公开表扬提出关键问题的评审者。

结果：两个月后，线上故障从月均 5-6 次降到 1-2 次，新人首次 CR 通过率从大约 40% 提到 80% 以上。关键在于 Leader 带头 + 工具先行降低执行阻力。

### 3.4 面试口述话术（1分钟版）

> 我在一个 5 人小组从零建立过 CR 流程。分三步：第一步上工具，P3C+SonarQube CI 自动拦截，不服不行；第二步定分级评审，支付级模块必须架构师+2人审，管理后台轻量审；第三步培养文化，我自己每天花 30 分钟带头做 CR，每条评论附"为什么"，每周公开表扬好评审。两个月后线上故障从月均 5-6 次降到 1-2 次，新人 CR 通过率上了 80%。核心心法：先机器后人，先流程后文化，Leader 自己不做就没资格要求别人做。

---

### 23.4 如何处理团队内部技术分歧

**面试可能怎么问**：团队里两个人对技术方案争执不下，你怎么处理？你自己选的技术方案被否决过吗，怎么应对？

#### 核心思路

技术分歧的本质通常不是"谁对谁错"，而是**双方站在不同视角看到了同一个问题的不同侧面**。处理的关键不是当裁判判定 A 赢 B 输，而是**把双方关注的维度都拿出来，用数据和原则做结构化决策，把个人之争转化为方案对比**。

#### 关键细节

**逐点争论是最大的坑**。对方每提一个技术风险，你立即逐条反驳——这会让讨论变成"论点爆炸"、聚焦次要细节而忽略核心矛盾。更好的做法是：聚焦核心正向论点，一次只讨论 1-2 个关键问题。

**三步处理法**：

```
第一步：识别方案 → 把双方方案写成文字，列到同一张表里
第二步：归类质疑 → 分为三类：
   - 有利于优化原方案且可行的 → 纳入优化
   - 是问题但暂时无法解决 → 略过或作为未来储备
   - 与原方案有较大不同但也可行 → 列为独立新方案
第三步：结构化决策 → 用决策矩阵（可维护性/性能/开发成本/风险 加权打分）
```

**决策矩阵（量化工具）**：当双方僵持不下，不要比声音大，比数据：

| 维度（权重） | 方案A 评分 | 方案B 评分 |
|------------|-----------|-----------|
| 可维护性(30%) | 8 | 6 |
| 性能(25%) | 6 | 9 |
| 开发成本(25%) | 7 | 4 |
| 团队熟悉度(20%) | 8 | 5 |
| **加权总分** | **7.35** | **6.15** |

算完分数后，再讨论分数本身是否合理。这个过程让讨论从"我认为"变成了"我们来看看哪个维度可以调整"。

**分歧升级的底线**：如果两人讨论 30 分钟仍无法一致，不继续耗——升级到 TL/架构师介入仲裁。但仲裁的依据必须是客观标准（数据/原则），而不是"我级别高听我的"。

**当你的方案被否决时**：
1. 先服从团队决策，百分百投入执行，不搞"我早就说不行"的马后炮
2. 异步复盘，对比两个方案在核心工程切面上的差异
3. 在合适的复盘节点（比如上线后回顾），带着实际数据做二次对齐。用证据说话，不争执

### 4.3 真实可讲的案例

**电商场景（MQ vs 定时任务之争）**：订单状态同步逻辑，一派人主张用 RocketMQ 延迟消息，一派人说现有定时任务够用别引入新组件。

处理方式：不站队，先让大家把两个方案的优缺点列在同一张表上（MQ：实时性好但增加运维复杂度；定时任务：简单但也有漏扫风险）。然后用决策矩阵从可靠性/延迟/运维成本/开发工作量四个维度打分。最终 MQ 方案胜出，但附带了一个约束——先在小流量业务验证一个月再推广。这个约束是反对派提出来的，我明确认可并写进了方案。后来推广顺利，反对派也觉得自己的声音被认真对待了。

**补充体会**：技术分歧中，最危险的不是公开争论，而是"会上点头、会后不动"的沉默分歧。所以每次方案评审后，我会发会议纪要，明确"定了什么、为什么、谁做什么"，确保大家都认账。

### 4.4 面试口述话术（1分钟版）

> 我处理技术分歧的原则是：把个人之争转化为方案对比。有一回订单同步逻辑，MQ 派和定时任务派僵持不下。我不站队，让他们把两个方案的优缺点写在同一张表上，用决策矩阵从可靠性/延迟/运维成本/开发量四个维度打分。最终 MQ 胜出，但反对派提的"先在小流量验证一个月"我写进了方案，这是个好约束。事后反对派也觉得被认真对待。核心心法：用数据代替情绪，承认反对意见中的合理部分，分歧就能变成更高质量的决策。

---

### 23.5 如何在资源不足时完成目标

**面试可能怎么问**：有没有遇到过人手不够、时间紧、需求还多变的情况？你是怎么应对的？

#### 核心思路

资源不足时，技术管理者最重要的能力不是"拼命加班"，而是**做减法——有纪律地取舍，有节奏地交付**。核心公式：先分层（什么必须做/什么可以不做），再聚焦（80% 精力打 20% 关键战），最后倒推（从终点拆到每一个里程碑）。

#### 关键细节

**第一层：MUST/SHOULD/COULD/WON'T 分层**

这是最基础也最重要的动作。每次迭代开始前，把所有需求过一遍四象限：

| 类别 | 处理 | 关键规则 |
|------|------|---------|
| Must | 必须做 | **Must 列表一旦超过团队容量的70%，就是在自欺欺人**。必须砍范围或补资源 |
| Should | 应该做 | 重要但可以等，下一迭代优先排 |
| Could | 可以做 | 锦上添花，有空再做 |
| Won't | 不做 | 明确告知"这轮不做"，但不代表永远不做 |

**第二层：紧急需求插队的防御机制**

紧急插队是破坏性最强的问题。不是堵死，而是建规则：

1. **双通道机制**：常规需求走评审，紧急需求走绿色通道——但绿色通道有硬准入条件（只有线上阻断性故障、重大客户履约危机才能走）
2. **预留应急资源池**：10-20% 产能专门应对突发
3. **插队必须附带代价评估**：凡挪用主线人力的临时需求，强制输出影响评估——"会造成哪个项目延期多久、带来什么损失"
4. **每月复盘所有紧急需求**：区分"不可预见的突发"和"前期规划缺失导致的人为紧急"，后者从源头堵

**第三层：用 RICE 模型量化排序，让取舍有据可查**

当你必须对业务方说"这个做不了"，不能只说"没资源"，要说"根据 RICE 评估，这个需求的得分在当前迭代排不进前 3，我们计划放在下个迭代"。

**第四层：从终点倒推里程碑**

确定 DDL → 拆关键步骤 → 预估各环节耗时（多留 15% buffer）→ 落实到日历。每日站会不问"做了什么"，问"离里程碑还有多远、有没有阻塞"。

### 5.3 真实可讲的案例

**电商场景（大促前需求爆发）**：临近双十一，四个业务方同时提了 11 个需求，团队就 5 个人。

做法：(1) 先用 Must/Should/Could/Won't 分层，把 Must 从 11 个砍到 4 个；(2) 对 4 个 Must 用 RICE 打分排序，结果是秒杀标签（Reach 高+Effort 低）排第一，数据埋点排到最后；(3) 预留 15% 人天做 buffer，并在同步会上给未排入的需求方逐一说明理由+给时间预期；(4) 每两天一次站会，只盯"离里程碑还有多远"。

过程中有一个临时紧急需求——运营要加一个会场活动页，被我拒绝了（不符合绿色通道准入标准），但给了替代方案：用已有的活动模板配置而非重新开发。运营接受了。

最终 4 个核心需求按期上线，大促零故障。关键是：让每个业务方都知道自己排在什么位置、为什么、什么时候能做，而不是一句"做不了"。

### 5.4 面试口述话术（1分钟版）

> 资源不够时的核心动作是做减法，不是加班。有一次双十一前 4 个业务方提了 11 个需求，团队 5 个人。我先用 Must/Should/Won't 分层砍到 4 个 Must，再用 RICE 打分定优先级，预留 15% 人天做 buffer。对没排上的需求方，逐一说明理由+给时间预期。中间运营要插队做活动页，我看了下不符合紧急通道标准，给了替代方案——用已有模板配置而非开发，运营接受了。最终核心需求全部上线，大促零故障。关键心法：取舍要有据可查，沟通要给出替代方案而不是一句"做不了"。

---

### 23.6 技术分享与知识沉淀

**面试可能怎么问**：你们团队有技术分享会吗？你怎么推动知识沉淀？你有没有做过文档建设？

#### 核心思路

技术分享和知识沉淀的本质不是"写文档"，而是**让个人经验变成团队资产，降低人员变动带来的风险和效率损失**。推动的关键不是定 KPI 要求每人写多少篇，而是让人感受到"写文档对自己也有好处"。

#### 关键细节

**知识沉淀按"从轻到重"分层建设**：

| 层级 | 形式 | 目的 | 频率 |
|------|------|------|------|
| 轻量 | 项目设计文档 + 技术方案 | 每个需求都有方案记录 | 每次开发 |
| 中量 | 故障复盘报告 + 最佳实践文档 | 把坑变成经验库 | 每次故障/每季度 |
| 重量 | 团队编码规范 + 新人入职手册 | 降低新人上手成本 | 持续迭代 |

**推动文档文化的三个关键动作**：

1. **Leader 先写**。你自己不写，别要求别人写。每次我做完设计评审，都会把文字版方案留在语雀/飞书知识库，形成惯例后团队自然跟上。

2. **不追求完美文档**。不要搞"先写个完整的设计文档"这种高门槛要求。从最简单的做起：每次 CR 中值得记录的技术讨论，截个屏贴到知识库加一行注释。等积累多了再整理。

3. **文档要有"消费场景"**。纯堆砌的文档没人看。好的文档要关联到具体场景：新人入职看哪个、排查问题看哪个、做技术选型看哪个。每个文档都标注"什么时候用"。

**技术分享会的进阶设计**：

- **不要固定主题只让资深的人讲**。轮值制：每周一个人，轮流分享。资深讲架构和踩坑，新人讲最近学到的一个技术点。新人讲的好处是他刚学完，讲得最清楚。
- **形式多样化**：线上分享（日常）+ 代码走读会（每迭代，挑代表性代码集体走读）+ 季度专题（深度主题，如"这一年我们踩过的 10 个 MySQL 坑"）
- **把 CR 本身当成学习平台**：推行"提问式评审"——"为什么这里用窗口函数而不是子查询？" 这类问题触发深度讨论，其实比正式分享会更有效

### 6.3 真实可讲的案例

**电商场景（文档从零到有）**：接手团队时发现知识全在几个人脑子里，有人请假就有人来问"这个接口干嘛的"。

做法：(1) 先建一个语雀知识库，按模块建目录（商品/订单/支付/履约）；(2) 定最低要求——每个模块至少有一篇"新人上手文档"，包含：模块职责、核心接口、关键表结构、常见问题；我带头写了两个模块；(3) 定规则：凡是生产故障，复盘报告必须归档到知识库，按"根因-影响-改进项"模板写；(4) 鼓励不做完美主义：CR 中讨论到一个有意思的技术点，截张图贴到知识库加一行注释，算完成一次沉淀。

半年后，知识库从 0 到 40+ 篇文章，新人上手时间从之前的两周缩短到 3-4 天。关键不是文档写得多好，而是**降低了写文档的启动门槛**。

### 6.4 面试口述话术（1分钟版）

> 我主导过一个团队的知识库从零建设。核心做法：第一，我带头写，先产出两个模块的新人上手文档做示范；第二，降低门槛——不强求完美文档，CR 中讨论到一个好技术点，截屏加一行注释就算一次沉淀；第三，每个文档标注"什么时候用"——新人入职看哪个、排查问题看哪个。半年后知识库从 0 到 40+ 篇文章，新人上手从两周缩短到 3-4 天。核心心法：知识沉淀最大的敌人是启动门槛太高，先动起来比写好更重要。

---

### 23.7 如何在团队中建立技术影响力

**面试可能怎么问**：你在团队里是公认的技术核心吗？别人为什么认可你的技术判断？

#### 核心思路

技术影响力不是靠 Title 给的，是靠**持续做出正确的技术判断 + 让别人因为你而变得更好**积累出来的。一句话总结：当别人遇到技术难题时第一个想到来问你，你的影响力就建立了。

影响力建立的三个支柱：**技术判断力（你选的方案反复被验证是对的）→ 交付信用（你说 3 天完成不会变成 5 天）→ 赋能他人（你帮过的人成长了）**。

#### 关键细节

**技术判断力的积累路径**：

- 每次技术选型不只是选方案，更重要的是**预判这个方案在什么情况下会出问题**，并提前准备应对。如果你能连续预判对 3-5 次，团队自然信任你的判断
- 勇于承认判断失误。你做错了一次判断，坦白复盘分析"为什么判断错了"，反而增加信任——因为这证明你不是在拍脑袋

**交付信用的建立**：

- 准确估算后兑现。这比写出漂亮代码更重要。技术 Leader 一吹牛排期，团队就失去对你的信任
- 一旦发现排期兜不住，第一时间预警，不要捂到最后一天

**赋能他人的具体做法**：

| 方法 | 具体做法 |
|------|---------|
| 代码评审 | 不只挑问题，讲"为什么"，让每次 CR 变成一次经验传递 |
| 方案评审 | 不直接给答案，问"你有没有考虑过 XX 场景？"，引导对方自己想 |
| 技术分享 | 带头做，但不独占讲台，培养更多人上台 |
| 问题咨询 | 别人来请教，先问"你试过哪些方法"，再补上他没考虑到的维度 |
| 故障处理 | 不要每次都自己上，带一个人一起处理，边处理边讲思路 |

**避免的误区**：

- 不要把"所有难题都我来解"当成影响力。这会让你变成瓶颈，团队其他人长不大
- 不要靠信息垄断建立地位。知识透明化、文档化，团队整体变强了你的影响力反而更大
- 影响力是"做出来"的。每个季度盯一个高影响力项目——方案设计、技术攻关、跨团队协调——交付成功就是最好的影响力证明

**关键时刻的"果断拍板"**：技术影响力不仅体现在日常，更体现在紧急时刻。当线上出故障、多人讨论拿不准方向时，你敢站出来说"先止血，用 A 方案，理由是 XX"，事后验证是对的，这种时刻对你影响力的建立，胜过十次日常分享。

### 7.3 真实可讲的案例

**电商场景**：不是靠 Title 压人。一个具体例子——团队在做库存扣减重构时，我提出用策略模式拆解普通/预售/秒杀三种场景，有人觉得过度设计。我没有强行要求，而是在技术方案评审时把三种场景的差异画在同一张图上，逐条对比复杂度。反对的同事看了图之后说"确实，不拆以后更麻烦"。让他自己想通的。

还有一次，线上 Redis 集群故障，团队讨论要不要切回单机——吵了五分钟没结论。我说"先切回单机止血，10 分钟后恢复服务我们再讨论长期方案。理由是单机虽然性能差但当前流量扛得住，切回去风险最小。"事后验证是对的，以后大家再遇到类似紧急场景，会主动问我"你看怎么办"。这种信任，是靠关键时刻敢拍板、拍了板也靠谱积累出来的。

### 7.4 面试口述话术（1分钟版）

> 我个人理解，技术影响力不是靠职级给的，是靠三个东西积累的：技术判断力、交付信用、赋能他人。一个例子是做库存扣减重构，我提用策略模式有人觉得过度设计，我没有强制，而是把三种场景的差异画在同一张图上逐条对比，反对的同事看了自己说"确实该拆"。让他自己想通。另一个例子是线上 Redis 故障，讨论五分钟没结论，我说先切单机止血，理由是当前流量扛得住风险最小，事后证明对了。以后大家紧急场景会主动来问我。核心是：关键时刻敢拍板、拍了板也靠谱，影响力是这么做出来的，不是挂出来的。

---

### 23.8 附录：追问速查

### 追问1："你说的这些实践，有没有失败的例子？"

**应对思路**：坦诚讲一个失败案例，重点放在"学到了什么、后续机制怎么改了"。面试官最怕的是候选人说自己"从来没失败过"。

**可选案例**：曾经急着推一个重构方案，低估了跨团队对齐的难度，结果方案评审时核心依赖方反对，导致延期两周。教训：以后推跨团队方案时，立项前先私下对齐对方 TL，达成初步共识再上正式评审会。

### 追问2："如果重新做一次XX（你讲的项目），会怎么改进？"

**应对思路**：做减法/做更早的验证/做更透明的沟通——选一个角度，给出具体改进点。

### 追问3："你觉得技术领导力最重要的一个特质是什么？"

**应对思路**：不是说"责任感"这种空话。说"做决策的能力"——在信息不完备的情况下，敢拍板、拍了板能负责到底。技术 Leader 最大的价值不是在信息充分时做决策（大家都会），而是在信息不完备时做决策并承担后果。

### 追问4："你给团队带来最大的改变是什么？"

**应对思路**：别说"我带了很多新技术"。说一个具体的文化/机制层面的改变，比如"建立了 CR 文化"、"建了技术方案存档机制"、"推动了故障复盘闭环"——这些才是能留下、不依赖个人的东西。

---

## 附：关键概念速查

| 概念 | 一句话解释 |
|------|-----------|
| RICE 模型 | (覆盖范围 × 影响程度 × 把握度) / 投入成本，量化需求优先级 |
| 三明治反馈 | 肯定 → 提出问题 → 共同寻找方案，用于代码评审中给改进建议 |
| 梯度任务设计 | 文档→Bug→小功能→跨模块→项目Owner，逐级挑战新人 |
| 分级 CR | 支付级严格审、业务级标准审、工具级轻量审，不同风险不同强度 |
| 绿色通道 | 紧急需求专用通道，有硬准入条件（线上阻断/重大客危），不让所有需求都变紧急 |
| 决策矩阵 | 多维加权打分，把主观争论变成客观对比（可维护性/性能/成本/风险） |
| 原子性 PR | 一个 PR 只做一件事，不超过 400 行，大了就拆 |
| 5 Why | 问五次"为什么"，从表象追问到根因，故障复盘的标准工具 |
| WSJF | 延迟成本 / 工作规模，适合多项目排队时定优先级 |


---
## 二十四、资损防控（P0）

> 资金安全是电商系统的底线。资损防控不是某个技术点，而是贯穿「事前预防→事中拦截→事后对账」的纵深体系。面试高频问。

### 24.1 资金一致性保障

**核心思路**：资金一致性的核心公式是「证」=「实」——业务凭证上的预期金额必须等于实际资金流动。资损就是二者不等。

**三层防控体系（阿里实践）**：

| 阶段 | 手段 | 目标 |
|------|------|------|
| 事前 | 静态代码扫描、资损风险检查、Code Review | 拦截已知风险 |
| 事中 | 实时对账、付款前拦截 | 资金不流出系统 |
| 事后 | T+1离线对账、红蓝军攻防演练 | 兜底发现、度量恢复能力 |

**日切问题**：多系统日期切换时间不一致，同一笔交易在A系统记T日、B系统记T+1日，对账时变成"差异"。解法：对账时按「交易时间」而非「系统记账时间」取数，且留出日切窗口（凌晨1:00-3:00）缓冲。

**结算校验三要素**：金额校验（结算金额 vs 应收金额）+ 状态校验（已送达才能结算）+ 幂等校验（同一笔订单不能重复结算）。

**可讲案例**：订单退款环节最容易出问题——一笔订单可能涉及「商品退款 + 运费退款 + 优惠券退回」三个资金动作。解法：三笔动作打包为一个结算批次，批次维度做证实核对——批次内汇总金额必须等于订单原始实付金额，不等的批次触发告警进入人工审核。

### 24.2 分布式事务在资金场景的应用

**核心思路**：资金扣款用 TCC（强一致），长链路清算用 Saga（最终一致），非关键异步操作用本地消息表。不要在高并发资金链路用 Seata AT 模式。

**TCC（Try-Confirm-Cancel）——支付扣款**：
- Try：冻结资金（余额扣减为不可用余额，不实际出账）
- Confirm：实际扣款（冻结→已扣除）
- Cancel：解冻资金（冻结→可用余额）

**三个经典陷阱**：
| 陷阱 | 场景 | 解法 |
|------|------|------|
| 空回滚 | Cancel 先到，Try 还没执行 | Cancel 查不到 Try 记录时，插入防悬挂标记 |
| 悬挂 | Cancel 执行完，Try 后到又把资源冻结了 | Try 前先查是否有 Cancel 记录 |
| 幂等缺失 | Confirm/Cancel 被重试 | tcc_transaction_log 表以 xid 为主键去重 |

**Saga——长流程清算**：将长事务拆成有序的本地事务序列，每步配补偿操作。例如：订单创建 → 支付扣款 → 积分发放 → 履约完成。补偿链：履约回退 ← 积分扣回 ← 退款 ← 订单取消。

**本地消息表——异步非关键操作**：业务操作和消息写入同事务中，定时任务扫未发送消息投递MQ，消费端幂等处理。可靠性最高。

**可讲案例**：电商营销发券场景——下单成功后，在同一事务里写入订单 + 发券消息记录。后台定时任务每30秒扫一次未发送消息投递RocketMQ，消费端以订单号为幂等键。MQ失败进入死信队列人工补发。

### 24.3 金额计算的精度问题

**核心思路**：永远用 `new BigDecimal(String)` 构造，不要用 `double`；分转元必须指定精度+舍入模式；equals 改用 compareTo。

| 规则 | 错误做法 | 正确做法 |
|------|----------|----------|
| 构造 | `new BigDecimal(0.1)` 精度丢失 | `new BigDecimal("0.1")` |
| 分转元 | `fen.divide(100)` 可能异常 | `fen.divide(new BigDecimal(100), 2, RoundingMode.HALF_UP)` |
| 比较 | `a.equals(b)` → 1.00 ≠ 1.0 | `a.compareTo(b) == 0` |

**舍入模式选择**：用户可见金额用 HALF_UP（四舍五入）；银行结算/利息用 HALF_EVEN（银行家舍入，大量交易下消除系统性偏差）；优惠门槛计算用 UP（平台利益保障）。

**存储与传输**：数据库用 `DECIMAL(19,4)`；JSON 传输用字符串 `"123.45"` 避免 JS Number 精度问题；高并发计算全链路用「分」（long），只在最终展示时转元。

**可讲案例**：营销活动发券对账发现差0.01元。排查发现历史代码用 `double` 计算优惠分摊，浮点累计误差导致最后一笔分摊金额偏差。修复：全部改为 BigDecimal 链式计算，分摊逻辑统一用「前N-1项按比例舍入、最后一项减法补齐」策略，确保总分一致。

### 24.4 幂等性设计

**核心思路**：分层防御——前端防重 → 网关去重 → 服务层Token/锁 → 数据层唯一索引 → 状态机兜底。重复请求返回第一次的结果，不是返回错误。

| 方案 | 原理 | 适用场景 |
|------|------|----------|
| 唯一键 + DB唯一约束 | 业务单号为幂等键，重复插入触发 DuplicateKeyException | 支付、退款、下单 |
| 幂等 Token | 先获取一次性Token，提交时校验并删除 | 前端防重复点击 |
| 状态机 | 更新时 WHERE 旧状态，影响行数为0则拒绝 | 订单/支付单状态流转 |
| 分布式锁 | 串行化「校验+执行」 | 配合上述方案，不单独使用 |

**关键坑点**：(1) Token 的 get+delete 必须用 Redis Lua 脚本保证原子性；(2) 订单从「支付中」回退到「待支付」时，旧的支付回调用过期状态判断会绕过校验——解法是引入版本号（version）；(3) 分布式锁释放时必须校验 value 是否为当前线程持有。

**可讲案例**：大促期间用户连续点击两次「确认支付」，前端按钮防重被网络抖动绕过，后端没有幂等导致重复扣款。修复方案：(1) 订单号+版本号唯一索引；(2) 状态机 WHERE status='待支付'；(3) 前端 Token 机制作第一道防线。修复后 JMeter 1000 线程并发压测，0笔重复扣款。

### 24.5 审计与追溯

**核心思路**：任何资金数据变更，必须能回答「谁、什么时间、从什么改成什么、为什么」四个问题。审计记录和业务数据必须在同一事务中写入。

**操作日志**：记录操作人、操作时间、操作类型、操作对象、IP地址。独立审计表，与业务事务原子写入。日志记录一旦生成不允许更新或删除，只能追加。

**数据变更记录**：before/after JSON 快照。可走应用层 AOP 拦截（灵活）或 binlog 监听 Canal（不侵入业务代码）。

**资金流水**：记录每笔钱的来龙去脉，是资损排查最终依据。核心字段：流水号、交易类型、交易金额、交易前余额、交易后余额、关联订单号。设计要点：(1) 流水不可修改，错误通过冲正修正；(2) 同一资金链路的所有流水有同一个 traceId 串联；(3) 通过余额连续性校验流水完整性——前一笔 afterBalance 必须等于后一笔 beforeBalance。

**可讲案例**：退款客诉排查从2小时降到10分钟。改造：(1) 退款全链路引入 traceId，申请→审批→打款→回调每步记录流水；(2) 数据变更记录保存 before/after 快照 JSON；(3) 凌晨自动校验退款流水余额连续性，中断则告警。

### 24.6 实时对账与离线对账

**核心思路**：离线对账是主力、实时对账是防线、平账中心是闭环。对账不是目的，发现问题并能自动修复才是目的。

| 维度 | 离线对账（T+1） | 实时/准实时对账 |
|------|----------------|-----------------|
| 时效 | 次日完成 | 秒级~分钟级 |
| 覆盖 | 全量数据 | 核心资金链路 |
| 技术 | SQL批量比对 + 定时任务 | Binlog监听 + Kafka + 流计算 |
| 目的 | 兜底全量校验 | 及时拦截，防止资金流出 |

**三种差异类型**：漏结/长款（渠道有账、系统无账）→ 自动补单；重复结 → 自动冲正+告警；错结（金额/状态不一致）→ 人工复核后处理。

**实时对账关键设计**：任一数据到达即可触发比对（不等双方数据都到齐），超时未匹配进入存疑队列；存疑期等一个可配置窗口（如5分钟），排除网络延迟/日切导致的假差异；付款前拦截——账单与结算单不一致时阻断付款。

**可讲案例**：电商平台和支付宝每日对账。凌晨2点拉取支付宝对账单文件（CSV，可能几百MB），用流式读取避免OOM。两边统一成「渠道单号+实付金额+交易时间」三元组，按渠道单号哈希分片 + 排序 + 双指针流式比对。每天处理约150万笔交易，日常差异在10笔以内，基本是日切窗口造成的假差异，T+2自动消失。

#### 面试回答策略

1. **开场定调（1分钟）**：「资损防控是纵深体系，分事前、事中、事后三层」
2. **深入一个话题（8-10分钟）**：推荐「幂等性设计 + 分布式事务选型」组合，跟Java后端经验最贴近
3. **补充其他维度（3-5分钟）**：简要提及对账机制、金额精度、审计追溯，展示体系化思维
4. **收尾（1分钟）**：「资损防控的本质是不信任任何单一系统，用独立的对账链路验证资金正确性」
---
## 二十五、领域建模与DDD（P1）

> 面试高频话题。DDD不是银弹，面试官要听的是你「知道什么时候该用、什么时候不该用、怎么落地」。

### 25.1 DDD战略设计核心概念

**限界上下文（Bounded Context）**：一个业务概念在不同子系统里含义不同。比如"用户"——对客服系统是买家信息+历史工单，对风控系统是设备指纹+行为轨迹。限界上下文就是把有明确语义边界的业务范围圈出来，范围内每个概念含义唯一。

**统一语言（Ubiquitous Language）**：让业务和开发使用同一套术语，代码中的类名、方法名、字段名直接使用这套语言。如果代码里还是 `status=1/2/3` 这种魔术数字，说明统一语言没落到实处。

**上下文映射（Context Map）**：多个限界上下文之间怎么协作。重点记三种关系：
- **防腐层（ACL）**：对接外部/遗留系统时加一层翻译，外部模型变化只改 ACL 不动业务代码
- **开放主机服务（OHS）**：对外提供标准化 API，下游都用同一套 DTO
- **上下游/顺从（Conformist）**：下游完全接受上游模型，不做翻译

**可讲案例**：对接第三方 ERP 时，ERP 返回的 `material_code` 要翻译成内部的 `sku_code`，`sales_org` 翻译成 `shop_id`。在订单域外建一个 ACL 专门做翻译。后来 ERP 版本升级改字段名，只改 ACL，业务代码一行没动。

### 25.2 DDD战术设计核心模式

**四类核心对象（面试讲这四个即可）**：

**Entity（实体）**：有唯一标识、有生命周期的对象。标识不变，属性可变。"订单"就是实体——订单号从创建到完成不变，但状态、物流单号一直变。判断两个订单是否同一，看订单号不看金额。实体应有行为方法：`order.confirmPayment()` 而非 `order.setStatus(PAID)`。

**Value Object（值对象）**：无唯一标识、通过属性值判等、不可变（immutable）。"收货地址"是值对象——省市区+详细地址一样就是同一个。`BigDecimal`、`LocalDateTime` 也是值对象。用 `Money`（金额+币种）代替 `BigDecimal`，可防止把人民币和美元直接相加的低级错误。

**Aggregate（聚合）**：一组相关对象的集合，聚合根为唯一入口。外部不能绕过聚合根直接修改内部对象。聚合是事务一致性边界——一个事务只修改一个聚合。聚合通过 ID 引用其他聚合（订单持有 productId，不持有 Product 对象）。

**Repository（仓储）**：聚合的持久化入口，屏蔽底层存储细节。接口在领域层，实现在基础设施层（依赖倒置）。一个 Repository 只负责一个聚合根。

**其他三个概念**（简要了解）：Domain Service（跨聚合的业务逻辑）、Domain Event（聚合内发生重要事件，事务提交后发布通知其他上下文）、Factory（封装复杂聚合创建逻辑）。

### 25.3 贫血模型 vs 充血模型

**这个几乎必问。** 先给定义，再讲为什么大部分代码是贫血的，最后讲什么时候该用充血。

| 维度 | 贫血模型 | 充血模型 |
|------|---------|---------|
| 特征 | 对象只有 getter/setter，逻辑在 Service | 对象包含数据+行为，外部通过方法改变状态 |
| 代码 | `order.setStatus(PAID); orderService.save(order);` | `order.confirmPayment(paymentId); orderRepository.save(order);` |
| 优点 | 简单、框架友好、学习成本低 | 业务规则内聚、单一修改点、可测试性好 |
| 缺点 | 业务规则散落各 Service，改一个规则可能漏改 | 学习门槛高、ORM 要求高、简单 CRUD 过度设计 |

**为什么大部分代码是贫血的**：(1) 历史原因——Spring MVC + MyBatis 默认倾向 Service+DTO 模式；(2) 简单业务不需要充血——管理后台、数据报表本质就是 CRUD；(3) 充血模型的落地需要领域建模能力 + ORM 深入使用，团队习惯和框架约束。

**什么时候该用充血**：(1) 业务规则复杂、多变、易扩散（如营销活动资格校验、优惠券互斥规则）；(2) 有明确状态机的业务（订单状态流转）；(3) 核心域（交易域、账务域），非核心域用贫血即可。

**务实混合策略（面试加分点）**：核心域核心聚合用充血（订单、支付、库存扣减）；通用域和支撑域用贫血（字典管理、消息推送）；读模型（查询接口）直接用贫血 DTO 不经过领域层。这就是 CQRS 思路——写侧充血，读侧贫血。

**可讲案例**：营销活动系统从"满100减10"逐步演化到"满100减10且与店铺券互斥、每周限用2次、仅限新用户"。贫血模型写了三个 Service 各自校验，经常遗漏。重构为充血模型：`Activity` 聚合根封装 `canApplyTo(order)` 方法，内部逐个调用 `Rule` 值对象的 `validate()` 方法。新增规则只需新增 Rule 实现类并注册，不再动编排代码。

### 25.4 电商场景的领域建模实例

**限界上下文划分**：

| 上下文 | 核心职责 | 核心聚合 |
|--------|---------|---------|
| 商品上下文 | 商品信息、类目、属性、SKU | 商品聚合（SPU+SKU）、类目聚合 |
| 订单上下文 | 下单、状态流转、逆向退款 | 订单聚合、退款单聚合 |
| 支付上下文 | 支付单管理、渠道适配、对账 | 支付单聚合 |
| 营销上下文 | 活动管理、优惠券、满减规则 | 活动聚合、优惠券聚合 |
| 用户上下文 | 用户信息、等级、积分 | 用户聚合、地址（值对象） |
| 库存上下文 | 库存预占、实际扣减、同步 | 库存聚合 |
| 物流上下文 | 发货、物流轨迹 | 运单聚合 |

**划分依据**：(1) 按业务能力——能独立完成一个完整业务功能的能力就是一个上下文；(2) 按变化频率——营销规则天天变，商品基础信息相对稳定，稳定性不同的放一起会拖累；(3) 按团队组织（康威定律）——商品组和交易组两个团队，就是对两个上下文。

**上下文协作关系**：订单 ⇿ 商品（开放主机服务——下单时查询商品信息并保存快照）；订单 ⇿ 营销（上下游——订单创建时查可用券）；订单 ⇿ 支付（防腐层——支付渠道返回格式各不相同，ACL统一翻译）。

### 25.5 聚合设计原则和常见陷阱

**四条核心原则**：
1. **在聚合边界内保证业务规则不变性**：如「订单总金额 = sum(订单项金额) - 优惠金额」在聚合内任何时候都成立
2. **聚合要尽量小**：太大→并发冲突多。建议一个聚合不超过5个对象。帖子和回复不应放同一聚合
3. **通过 ID 引用其他聚合**：订单存 productId，不存 Product 对象
4. **聚合内强一致，聚合间最终一致**：一个事务只修改一个聚合实例

**常见陷阱**：
- **大聚合**：把订单+订单项+支付+物流+发票全放一个聚合，改物流状态要锁整个订单
- **双向引用**：用户聚合放订单ID列表，订单又放用户对象引用，随便改一个都担心影响另一个。正确做法只保留单向引用
- **用数据库自增ID作聚合标识**：聚合ID应该是业务标识（如订单号），不依赖持久化

**可讲案例**：订单聚合设计过大（含订单+订单项+收货地址+优惠明细+支付单+发票），线上并发冲突严重——用户改发票抬头的同时客服改收货地址，乐观锁冲突导致后提交的那个失败重试。拆成三个独立聚合（订单、支付、发票）后并发冲突消失。

### 25.6 DDD落地到代码结构

**COLA四层架构（面试推荐讲这个）**：

```
适配层（Adapter）：Controller / MQ Listener —— 参数校验、格式转换
应用层（Application）：AppService / EventHandler —— 用例编排、事务管理
领域层（Domain）：Entity / ValueObject / Aggregate / Repository接口 —— 业务规则
基础设施层（Infrastructure）：RepositoryImpl / Mapper / Gateway —— DB/缓存/消息实现
```

**依赖方向**：只有外层依赖内层。领域层是核心，不依赖任何层。基础设施层实现领域层定义的接口（依赖倒置）。

**关键实践点**：(1) 仓储接口在领域层，实现在基础设施层；(2) 聚合根不应该是 Spring Bean，通过 Repository 或 Factory 创建；(3) 领域事件在聚合根内记录，在应用层发布——保证事件在数据持久化成功后才发出；(4) 读操作可以绕过领域层（CQRS落地——写走完整链路，读直接 Adapter→Infra）；(5) 不要一上来就全套 DDD——用分级策略（总是做统一语言 → 复杂度中等时做战术设计 → 高复杂度时做全套）。

### 25.7 DDD的代价和什么时候不该用

| 场景 | 为什么不该用 | 该用什么 |
|------|------------|---------|
| 内部管理后台/CRUD系统 | 业务逻辑就是增删改查表单 | 传统三层架构 |
| 数据报表/BI展示 | 核心是SQL查询和数据可视化 | 直接SQL+前端图表 |
| 项目MVP阶段 | 业务没跑通，模型频繁变 | 快速CRUD，跑通再重构 |
| 简单网关/代理服务 | 只做协议转换和路由 | 轻量级框架 |
| 团队<5人、业务简单 | DDD战略设计在单人团队是额外负担 | 简化分层即可 |

**给面试官的务实总结**：「DDD不是架构的全部。核心域的核心聚合用充血建模保证业务规则内聚，非核心域用传统三层降低开发成本。一刀切式的'全用DDD'和'全不用DDD'都是错的。关键是识别哪些业务复杂度值得投入建模成本。」
---
## 二十六、AI Agent 核心认知（P1）

> 转型 Agent 开发的核心差异化标签。面试官不期待你是算法专家，但期待你能讲清 Agent 的核心概念、落地场景，以及 Java 经验为什么能迁移过来。

### 26.1 Agent 核心架构

**一句话定义**：Agent 不是单次问答的 LLM，而是以 LLM 为推理引擎、具备记忆、规划和工具调用能力、能在多步循环中自主完成任务的智能系统。

**核心公式**：`Agent = LLM（大脑）+ Planning（规划）+ Memory（记忆）+ Tools（工具）+ Feedback Loop（反馈环）`

**执行循环（ReAct 模式）**：`Thought → Action → Observation → Thought → ... → Final Answer`

例如查天气：Thought（用户想知道北京天气，需要调天气工具）→ Action（调用 get_weather("北京")）→ Observation（晴，25°C）→ Thought（已获取信息，可以回答）→ Answer（今天北京晴，25°C）

**Java 类比**：

| Agent 概念 | Java 对应 |
|-----------|----------|
| Tool 注册与绑定 | SPI 机制 / Spring Bean 注入 |
| Planning 工作流编排 | Flowable/Camunda 工作流引擎 |
| Memory 多轮状态管理 | Session + Redis 缓存 |
| Feedback 纠错 | 重试拦截器 + 断路器（Resilience4j） |
| 多 Agent 通信 | 消息队列（Kafka）异步解耦 |
| 检查点/断点续传 | Saga 分布式事务补偿 |

### 26.2 Function Calling / Tool Use 原理

**核心区分**：Function Calling 是 LLM 输出结构化调用的能力，Tool Use 是在此之上形成的完整执行闭环，Agent 则是具备自主决策和多步循环的完整系统。三者关系：`Function Calling（机制层）→ Tool Use（系统层）→ Agent（决策层）`

**5步工作链路**：
1. 注册工具（JSON Schema 描述工具名、参数类型、功能说明）
2. 用户输入自然语言，LLM 判断是否需要调工具
3. LLM 输出结构化 JSON（工具名+参数），**不执行**
4. 应用程序（你的后端代码）真正执行函数
5. 执行结果喂回 LLM，LLM 基于结果生成最终回复

**关键细节**：LLM 不执行任何代码，只输出 `{"name": "search_order", "arguments": {"orderId": "123"}}` 这种 JSON，执行是 Agent 框架的职责（经典陷阱题）。多轮调用是常态——一个"查订单并退款"实际链路是：意图识别→查订单→获取结果→判断退款条件→调退款工具→告知用户，中间可能有 3-5 轮 LLM 调用。

**Java 类比**：Tool Schema ≈ RPC 接口定义（IDL/Proto）；LLM 判断调哪个工具 ≈ 服务路由（Gateway 选后端服务）；Tool 执行 ≈ 实际 RPC 调用；结果回填 ≈ 调用方拿到 response 做下一步处理。区别在于：传统 RPC 是程序员硬编码调用链路，Tool Use 是 LLM 用自然语言推理决定调用链路。

### 26.3 MCP 协议（Model Context Protocol）

**一句话定义**：MCP 是 Anthropic 2024 年底推出的开放协议，解决「LLM 如何标准化地连接外部工具和数据源」的问题。通俗类比：**MCP 是 AI 世界的 USB-C 接口**。

**为什么需要 MCP**：传统 Function Calling 每个 LLM 厂商、每个工具都用各自的接入方式。接 10 个外部服务就是 M×N 的集成复杂度。MCP 用一套标准协议让 LLM（客户端）和工具（服务端）解耦，变成 M+N 的线性复杂度。

**核心架构（Client-Server，JSON-RPC 2.0）**：

MCP 定义三种能力：(1) **Tools**：可执行的动作，LLM 决定何时调用（类比 REST POST）；(2) **Resources**：可寻址的上下文数据，如文件、DB记录（类比 REST GET）；(3) **Prompts**：可复用的参数化提示模板（类比预定义 SQL 模板）。

三种传输方式：STDIO（本地进程通信）、SSE（Server-Sent Events，Web应用）、Streamable HTTP（2025新规范，推荐）。

**MCP vs Function Calling**：Function Calling 是机制（LLM 输出结构化调用的能力），MCP 是协议（标准化工具接入的规范）。类比：JDBC 驱动和 JDBC 标准的关系。

**Spring AI 落地**：`@McpTool` 注解即可暴露 Java Service 为 MCP Tool，支持 STDIO、SSE、Streamable HTTP 三种传输方式。一个注解把业务能力暴露给 AI。

**Java 类比**：MCP 本质上就是 SPI 机制——定义标准接口→各厂商实现→运行时自动发现和加载。只是从 JVM 内部扩展到了 LLM 与外部工具的通信层。

### 26.4 框架选型：LangChain vs LangGraph vs CrewAI

| 维度 | LangChain | LangGraph | CrewAI |
|------|-----------|-----------|--------|
| 编排模型 | 链式（Chain） | 图/状态机（Graph） | 角色协作（Crew） |
| 核心抽象 | Chain + Tool + Memory | Node + Edge + State | Agent + Task + Crew |
| 流程控制 | 线性为主 | 循环、条件分支、人机协同 | 自动委派与合并 |
| 适合场景 | 快速原型、RAG、单步任务 | 多步工作流、审批节点 | 角色分工场景 |
| Java类比 | Servlet Filter Chain | Flowable/Camunda BPMN | 微服务编排（每个Agent=微服务） |

**选型建议**：入门用 LangChain（掌基础知识）→ 进阶用 LangGraph（复杂工作流编排）→ 多Agent协作用 CrewAI（真正需要多角色分工时才用）。简单任务不需要 Graph 的复杂度，线性流程不需要多 Agent 的角色分工。

### 26.5 RAG（检索增强生成）原理

**一句话定义**：RAG 是在 LLM 生成回答前，先从外部知识库检索相关信息注入 Prompt 中，再让 LLM 基于检索结果生成回答。**先搜后答，有据可查。**

**技术链路**：离线阶段（文档→切块→Embedding→向量库存储）→ 在线阶段（用户问题→Embedding→向量检索→上下文注入→LLM生成）

**混合检索（生产必备）**：向量检索（语义相似度，理解同义词）+ 关键词检索（BM25，精确匹配），加权融合（常见权重 7:3），取综合 Top-K。

**RAG vs ES 倒排索引**：ES 返回文档列表，RAG 读了文档之后用自己的话整合回答——这是质的区别。

**电商场景**：客服知识库通过 RAG 实时检索注入 Prompt，回复正确率超 90%，知识更新从周级缩短至分钟级（改文档即生效，不需要重新训练模型）。

### 26.6 Agent 在电商中的落地场景

| 场景 | Agent 角色 | 核心价值 |
|------|-----------|----------|
| 智能客服 | 售前咨询+售后退款+FAQ，调用真实业务接口 | 人工坐席成本降40-60% |
| 自然语言问数 | 自然语言→SQL→查库→生成图表+解读 | 运营自己问数，不用找DBA |
| 营销文案 | 根据商品属性+活动规则批量生成 | 从0→60分，人做60→90打磨 |
| 代码生成 | 需求→写代码→跑测试→提交PR | 提效，但仍需人工Review |

### 26.7 为什么 Java 工程师转型 Agent 有优势（面试核心卖点）

**核心论点**：Agent 落地的最大瓶颈不是模型能力，而是系统工程能力。这正是 Java 后端工程师的核心竞争力。

**五个优势维度**：
1. **系统设计能力**：Agent 要处理多轮对话状态、工具调用编排、多 Agent 通信、容错降级——这些是分布式系统设计的经典问题。Java 工程师常年在做服务拆分、接口设计、状态管理、容灾方案。
2. **API 编排经验**：Agent 的 Function Calling 本质就是「自然语言输入→动态路由到不同后端服务」。网关选服务→传参→接收返回→组合结果，这个心智模型 Java 工程师门儿清。
3. **状态管理**：Agent 的 Memory 体系在 Java 里就是 Session（会话状态）+ Redis（缓存）+ Saga（分布式事务状态机），对"在分布式环境中管理跨请求状态"有肌肉记忆。
4. **框架思维**：Tool 注册 = Bean 注入；工作流编排 = Flowable/Camunda；中间件 = AOP + Filter Chain。Spring AI 本身就在用 Spring 的 DI/AOP/自动配置范式做 Agent 开发。
5. **务实工程观**：Agent Demo（100行 Python 脚本跑通）和 Agent 生产系统（可靠、可观测、可运维）之间是鸿沟。Java 工程师长期在企业级环境中带着「异常处理、日志监控、灰度发布、压测容量」的工程习惯，这在 AI 团队里是稀缺品。

**面试定调话术**：「我转型 Agent 不是从零开始。12年后端经验沉淀的系统设计能力在 Agent 场景里直接可迁移。我的差异化价值是：既能理解 AI 的能力边界，又能把 AI 能力工程化地嵌入业务系统。团队需要的是打通「业务系统」和「智能算法」之间的桥梁，这就是我的定位。」

**避坑提醒**：不要说自己「放弃了 Java」，而是说「在 Java 工程基础上增加了 AI 能力层」。后端能力在 Agent 项目里仍然是必需的——接口、数据库、缓存、消息队列、部署运维。Agent 不等于替代后端，Agent 需要后端。
---
## 二十七、技术选型与架构决策（P0补充）

> 与第一节「技术选型 Trade-off」互补——第一节讲具体案例，本节补方法论和决策框架。高级工程师及以上常考。

### 27.1 技术选型核心原则

**选型不是"哪个技术最强"，而是"在当前约束下，哪个方案总成本最低"。**

**四维评估框架**：`选型决策 = 业务匹配度 × 团队能力 × 长期成本 × 生态风险`

- **业务匹配度**：这技术解决的是我当前阶段的问题，还是5年后才有的问题？日活不到1万的团队拆12个微服务，开发周期翻倍，响应变慢
- **团队能力**：不是"团队里有没有人会"，而是"出问题有没有人能30分钟内定位"。选型时问三问：团队有人深入用过吗？线上故障能快速定位吗？招聘市场好招人吗？
- **长期成本（TCO）**：不只算引入成本，算5年总持有成本 = 学习成本 + 开发效率 + 运维复杂度 + 招聘成本 + 迁移成本
- **生态风险**：开源项目看 GitHub star 趋势 + issue 响应速度 + 核心贡献者是否分散（防单点依赖）。阿里系中间件的共同特征：内部双11验证→开源→Apache顶级项目，生态风险可控

### 27.2 引入新技术的「三问决策法」

```
一问：旧技术是否已经对业务造成了实质伤害？
二问：新技术的收益能否覆盖迁移成本？
三问：团队是否具备踩坑填坑的能力储备？
```

**决策图谱**：旧技术有实质痛点？→ 否：不改 → 是：新技术ROI>迁移成本？→ 否：优化旧方案 → 是：团队有能力承接？→ 否：先招人/培训 → 是：做POC→渐进迁移

**迁移成本估算** = 编码改造 + 数据迁移 + 测试回归 + 灰度验证 + 团队学习 + 线上风险 + 回滚预案。口诀："迁移不是把代码从A语言翻译成B语言，是把一个团队的知识体系从A生态移植到B生态。"

### 27.3 技术预研和POC

**POC的本质：用最小的代价验证最大的风险假设。**

**六步法**：(1) 定义验证目标（明确要验证什么，不是"调研一下XX"）；(2) 设定量化通过标准（P99延迟<200ms、7天压测零数据丢失、故障恢复<30s）；(3) 设计对照实验（控制变量：同数据量、同查询模式、同硬件）；(4) 实施+记录（惊喜数据要重测——极端好的结果往往是测试方法有问题）；(5) 输出明确结论（通过/不通过/有条件通过，不要写"建议进一步调研"）；(6) POC代码不要当生产代码用。

### 27.4 架构演进节奏

**口诀**：先跑通再拆，拆非核心先试水，步子小回退快。

```
单体 → 模块化单体 → 微服务 → 服务网格
         ↑            ↑         ↑
      先做到这里     别急着跳   不到万不得已别碰
```

**拆分顺序**：非核心无依赖（日志/通知）→ 低依赖独立业务（商品浏览）→ 核心高依赖（订单/支付）。原因：从最不重要的服务开始试水，出了故障影响最小。

**拆分的正确姿势——绞杀者模式**：新建微服务→双写同步→流量灰度切流（10%→30%→50%→100%）→稳定后删旧代码。每步可独立回滚。

**什么时候不该拆微服务**：三个条件缺一个就不该拆——(1) 业务模型还没稳定（频繁改表结构）；(2) 团队不到10人（拆了沟通成本反而大于收益）；(3) 没有自动化部署能力（手工运维10个服务比1个单体灾难100倍）。

### 27.5 向非技术方解释技术决策

**翻译三步法**：`技术语言 → 业务影响 → 量化收益`

**四原则**：(1) 从业务痛点切入，不是从技术特性切入——"查订单要5秒被商家投诉" vs "TiDB支持水平扩展"；(2) 用"可逆决策"降低决策压力——展示回滚方案；(3) 把技术成本翻译成人民币——分库分表每年0.8个DBA人力≈30万/年，TiDB自动化降到0.2个≈7.5万/年，5年省120万；(4) 给老板一个"不选会怎样"的对比。

**不同角色的侧重点**：老板/VP（ROI、风险、时间线）→ 产品经理（业务影响、功能交付）→ 业务方（稳定性、连续性）→ 技术团队（实现细节、迁移路径）→ 运维/QA（可观测性、回滚方案）

### 27.6 选型速查（详见各章节）

具体技术选型对比已在各章节展开：MQ选型参见「八、消息队列深度 8.4」、注册中心选型参见「四、微服务体系核心」、数据库选型参见「五、中台架构 5.X」、RPC选型参见「四、微服务体系核心 Dubbo部分」。本节补的是决策框架而非具体对比表。

### 27.7 常见选型追问速答

| 追问 | 要点 |
|------|------|
| 选型时犯过什么错误？ | 早期因技术热度选型（看到Kafka火就想用），后来发现RocketMQ的事务消息才是业务刚需。教训：为场景选技术，不是为技术找场景 |
| 开源项目怎么评估风险？ | star趋势+issue响应速度+核心贡献者分散度。阿里系加分项是走完"内部验证→开源→Apache"路径 |
| 怎么判断新技术是趋势还是炒作？ | 看它解决了什么以前解决不了的问题。Kubernetes解决了容器编排→趋势。微前端对大部分公司是过度设计→炒作 |
| 老板坚持用你不看好的技术怎么办？ | 用POC数据说话，设计公平对照实验。如果老板仍然坚持——把风险点文档化、明确告警阈值、准备回滚预案。决策保留意见，执行对结果负责 |
---
## 二十八、高并发系统设计：限流策略与串联框架（P1补充）

> 本节与 Redis（缓存三问题/热Key）、MQ（削峰/堆积）、MySQL（分库分表）、分布式理论（CAP）互补。那些章节讲具体技术，本节补两个被遗漏的点：限流策略和端到端串联回答框架。

### 28.1 限流策略

**核心思路**：限流是"宁可拒绝部分请求，也不能让所有人一起完蛋"。分层实施：应用层（接口级）+ 网关层（入口级）+ 资源层（连接池/线程池）。

**三种算法对比**（面试重点）：

| 算法 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| 令牌桶 | 固定速率放令牌，请求需获取令牌 | 允许短时突发 | 高峰后可能抖动 | API网关，首选 |
| 漏桶 | 请求入桶，固定速率处理 | 流量绝对平滑 | 无法应对突发 | 调用第三方接口 |
| 滑动窗口 | 统计最近N秒请求数 | 精度高，无临界问题 | 内存开销大 | 风控、精准计数 |

**固定窗口为什么不行**？窗口边界的"临界突刺"问题——00:00:59和00:01:00两个窗口交界处，1秒内可能通过2倍限流阈值的请求。

**工程实践**：
- 单机限流：Guava RateLimiter（平滑突发）或 Sentinel（阿里开源，控制台管理）
- 分布式限流：Redis + Lua 脚本原子执行，单节点约4.3万QPS
- 分级限流：用户级（50次/s）< IP级（200次/s）< 接口级（1万次/s）< 服务级（5万次/s），层层收口
- 配合熔断降级：限流触发后返回降级响应（缓存数据、默认值、排队提示），不能让用户看到500错误

### 28.2 高并发系统的端到端串联框架

当面试官问「你的系统怎么扛高并发的？」，用这个**纵深防御六层框架**回答，每层一句话点到为止，根据追问再展开：

> "我们的高并发方案是一个纵深防御体系，从外到内六层：
> 1. **接入层**：CDN + 网关限流（令牌桶），拦掉恶意流量和超量请求
> 2. **缓存层**：多级缓存（Caffeine + Redis），90%+ 读请求在这层消化（详见Redis章）
> 3. **队列层**：MQ 削峰填谷，写请求异步化，保护核心服务（详见MQ章）
> 4. **应用层**：弹性伸缩 + 连接池保护 + 热点数据本地缓存
> 5. **数据层**：读写分离 + 分库分表 + 热点Key打散（详见MySQL章）
> 6. **兜底层**：熔断降级 + 限流升级 + T+1对账补偿
>
> 以我负责的XX场景为例，核心瓶颈在于XXX，我们在XX层做了XXX优化，最终效果是XXX。"

每层点到为止，根据面试官追问的方向再展开细节。不要一次性全倒出来。

### 28.3 热点数据处理速查

详见「七、Redis 深度 7.7 大Key、热Key」章节。这里补一个面试必备的核心判断：

**热点发现**：可预知热点（秒杀商品→提前30分钟预热）；不可预知热点（突发爆款→本地LRU统计+中心化标记）。拼多多通过ZK实时分析节点负载，50ms内识别访问量突增300%的key。

**热点应对优先级**：本地缓存（最有效，Caffeine微秒级）> Key打散（读远大于写时适用）> 多级限流（热点请求单独限流，更严格阈值）。

**注意事项**：热点不要用分布式锁（高并发下锁竞争让Redis成为新瓶颈，用本地缓存+乐观锁更好）；Key打散只适用于读热写温场景。

---
## 二十九、HR面/政委面高频话题（P0）

> 这些话题100%会被问到。核心原则：不说套话、不黑前司、不画大饼。每个回答要能让HR感觉到「这人有自知之明、思路清晰、不会是个管理炸弹」。

### 29.1 为什么离职/看机会

**核心思路**：不是「离开前司」，而是「阶段任务完成 + 能力模型需要下一个场景」。不评价前司好坏，不讲人际关系。

**口述要点**：
- 我在得物经历了从业务高速增长到系统稳定化的完整周期。早期跟着业务跑，做了很多0到1的东西；后期更多是在现有架构上做优化和治理。
- 现在系统已经比较成熟了，我自己的成长曲线也开始变平。接下来3-5年我想在「复杂业务建模 + 技术纵深」上再上一个台阶，但目前团队的技术挑战更多集中在业务支撑层面，缺少进一步打磨架构能力的机会。
- 所以我主动选择出来看机会，不是为了走而走。我对前司非常感激，那是我成长最快的一段经历。离开是能力发展阶段的选择，不是对团队或业务不满意。

### 29.2 职业规划（3-5年）

**核心思路**：不画大饼说「做架构师/CTO」，用阶段论表达清晰路径——每个阶段解决什么问题、产出什么价值。

**口述要点**：
- **第一阶段（1-2年）**：在新公司扎下去，先成为某个核心业务域（交易、履约、商品等）的技术Owner。不只是写代码，是能对这个域的架构设计、稳定性指标、技术债务治理完整负责，并且在业务方那里有口碑——「这块找XX就行」。
- **第二阶段（3-5年）**：从单域扩展到跨域架构。电商系统最难的不是单个服务，而是跨域协作——交易和履约之间的一致性、库存和营销的实时联动。希望成为能解决跨域复杂问题的架构角色，同时开始带人、培养梯队。
- 我从没想过转纯管理，技术手感是我最核心的竞争力，不会丢。

### 29.3 最大的失败/挫折及复盘

**核心思路**：选真实技术故障案例（不是人为失误），重点在复盘闭环——不只修Bug，是建立机制让同类问题不再发生。

**推荐案例方向——缓存变更引发的线上故障**：
- 有一次大促前，上线了一个「看似无害」的缓存预热逻辑变更。逻辑本身测过没问题，但没考虑到预热脚本在生产环境的批量加载量级，导致Redis连接池被打满，上游交易大面积超时。影响了十几分钟，幸好有熔断兜底。
- **当时处理**：回滚、扩容、恢复，常规操作。
- **复盘才是重点**。我问了自己三个问题：(1) 为什么测试和生产表现不一致？——缺少生产级压测环境；(2) 为什么影响范围这么大？——缓存和核心交易的连接池共享，没做隔离；(3) 为什么上线没感知风险？——变更审批只看代码Review，没人关心非代码类变更的风险。
- **改进动作**：(1) 推动成立发布Checklist机制，非代码变更必须有独立风险评估；(2) 缓存连接池物理隔离，核心链路用独立集群；(3) 补充生产级压测回归项。
- 这件事让我意识到：**大部分故障不是架构问题，是流程问题和认知盲区**。从那以后每次大促我都主动做变更风险推演，这个习惯一直保持到现在。

### 29.4 和领导意见不一致时如何处理

**核心思路**：不是「谁说服谁」，而是「把决策依据显性化 + 让数据说话」。体现有观点但不固执，有判断但不越界。

**三步处理逻辑**：
- **第一步，确保理解了Leader的完整上下文。** Leader看到的往往比我广，可能有我不知道的约束条件（排期压力、组织层面考量）。先问自己：他的决策在什么约束下是最优的？
- **第二步，如果纯技术路径上确实不认同，写对比分析文档。** 不是口头争论——方案A vs 方案B，各自的收益、风险、成本、可逆性。有条件就做最小POC验证核心假设，让事实说话。
- **第三步，Leader做最终决策后，全力执行。** 不管之前分歧多大，一旦定了，我的角色就是让方案落地，同时在过程中做好风险预案，确保不出大问题。
- **真实例子**：有一次Leader倾向成熟开源方案快速上线，我倾向自研轻量化方案。我写了对比文档，核心担忧是开源方案的定制成本在后期会很高。最终Leader决定先用开源快速验证，同时让我把自研方案的核心模块做了预研。两个月后业务验证完需求变了，基于预研的自研方案重构，比从头开始节约三周。这件事让我学到：**不追求当下最优，追求可逆的决策 + 留有后手。**

### 29.5 最大的缺点/自我认知

**核心思路**：说真实的、和工作相关的缺点，关键要有「认知到 + 在改 + 有可见变化」。这题的坑不是说了一个改不掉的性格缺陷。

**口述要点**：
- 我的缺点是有时候对技术方案过度追求「完备性」。设计服务时会下意识考虑很多极端场景——数据一致性、异常回滚、灰度切流、监控告警——结果方案评审时文档比别人多一倍，协作方会觉得「太复杂了，能不能简单点」。
- 意识到这个问题是在一次跨团队评审时，产品经理直接说「你这个方案我听不懂，能不能告诉我什么时候能上线」。我当时很受触动——**技术方案的价值不是自嗨，是被理解、被落地。**
- **改进动作**：我现在刻意逼自己做减法。每个方案文档开头必须有一段100字内的「一句话说清楚在干什么」。复杂方案先发一页纸轻量版，收到反馈再补细节。最近几次和产品、运营的协作基本没人提「听不懂」了。

### 29.6 期望薪资及谈判思路

**核心思路**：不亮底牌，先聊价值再聊价格。把薪资拆成base + 年终 + 股票/RSU三层，谈判时用框架而非固定数字。

**口述要点**：
- 我的期望薪资基于两个维度评估。一是市场对标——12年经验、电商核心链路、有完整0到1和大促保障经历，我会参考同级岗位的市场中位数；二是岗位价值——需要我从0搭建核心系统 vs 维护成熟系统，价值不同，期望定位也不同。
- **被追问具体数字时**：我现在年薪总包大概在XX万左右，希望新机会能有一定涨幅，但涨幅不是我第一考量。我更看重base部分的保障性和可持续性，年终奖的兑现率（是否有历史数据参考），以及如果有股票/RSU的话归属周期和公司阶段。这三点加在一起综合评估。
- **谈判技巧**：不在HR第一次问时就给精确数字，而是先了解公司对这个岗位的预算区间。如果区间和我的期望有偏差，不硬磕，而是聊「除了现金，有没有其他我能看到的增值空间」——期权、技术影响力、带团队的机会。有时候比月薪多几千更重要。

### 29.7 为什么选择我们公司

**核心思路**：提前做功课，找1-2个特定的技术/业务切入点。不要泛泛夸「大平台/好发展」。

**口述要点（面试前需按目标公司定制）**：
- 我关注到你们在XX业务方向上最近有一些动作，比如XX功能上线或XX技术重构。我在电商后端做了12年，对这个方向的系统复杂度是有体感的——比如XX场景下的库存实时性、多仓履约路由、高并发下的数据一致性——这些恰好是我过去一直在解决的问题。
- 另外我了解到你们目前在XX技术栈上有比较深的投入。我之前在类似的技术体系下带过核心项目的架构演进，踩过很多坑，也沉淀了一套稳定性治理的方法论。我觉得自己来了能比较快地产生价值，不是来学习的，是来输出的。
- 更深一层说，我看机会不仅是看薪资和岗位。我关注的是**这个业务是否处于上升期，技术挑战是否足够让我再成长**。

### 29.8 最有成就感的一件事

**核心思路**：不在技术多牛，在「你作为个体起到了什么不可替代的作用」。成就感来源要体现驱动力内核。

**推荐案例方向——主导大促稳定性改造**：
- 背景：交易链路核心服务经历一次大促接近极限——QPS到设计容量的90%，几个接口的RT出现尖刺。虽然不是故障但团队都很紧张。大促后Leader问我愿不愿意牵头做一个全链路的稳定性专项。
- 做了两个多月，涉及：(1) 梳理全链路强弱依赖，画了一张大图；(2) 核心链路线程池和连接池物理隔离；(3) 和QA一起建了接近生产的压测环境，输出容量预估模型；(4) 故障处理SOP + 上下游联合演练。
- 下次大促，核心链路QPS涨40%，RT反而降15%，全程零故障。
- 为什么有成就感？不是技术多难。是因为**我是这件事的发起者和推动者**——从发现问题、说服Leader投入资源、协调跨团队配合、到最终交付，从头到尾是我主导的。而且做完以后，这件事变成了团队的常态化机制，即使我离开，这套体系还在运转。这让我清楚自己的核心驱动力：**解决有价值的、系统性的问题，并让解决方案持续生效。**

### 29.9 你离开后团队还能正常运作吗

**核心思路**：加分题。体现的不是「我多重要」，而是「作为高级工程师的知识沉淀意识和梯队培养能力」。

**口述要点**：
- 我觉得能。而且我认为这恰恰是判断高级工程师成熟度的重要标准——你走之后团队是不是瘫痪了。
- 我日常刻意做了几件事：(1) **文档和知识外化**——负责的核心模块都有架构决策记录和运维手册，每次线上变更或故障后当场更新，文档是活的；(2) **On-call轮值**——前三次同类问题我带同事一起看并做复盘，之后同样问题让同事独立闭环，逼着知识从我脑子里转移到团队里；(3) **梯队培养**——带过的同学从需要我拆任务到独立负责子模块的设计上线。我的目标是让自己「可被替代」——这不是自我贬低，是对团队负责。
- 但也实实在在说：核心架构的理解深度和大型故障的经验判断，靠文档和日常带人无法完全传递，需要时间和实战。我离开短期内团队运维维护层面不会有问题，但遇到重大架构决策时可能需要一个过渡期。所以离职交接我一直做得很认真——留任期内把事情交代清楚，留任后也愿意做关键问题咨询。这是职业素养。

### 面试前速览清单

- 2 个项目 STAR，3-5 分钟讲清「我」的决策，不是「我们」
- Java 并发一条线：JMM → volatile → synchronized → AQS → ReentrantLock → CHM → ThreadLocal → 线程池
- Spring：三级缓存解决循环依赖 + 事务失效 6 种场景
- 分布式锁/MQ/注册中心/Dubbo：选型 + SPI + 灰度/压测/链路追踪
- 系统稳定性：限流熔断降级 + 黄金指标 + 1-5-10 应急 + 全链路灰度 + 强弱依赖治理
- 系统设计：5 步法 + 秒杀完整链路 + 短链/排行榜/Feed/IM 关键思路
- MySQL：MVCC RR vs RC + redo/undo/binlog + 索引/锁机制
- Redis：底层数据结构 + 持久化 + 集群 + 缓存一致性
- IO 模型：select→poll→epoll 演进 + Netty Reactor 模式
- JVM：GC 演进 CMS→G1→ZGC + 调优排查案例数据
- 项目管理：需求冲突四步法 + 排期buffer三级预警 + 跨团队利益对齐 + 技术债搭车重构 + 故障复盘5Why
- 3 个反问面试官的问题
