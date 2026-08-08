# 算法刷题提纲

> 目标：HackerRank / LeetCode medium 通过。只列题型和题号，不写答案。

---

## 一、HashMap + 前缀和 + 双指针

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 1 | Two Sum | HashMap 存差值 |
| 3 | Longest Substring Without Repeating Characters | 滑动窗口 + HashSet |
| 560 | Subarray Sum Equals K | 前缀和 + HashMap |
| 15 | 3Sum | 排序 + 双指针 |
| 11 | Container With Most Water | 双指针向中间收 |

---

## 二、链表

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 206 | Reverse Linked List | 迭代 + 递归 |
| 21 | Merge Two Sorted Lists | 虚拟头节点 |
| 141 | Linked List Cycle | 快慢指针 |
| 19 | Remove Nth Node From End of List | 快慢指针差 N 步 |
| 160 | Intersection of Two Linked Lists | 双指针走对方的路 |

---

## 三、二叉树 + BFS/DFS

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 102 | Binary Tree Level Order Traversal | BFS + Queue |
| 104 | Maximum Depth of Binary Tree | 递归 max(left, right)+1 |
| 94 | Binary Tree Inorder Traversal | 递归 + 迭代(栈) |
| 112 | Path Sum | DFS 回溯 |
| 236 | Lowest Common Ancestor of a Binary Tree | 后序遍历递归 |

## 四、图 / 矩阵 BFS/DFS

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 200 | Number of Islands | DFS/BFS 标记已访问 |
| 207 | Course Schedule | 拓扑排序 / DFS 环检测 |
| 994 | Rotting Oranges | BFS 多源扩散 |
| 79 | Word Search | DFS + 回溯 + 标记恢复 |

---

## 五、排序 + 二分查找

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 704 | Binary Search | 基础二分模板 |
| 33 | Search in Rotated Sorted Array | 二分变种：判断有序侧 |
| 153 | Find Minimum in Rotated Sorted Array | 二分变种 |
| 56 | Merge Intervals | 排序 + 一次遍历 |
| 215 | Kth Largest Element in an Array | 快排 partition / 堆 PriorityQueue |

---

## 六、动态规划

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 70 | Climbing Stairs | 斐波那契 dp[i]=dp[i-1]+dp[i-2] |
| 53 | Maximum Subarray | Kadane: dp[i]=max(nums[i], dp[i-1]+nums[i]) |
| 198 | House Robber | 状态转移 dp[i]=max(dp[i-1], dp[i-2]+nums[i]) |
| 300 | Longest Increasing Subsequence | dp[i]=max(dp[j]+1) for j<i, nums[j]<nums[i] |
| 322 | Coin Change | 完全背包 |

---

## 七、回溯

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 78 | Subsets | 选/不选，回溯模板 |
| 39 | Combination Sum | 无限取，startIndex 防重 |
| 46 | Permutations | 全排列，used 标记 |
| 22 | Generate Parentheses | 左括号< n 加左，右<左 加右 |
| 17 | Letter Combinations of a Phone Number | 组合树，回溯经典 |

---

## 八、贪心

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 121 | Best Time to Buy and Sell Stock | 记录历史最低价 |
| 55 | Jump Game | 维护最远可达位置 |
| 435 | Non-overlapping Intervals | 按结束时间排序 + 贪心选择 |

---

## 九、字符串

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 14 | Longest Common Prefix | 逐个字符比对 |
| 49 | Group Anagrams | 排序后字符串作 key / 计数 |
| 5 | Longest Palindromic Substring | 中心扩散法 / DP |
| 76 | Minimum Window Substring | 滑动窗口（hard 题，但重要） |

---

## 十、栈 / 单调栈

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 20 | Valid Parentheses | 栈匹配 |
| 739 | Daily Temperatures | 单调递减栈 |
| 155 | Min Stack | 辅助栈存最小值 |

---

## 十一、堆 / PriorityQueue

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 347 | Top K Frequent Elements | HashMap 计数 + 小顶堆 |
| 23 | Merge k Sorted Lists | 小顶堆持续 poll 最小节点 |

---

## 十二、位运算

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 136 | Single Number | 异或 XOR，相同为 0 |
| 191 | Number of 1 Bits | n & (n-1) 消除最低位 1 |
| 338 | Counting Bits | dp[i] = dp[i>>1] + (i&1) |

---

## 十三、设计题

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 146 | LRU Cache | HashMap + 双向链表 |
| 460 | LFU Cache | HashMap + TreeMap 按频率淘汰 |

---

## HackerRank 备忘

- 切中文：右上角语言选择
- 开头模板：`import java.util.*; public class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); ... } }`
- 先看输入输出示例，比读英文描述快
- 时间充足先在本地 IDEA 跑通再粘贴
