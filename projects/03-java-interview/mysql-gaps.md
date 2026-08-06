# MySQL 面试补缺清单

## 事务基础（遗漏整节）
- 四种隔离级别各自解决的问题（脏读/不可重复读/幻读）及 InnoDB 实现方式
- InnoDB 如何实现 ACID（redo→持久性, undo→原子性, MVCC+锁→隔离性, 约束+undo→一致性）
- 长事务的危害（undo log 膨胀/锁长期持有/主从延迟）和监控方法

## 索引原理补充（6.1）
- Change Buffer 的作用和适用场景（为什么唯一索引的插入不走 Change Buffer）
- 前缀索引的选长策略（索引选择性计算，distinct / total）
- 为什么推荐自增主键（页分裂 vs UUID随机主键，插入性能差异原因）
- MySQL 8.0 函数索引（Functional Index）的使用场景和限制
- 优化器选错索引的原因（统计信息不准、回表代价估算偏差）和对策

## 锁机制补充（6.2）
- MDL 锁（Metadata Lock / 元数据锁）的作用和对 DDL/DML 阻塞的影响
- 自增锁的三种模式（innodb_autoinc_lock_mode=0/1/2）及高并发插入下的选择
- information_schema 锁等待视图排查实战（innodb_trx / innodb_locks / innodb_lock_waits）
- 悲观锁 vs 乐观锁在 MySQL 层的实现方式和各自适用场景
- 间隙锁对高并发插入的影响及降低锁冲突的实战方案
- 生产环境为什么不推荐使用外键约束

## 日志系统补充（6.3）
- Double Write Buffer 的原理（什么是部分页写/页断裂问题）
- Crash Recovery 过程（重启后 redo log 前滚 + undo log 回滚的完整流程）
- undo log 的 purge 线程工作机制（什么时候真正清理 delete-marked 记录）
- binlog 组提交（group commit）的原理和调优参数

## 主从复制补充（6.5）
- GTID（全局事务标识符）的原理、优势及与传统位点复制的对比
- 主从切换高可用方案（MHA / Orchestrator 工作原理）

## SQL 优化补充（6.6）
- 临时表产生的场景（group by/distinct/union/order by）和优化方法
- MySQL 8.0 EXPLAIN ANALYZE（输出实际执行代价，与 EXPLAIN 估算对比）
- 批量插入的优化手段（批量提交、关闭 autocommit、load data infile）
- 慢查询日志分析工具和方法论（pt-query-digest / 慢查询分析平台搭建思路）

## 分库分表深入（6.7）
- 分片策略对比（哈希取模、范围分片、一致性哈希）各自优缺点
- 跨分片分页/排序的实现方案（归并排序法、全局游标法）
- 分布式主键生成方案（雪花算法、号段模式、Redis 自增）及各自弊端
- 平滑扩容方案（一致性哈希+虚拟节点、双倍扩容法）
- 在线数据迁移方案（双写+数据校验、全量+增量同步）
- 分库分表中间件对比（ShardingSphere-Proxy vs MyCat vs Vitess 核心差异）

## DDL 与运维补充
- Online DDL 的原理（inplace / copy / INSTANT 三类算法差异）
- 大表 DDL 变更方案对比（gh-ost vs pt-online-schema-change vs 原生 online DDL）
- 数据库连接数的合理配置（连接池大小公式、最大连接数的判断依据）
- Buffer Pool 的内部结构（LRU 链表 young/old 分区、Free 链表、Flush 链表）及调优
- MySQL 8.0 不可见索引（Invisible Index）的使用场景和软删除实践
