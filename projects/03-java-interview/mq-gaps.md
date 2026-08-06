# MQ面试题缺漏清单

## Kafka

- 幂等生产者和事务消息原理（enable.idempotence、PID+SequenceNumber、事务协调器、LSO）
- 消费组分区分配策略（Range / RoundRobin / Sticky / CooperativeSticky 四种策略的区别与演进）
- 日志清理策略（delete vs compact，compact的原理和适用场景）
- 端到端不丢消息的完整配置链路（producer端retries+acks=all + broker端min.insync.replicas+unclean.leader.election.enable=false + consumer端手动提交）
- Leader Epoch机制（解决HW截断导致副本数据不一致的问题）
- 消息重复消费的常见原因与幂等处理方案（生产者重试导致重复 vs 消费者rebalance导致重复）

## RocketMQ

- 刷盘机制（同步刷盘 vs 异步刷盘，性能与可靠性的权衡，flushDiskType配置）
- 消息过滤（Tag过滤 vs SQL92属性过滤，实现原理和性能差异）
- 主从同步与高可用（同步复制 vs 异步复制，DLedger基于Raft的HA替代传统Master-Slave）
- 5.x新特性深入（Pop消费模式、Proxy代理层、Controller模式HA，与4.x的对比）
- 生产者负载均衡（默认轮询 vs 自定义MessageQueueSelector，与Kafka分区器的对比）

## 通用MQ

- 消息队列技术选型四维度（Kafka / RocketMQ / RabbitMQ / Pulsar 适用场景、性能边界、运维成本）
- 分布式事务最终一致性方案对比（本地消息表 vs RocketMQ半消息 vs Seata AT，各自优劣和适用场景）
- 生产环境MQ实战（消息丢失如何排查定位、重复消费如何兜底、堆积应急预案全流程）
- 消息队列如何保证高可用（Kafka的ISR+Leader选举 vs RocketMQ的Master-Slave+DLedger）
