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
| 容器化基础 | **P2** | Docker镜像分层 + K8s核心概念 + 优雅上下线 |
| Elasticsearch | **P2** | 倒排索引/写入流程/脑裂 |



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

```
               有竞争(撤销偏向)
无锁 ──→ 偏向锁 ──→ 轻量级锁 ──(自旋失败/竞争加剧)──→ 重量级锁
  ↑          ↓ CAS替换ThreadID        ↓ CAS设置LockRecord指针
  │    同一线程重入（无需CAS）      自旋等待（自适应次数）
  │
  └── 不可降级（但批量重偏向/批量撤销机制可以降级到无锁状态下重新偏向）
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
| size | 先 3 次不加锁，失败后全局加锁 | baseCount + CounterCell[]（类似 LongAdder） |
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
- JDK7：先不加锁 sum 3 次，如果连续 2 次结果相同返回，否则全局加锁 → 性能差
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
- JDK8 扩容后位置计算：hash & oldCap == 0 → 原位置；== 1 → 原位置 + oldCap。不需要重新 hash

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
| 异常被 catch 了 | @Transactional 只对 RuntimeExcepiton/Error 回滚 |
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
- 面试时说："FactoryBean 是解决复杂 Bean 创建的模式，比如需要多步构建、需要返回代理对象的场景。getObject() 每次调用可能返回不同实例。"

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

**Seata AT 原理**：代理数据源，拦截 SQL → 解析前后镜像（UNDO_LOG）→ 生成回滚 SQL → 提交时一次性回滚。优点无侵入（业务代码零改动），缺点性能开销（前后镜像+全局锁）。

**选型核心**：大部分场景最终一致性就够了。最终一致性的落地关键：本地消息表 + MQ 发送 + 定时扫表补偿 + T+1 对账兜底。AT/TCC 的一致性收益要大于侵入性代价才值得用。高层次认知：好的架构设计应该通过业务边界划分和状态机设计来避免分布式事务，而不是引入更复杂的框架来处理它。

### 分布式锁

- Redisson 看门狗：默认 30s 过期，每 10s 续期，Netty 时间轮调度；Hash 结构可重入
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
- dubbo 协议（默认）：单一长连接+NIO+异步，适合小数据量高并发
- http 协议：短连接，适合异构系统或跨语言调用

**调用链路（一次完整 RPC）**：
```
Proxy → Cluster → LoadBalance → Filter Chain → Protocol → Exchanger → Transporter
```
- Proxy：代理层，封装调用细节；Cluster：集群容错（failover/failfast）；LoadBalance：负载均衡；Filter Chain：责任链（监控/鉴权/限流）；Protocol：协议层编解码；Exchanger：请求响应映射；Transporter：Netty 网络传输

**SPI 扩展机制**：
- JDK SPI：破坏性加载，一次性实例化所有实现（如所有 JDBC 驱动）
- Dubbo SPI：key-value 方式按需加载，`@SPI` 指定默认实现，`@Adaptive` 自动生成适配类，`ExtensionLoader.getExtensionLoader()` 获取扩展
- 这是 Dubbo 可插拔设计的灵魂——协议、注册中心、负载均衡、序列化全部通过 SPI 切换。JDK SPI 一次性实例化所有实现，Dubbo SPI 按需加载

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

## 五、MySQL 深度（P1）

### 5.1 索引原理

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

### 5.2 锁机制完整版（InnoDB RR）

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

### 5.3 日志系统：redo log / undo log / binlog

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

### 5.4 MVCC：RR vs RC 的 ReadView 差异

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

### 5.5 主从复制

| 复制格式 | 优点 | 缺点 |
|----------|------|------|
| STATEMENT | binlog 小 | 部分函数/存储过程可能不一致 |
| ROW | 精确 | binlog 大（推荐） |
| MIXED | 自动选择 | 复杂 |

**面试话术（30秒版）**：
> 「主从复制三个线程：主库的 dump 线程推送 binlog → 从库的 IO 线程接收写入 relay log → 从库的 SQL 线程回放 relay log。半同步复制在从库收到 relay log 后给主库 ACK，主库再返回客户端。并行复制（MySQL 5.7+）基于 group commit，同一个 binlog group 内的事务可以在从库并行回放。」

**追问：主从延迟怎么处理？**
- 业务层面：写完立即读 → 强制走主库（ShardingSphere 的 HintManager）
- 监控层面：pt-heartbeat 监测延迟秒数，超过阈值告警
- 架构层面：MGR（MySQL Group Replication）或自研中间件做读写分离的动态路由

### 5.6 SQL 优化

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

### 5.7 分库分表 & 数据治理

分片键选法、跨分片问题。补充数据生命周期管理：冷热分离（按时间分表+定时归档）、异构数据同步（Canal→ES/ClickHouse，延迟一致性怎么处理）。MySQL 8.0+ 不可见索引/降序索引（加分项）。

---

## 六、Redis 深度（P1）

### 6.1 数据结构底层

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

### 6.2 持久化机制

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

### 6.3 过期删除与内存淘汰

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

### 6.4 集群方案

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

### 6.5 缓存一致性

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

### 6.6 缓存三问题

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

### 6.7 Redis Pipeline、事务、大Key、热Key

**Pipeline（管道）**：批量发送命令→批量接收响应，减少 RTT。不是原子操作，只是网络优化。

**事务（MULTI/EXEC/WATCH）**：不支持回滚（语法错整个事务失败，运行时错只有错的那条失败）。WATCH 实现 CAS 乐观锁。

**Lua 脚本**：原子执行，减少网络往返，替代事务的常用方案。

**大Key**：String >10KB 或集合元素 >1万。危害→阻塞（DEL 大集合会卡主线程）、带宽打满、数据倾斜。排查→`redis-cli --bigkeys`/`MEMORY USAGE key`。删除→`UNLINK`（4.0+异步删）或分批删（`HSCAN` + `HDEL`）。

**热Key**：单 key QPS 极高把某个节点 CPU 打满。发现→`redis-cli --hotkeys`/客户端统计。解决→本地缓存/读写分离/热 key 多副本分散到不同节点。

---

## 七、消息队列深度（P1）

### 7.1 Kafka 架构

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

### 7.2 RocketMQ 架构

**架构角色**：NameServer（无状态路由，类似 Nacos 的简化版，不选举不持久化）→ Broker（主从）→ Producer/Consumer

**追问：RocketMQ 的 NameServer 和 Kafka 的 ZK 有何不同？**
- NameServer 极度简单：无状态、不选举、不持久化，节点间不通信
- 这是 RocketMQ 的架构哲学：用简单组件替代复杂组件，运维友好
- ZK 自身就是一个分布式系统（有选举/持久化/JVM 开销），Kafka 用 KRaft(Kafka Raft) 正在替代 ZK 依赖

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
- 不支持任意时间延迟，只支持预设的18个级别：1s/5s/10s/30s/1m/2m/3m/4m/5m/6m/7m/8m/9m/10m/20m/30m/1h/2h
- 实现：投递到 SCHEDULE_TOPIC_XXXX 系统主题，定时任务到时间后投递到目标 Topic
- 订单超时关单的典型场景

**消费者 Rebalance**（客户端驱动）：
- 触发条件：消费者数量变化、Topic 配置变化
- 过程：每个消费者定时拉取 Topic 路由信息和同一消费组的消费者列表，在**客户端独立计算**自己应消费哪些 Queue。与 Kafka 的 GroupCoordinator 驱动模式不同。
- 注意：Rebalance 期间短暂暂停消费（类似 Kafka 的 STW）

### 7.3 消息可靠性三种语义

| 语义 | 含义 | 实现方式 |
|------|------|---------|
| at most once | 最多一次，可能丢 | acks=0，异步发送 |
| **at least once** | 至少一次，可能重复 | acks=all + 同步发送 + 消费端幂等 |
| exactly once | 精确一次，不丢不重 | Kafka 幂等 Producer + 事务（或业务层幂等） |

面试时说：
> 「大多数业务场景 at least once + 消费者幂等就够了。exactly once 的代价很高（需要事务支持 + 性能下降），不是所有场景都值得。幂等可以通过业务唯一键 + DB 唯一索引 + Redis Set NX 实现。」

### 7.4 Kafka vs RocketMQ 选型对比（高频）

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

### 7.5 消息堆积处理

**面试话术**：
> 「消息堆积的核心思路是增加并行度，而不是简单加机器。手段包括：增加消费者数量（但受分区数限制，Kafka 分区数要 >= 消费者数）、批量消费、降级非核心逻辑、临时跳过堆积的非核心消息、紧急修复消费慢的代码性能瓶颈。关键是要有消费延迟的监控告警，不要等堆积了才发现。」

### 7.6 RocketMQ 可靠性

**三环节**：生产（同步+重试）→ Broker（同步刷盘+主从复制）→ 消费（手动ack+幂等+重试）

**幂等**：业务唯一键 → DB 唯一索引 → Redis Set NX

---

## 八、IO 模型 & Netty（P1）🔥

### 8.1 BIO / NIO / AIO

**面试话术（30秒版）**：
> 「BIO 一个连接一个线程，accept 和 read 都阻塞 → 连接多了线程切换开销无法承受。NIO 引入 Channel + Buffer + Selector 的 Reactor 模式，一个 Selector 线程管理多个 Channel，只有就绪的 Channel 才处理。AIO 更进一步——读写操作也异步，操作系统完成后再回调通知，但 Linux 上 AIO 不成熟，用的很少。Java 生态主力是 NIO + Netty。」

**三种模型对比**：

| 模型 | 连接/线程关系 | 阻塞点 | Java 实现 | 适用 |
|------|-------------|--------|-----------|------|
| BIO | 1:1 | accept + read 都阻塞 | ServerSocket | 低连接数、长连接少量场景 |
| NIO | M:1 | 只有 select 阻塞 | Selector + SocketChannel | 高并发连接、短连接 |
| AIO | M:0（回调） | 完全不阻塞 | AsynchronousChannel | Windows（IOCP），Linux 不成熟 |

### 8.2 select / poll / epoll

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

### 8.3 Netty 核心概念

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

## 九、分布式理论（P1）

### 9.1 CAP 与 BASE

**面试话术（30秒版）**：
> 「CAP 理论是分布式系统的经典约束：C（一致性）、A（可用性）、P（分区容错）三者最多同时满足两个。实际工程中 P 是必须选的（网络分区不可避免），所以核心决策是 CP 还是 AP——一致性优先（金融支付场景）选 CP，可用性优先（社交/电商）选 AP。BASE 是对 CAP 的工程妥协：Basically Available（基本可用）+ Soft state（软状态/中间态）+ Eventually consistent（最终一致）。」

**面试中怎么举例子**：
- CP 系统：ZooKeeper、etcd、HBase（一致性优先，网络分区牺牲可用性）
- AP 系统：Eureka、Cassandra、DynamoDB（可用性优先，允许临时不一致）
- Nacos 的巧妙之处：临时实例走 AP，永久实例走 CP → 一个组件同时满足两类需求

### 9.2 Raft 一致性协议

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

### 9.3 分布式 ID

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

### 9.4 分布式锁（延展）

已在 P0 技术选型中详细讨论，这里补充**红锁（Redlock）** 认知：
- Redlock 是 Redis 作者提出的多节点分布式锁方案，试图解决单节点锁不可靠的问题
- 争议：Martin Kleppmann（《数据密集型应用系统设计》作者）指出 Redlock 依赖时钟同步假设，时钟跳变会破坏安全性
- 面试时说：「学术界对 Redlock 有争议，工程中我的选择是 Redisson 单节点锁 + 业务幂等兜底。如果你真的需要强一致性的分布式锁，用 ZK 或 etcd。」

---

## 十、系统设计 & 算法（P1）

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

## 十一、JVM & 故障排查（P2）

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

## 十二、操作系统 & 网络基础（P2）

> 社招不会像校招那样手写代码，但底层原理会被问到。目标是能用 Java 工程师的类比讲清楚关键概念。

### 12.1 操作系统

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

### 12.2 网络基础

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
- 四种种服务类型：Unary（一应一答）、Server Streaming、Client Streaming、Bidirectional Streaming
- 适用场景：微服务间高性能通信（跨语言、强类型、有 IDL 约束）
- 面试时说：「gRPC 解决的是微服务间高性能通信问题——Protobuf 比 JSON 省带宽，HTTP/2 多路复用减少连接数，IDL 自动生成客户端代码消除手写 SDK 的开发成本。」

**WebSocket**：
- 全双工通信：通过 HTTP Upgrade 握手从 HTTP 升级到 WebSocket 协议
- 与 HTTP 短连接的对比：HTTP 每次请求都要建连+传头，WebSocket 一次握手后持续通信
- 适用：实时推送（IM消息、股价、协同编辑）、服务端主动通知
- 面试时说：「WebSocket 解决的是"服务端主动推"的需求。HTTP/2 的 Server Push 只能推静态资源，WebSocket 才是真正的双向实时通道。」

---

## 十三、设计模式在框架中的应用（P2）

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

## 十四、新趋势速览（P2）

### 虚拟线程（JDK 21，高频新考点）

M:N 映射，IO 密集型可开数万线程，写同步代码达异步性能。局限：ThreadLocal 开销（用 ScopedValue 替代）。

### 其他（知道即可，不展开）

- **可观测性**：OpenTelemetry 统一标准
- **AI 集成**（差异化谈资，2-3 句话）：Agent 通过 Function Calling/MCP 对接现有微服务体系

---

## 十五、Java 基础体系（P2）

> 面试中容易被当"默认应该会"来问的 Java 基础，表格式速查足够。

| 知识点 | 核心要点 | 一句话面试 |
|--------|---------|-----------|
| ArrayList vs LinkedList | 数组（O(1)随机访问）vs 双向链表（O(1)头尾插入），ArrayList 默认容量 10，扩容 1.5 倍 | 读多用 ArrayList，频繁头尾增删用 LinkedList |
| TreeMap | 红黑树实现，key 有序（自然序或 Comparator），put/get/remove O(logN) | 需要排序的映射场景；HashMap 无序，LinkedHashMap 按插入序 |
| 反射 | Class.forName / getDeclaredMethod / setAccessible，Spring IOC 和动态代理的基础 | 框架的"万能钥匙"——运行时拿类的元信息并操作，性能低于直接调用 |
| 泛型类型擦除 | 编译后 List\<String\> 和 List\<Integer\> 都是 List，桥接方法保证多态 | 编译期检查 + 运行期擦除，获取泛型参数靠反射 |
| 异常体系 | checked（必须 try-catch 或 throws，如 IOException）vs unchecked（RuntimeException，如 NPE） | Spring 事务只回滚 unchecked；checked 需要 rollbackFor 指定 |

---

## 十六、安全基础（P2）

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

## 十七、容器化基础（P2）

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

## 十八、Elasticsearch（P2）

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

### 面试前速览清单

- 2 个项目 STAR，3-5 分钟讲清「我」的决策，不是「我们」
- Java 并发一条线：JMM → volatile → synchronized → AQS → ReentrantLock → CHM → ThreadLocal → 线程池
- Spring：三级缓存解决循环依赖 + 事务失效 6 种场景
- 分布式锁/MQ/注册中心/Dubbo：选型 + SPI + 灰度/压测/链路追踪
- 系统设计：5 步法 + 秒杀完整链路 + 短链/排行榜/Feed/IM 关键思路
- MySQL：MVCC RR vs RC + redo/undo/binlog + 索引/锁机制
- Redis：底层数据结构 + 持久化 + 集群 + 缓存一致性
- IO 模型：select→poll→epoll 演进 + Netty Reactor 模式
- JVM：GC 演进 CMS→G1→ZGC + 调优排查案例数据
- 3 个反问面试官的问题
