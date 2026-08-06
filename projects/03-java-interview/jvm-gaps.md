## GC 深度

1. G1 的 Region 类型有哪些？Mixed GC 的完整流程是怎样的？
2. Young GC（Minor GC）、Mixed GC、Full GC 分别的触发条件是什么？
3. 对象晋升到老年代的几种情况？动态年龄判断的机制是怎样的？
4. 三色标记法（Tri-color Marking）的工作原理？漏标的两个必要条件？CMS 的 Incremental Update 和 G1 的 SATB 分别怎么解决漏标？
5. G1 中 Remembered Set (RSet) 和 Card Table 各有什么作用？为什么 G1 需要 RSet 来维护跨 Region 引用？
6. GC 日志怎么读？如何从日志中区分 Young GC / Mixed GC / Full GC？关键指标（暂停时间、回收量、堆变化）怎么看？
7. CMS 的 7 个阶段分别是什么？哪些阶段是 STW 的？哪些是并发的？
8. G1 的 Humongous 对象（大对象）分配存在什么问题？为什么可能导致提前 Full GC？
9. ZGC 的染色指针（Colored Pointer）原理？相比 G1 的屏障机制有什么本质区别？

## JVM 内存结构

10. JVM 运行时数据区各区域（堆/虚拟机栈/方法区/程序计数器/本地方法栈）分别存储什么？各自会抛什么异常（OOM / StackOverflow）？
11. 方法区/元空间（Metaspace）什么场景会 OOM？怎么排查？
12. 直接内存（Direct Memory）OOM 的表现是什么？和堆 OOM 有什么区别？怎么排查？
13. 强引用、软引用、弱引用、虚引用的区别和各自的使用场景？

## JIT & 编译优化

14. JIT 编译器 C1（Client Compiler）和 C2（Server Compiler）的区别？分层编译（Tiered Compilation）的原理和优势？
15. 逃逸分析、标量替换、锁消除、栈上分配 四者之间的关系和协作流程？（上一节已零星提及锁消除/逃逸分析，此处应串联成完整链路）
16. 方法内联（Method Inlining）的触发条件和限制是什么？（方法体大小、调用深度、虚方法/接口调用）

## 类加载深入

17. 类加载过程中「准备」阶段和「初始化」阶段的区别？静态变量和静态代码块的执行时机？（区分 static final 基本类型 vs static final 引用类型的赋值时机）
18. 类卸载（Class Unloading）的条件是什么？什么场景下一个类永远不会被卸载？
19. 自定义类加载器的典型应用场景和注意事项？（热部署、字节码加密、多版本共存）

## 调优 & 排查

20. 频繁 Full GC 的排查思路和优化方法论？（要讲分析路径和决策链，不是罗列工具）
21. Arthas 常用命令和各自的排查场景？（watch / trace / tt / monitor / thread / vmoption / profiler）
22. 生产环境 JVM 参数怎么规划？常用的关键参数和调优经验？
23. SafePoint（安全点）是什么？什么场景会导致 STW 时间过长？「Stop The World」具体在等什么？
