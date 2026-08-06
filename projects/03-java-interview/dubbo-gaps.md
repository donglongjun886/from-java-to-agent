# Dubbo 面试题缺失清单

> 对照 README.md 第四节「微服务体系核心 → Dubbo 核心」(行773-815) 已覆盖内容，
> 以下为社招（P6+/P7）真实高频面试题中未覆盖的主题，按子话题分组。

---

## 一、服务暴露与引入全流程
- 服务暴露全流程：ServiceBean 触发 → ProxyFactory 封装 Invoker → Protocol.export（RegistryProtocol 负责注册元数据 vs DubboProtocol 负责真正启动 Netty Server）→ 注册中心注册 → Netty 端口监听
- 服务引入全流程：ReferenceBean → RegistryDirectory 注册中心订阅并拉取地址列表 → Protocol.refer → DubboInvoker → ProxyFactory.getProxy 生成动态代理对象 → Consumer 端本地地址缓存机制

## 二、集群容错与重试
- 集群容错 6 种模式详解：Failover（默认，读请求重试）/ Failfast（写请求快速失败）/ Failsafe（吞异常记日志）/ Failback（定时补偿重试）/ Forking（并行调用多Provider）/ Broadcast（广播所有Provider），各自选型场景
- 超时配置优先级链：Consumer 方法级 > Consumer 接口级 > Provider 方法级 > Provider 接口级 > 全局配置，retries 参数与幂等性冲突如何规避

## 三、序列化方案
- Dubbo 序列化方案对比：Hessian2（默认）vs Kryo vs Protobuf vs Fastjson，从性能 / 跨语言 / 兼容性三维度横向对比，为什么 Dubbo 2.x 默认选 Hessian2
- Hessian2 的局限性：对 Lambda、CompletableFuture、泛型嵌套、LocalDateTime 等部分 Java 特性兼容性不完善，生产踩坑场景及切换 Kryo/Protobuf 的时机

## 四、线程模型与并发控制
- Dubbo 线程模型分层：Netty Boss 线程（建连） → Worker 线程（IO 读写）→ Dubbo 业务线程池（执行 Provider 方法），各层职责与线程数调优依据
- 服务端线程池调优：默认固定 200 线程，IO 密集型 vs CPU 密集型的参数调整策略，线程池打满的排查思路

## 五、异步调用
- Dubbo 异步调用演进：2.6 时代通过 RpcContext.getContext().getFuture() 获取 Future vs 2.7+ 原生支持 CompletableFuture，Consumer 端异步 / Provider 端异步的写法差异
- 异步调用的坑：Callback 线程池耗尽风险（异步回调 QPS 高而线程池小导致积压），RpcContext Attachment 在异步场景下的透传丢失问题

## 六、扩展机制与高级特性
- 泛化调用原理与应用：GenericService 无需依赖 API Jar 包即可远程调用，核心参数（服务名/方法名/参数类型），典型场景（API 网关、测试平台、跨语言调用）
- Filter 机制深入：责任链设计原理，Provider 端内置 Filter 链路与执行顺序（EchoFilter → ClassLoaderFilter → GenericFilter → ContextFilter → ExecuteLimitFilter → TimeoutFilter → MonitorFilter → ExceptionFilter），自定义 Filter 三步：实现 Filter 接口 → @Activate 指定生效端 → SPI 文件注册
- ZooKeeper 注册中心存储结构：节点路径 /dubbo/com.xxx.Service/ 下的 providers / consumers / configurators / routers 子节点，节点内容（URL 格式），临时节点 + Watcher 变更推送机制
- Dubbo 3.x 应用级服务发现：接口级注册（每个接口一条数据）→ 应用级注册（每个应用一条数据），注册中心数据量如何减少 90%，元数据中心（MetadataReport）扮演的角色
- 多协议与多注册中心场景：同一服务同时暴露 dubbo 协议（对内 RPC）+ REST 协议（对外 HTTP），双注册中心热备 / 跨机房场景的同组服务不同注册中心配置
