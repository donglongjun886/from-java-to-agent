# Redis 面试题补缺清单

> 对照「七、Redis 深度（P1）」章节（7.1 ~ 7.7），以下为社招面试高频但尚未覆盖的题目方向。
> 仅列题目方向，不写答案。

---

## 1. 线程模型与IO多路复用（最高频缺口）

- Redis单线程模型的完整解释：为什么单线程能支撑高并发？
- IO多路复用机制：epoll/select/poll对比，Redis为什么选择epoll？
- Redis事件处理模型：文件事件 + 时间事件（serverCron）
- Redis 6.0引入多线程的背景：多线程的边界是什么？（网络IO多线程，命令执行仍单线程）
- 单线程的真正瓶颈在哪里？（大Key CPU密集操作、CPU核心无法水平扩展）

## 2. 阻塞场景排查与Lazy-free

- 哪些操作会阻塞Redis主线程？（KEYS/SMEMBERS/HGETALL/DEL大集合/FLUSHDB/AOF fsync）
- Redis 4.0 Lazy-free机制：UNLINK、FLUSHALL ASYNC、lazyfree-lazy-* 系列配置
- fork操作对性能的影响：内存越大fork越慢，10G内存场景下BGSave/fork耗时分析
- AOF刷盘策略对延迟的影响：always/everysec/no 三种策略的阻塞风险
- Swap（操作系统换页）导致Redis延迟抖动的排查

## 3. 内存优化与碎片管理

- 内存碎片率（mem_fragmentation_ratio）的含义：正常范围、何时需要关注（>1.5）
- 内存碎片整理（activedefrag）的触发条件和参数配置
- jemalloc 内存分配器的特点：与glibc malloc的对比，为什么Redis选择jemalloc
- 共享对象池机制：Redis默认共享0-9999的整数对象，为什么批量创建整数key内存占用低
- 如何估算一个key的实际内存占用？（内存模型：redisObject + SDS/dictEntry等结构开销）
- bigkey对内存碎片的加剧效应

## 4. 慢查询与性能诊断

- slowlog的配置与解读：slowlog-log-slower-than、slowlog-max-len，输出字段含义
- latency monitor的使用：latency doctor/latency graph/latency history 命令
- 如何系统性排查Redis延迟抖动？（三个维度：命令端、网络端、系统端）
- INFO commandstats 分析命令分布，识别高频危险命令
- redis-cli --bigkeys 的局限性（只是key采样，不反映实际内存占用）与改进方案
- redis-cli --hotkeys 的工作原理（基于LFU采样）

## 5. Redis Stream 消息队列

- Stream的数据结构：消息链表 + 消费组，底层用Rax（基数树）
- 消费组机制：XREADGROUP、pending列表、XACK确认、消息回溯（XREADGROUP + 0）
- Stream vs List vs PubSub 的场景对比与选型
- Stream与Kafka的定位差异：轻量级消息队列 vs 分布式流平台
- 消费者挂掉后pending消息的处理：XCLAIM转移待处理消息

## 6. 高级数据结构应用

- HyperLogLog：基数统计原理（调和平均数），UV统计场景，误差率0.81%，PFADD/PFCOUNT/PFMERGE
- Bitmap：位图操作，签到打卡、活跃用户统计，SETBIT/GETBIT/BITCOUNT/BITOP/BITFIELD
- GEO：地理位置（附近的人），底层用ZSet+GeoHash编码，GEOADD/GEORADIUS/GEODIST
- RedisBloom模块：布隆过滤器（比应用层手写布隆性能更高，支持扩容）
- Sorted Set在实时排行榜中的应用（ZINCRBY + ZREVRANGE）

## 7. Redis Sentinel 深入

- 主观下线（SDOWN）vs 客观下线（ODOWN）的判定流程差异
- Sentinel leader选举机制：基于Raft的简化版，epoch概念
- 故障转移完整流程：ODOWN判定 → Sentinel leader选举 → 选新主节点 → 通知所有从节点 → 更新配置
- 脑裂场景分析：网络分区导致出现多个主节点，min-slaves-to-write/min-slaves-max-lag 如何缓解
- 为什么Sentinel集群推荐至少3个节点？（多数派判定，防止单Sentinel误判下线）
- Sentinel的发布订阅通信机制（__sentinel__:hello频道）

## 8. 缓存一致性与Canal深入

- 先更新DB后删缓存，删除失败的重试策略（消息队列异步重试、定时任务补偿）
- Canal的工作原理：伪装成MySQL Slave，解析binlog（row模式），投递到MQ/Kafka触发缓存更新
- Canal延迟对一致性的影响：从DB写入到缓存更新的端到端延迟分析
- 最终一致性窗口期的业务容忍度：什么场景能接受多长时间的不一致
- 读写分离架构下的缓存同步坑：主从同步延迟 + 先删缓存超时 = 缓存里的数据比DB从库还旧

## 9. 缓存预热与多级缓存架构

- 系统重启/新版本上线时的缓存预热策略：离线脚本预加载、日志回放、AOF回放
- 多级缓存架构设计：本地Caffeine + 远程Redis，各级的TTL与数据一致性如何保证
- 热点发现与自动降级：如何实现热key自动探测并下沉到本地缓存
- 缓存全量失效时的降级兜底：DB压力评估、限流策略配合

## 10. 数据倾斜与集群运维

- Cluster模式下数据倾斜的原因分析：hash tag设计不当、业务热点数据、slot分配不均
- 热Key在Cluster中的放大效应：单分片CPU打满，影响同分片其他key
- slot迁移的详细过程（redis-cli --cluster reshard）：MIGRATE命令的工作原理
- slot迁移期间对线上性能的影响（MIGRATE是阻塞式的，如何降低影响）
- 集群扩容/缩容的最佳实践与灰度策略

## 11. 主从复制深入

- 全量同步对主库的三重影响：fork耗时 + RDB磁盘IO + RDB网络传输带宽
- repl-diskless-sync（无盘复制）：原理、优缺点、适用场景
- repl-backlog-size 的合理估算：根据写入QPS和最大可容忍断连时间计算
- 主从复制延迟监控：INFO replication 中 slave_repl_offset 与 master_repl_offset 的差值
- 主从切换可能丢数据的场景分析：异步复制的天然窗口，低延迟网络下也「至少丢失几毫秒」
