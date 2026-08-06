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
| 141 | Linked List Cycle | 快慢指针 |
| 21 | Merge Two Sorted Lists | 虚拟头节点 |
| 160 | Intersection of Two Linked Lists | 双指针走对方的路 |
| 19 | Remove Nth Node From End of List | 快慢指针差 N 步 |

---

## 三、二叉树

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 102 | Binary Tree Level Order Traversal | BFS + Queue |
| 104 | Maximum Depth of Binary Tree | 递归 max(left, right)+1 |
| 94 | Binary Tree Inorder Traversal | 递归 + 迭代(栈) |
| 112 | Path Sum | DFS 回溯 |
| 236 | Lowest Common Ancestor of a Binary Tree | 后序遍历递归 |

---

## 四、排序 + 二分查找

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 704 | Binary Search | 基础二分模板 |
| 33 | Search in Rotated Sorted Array | 二分变种：判断有序侧 |
| 153 | Find Minimum in Rotated Sorted Array | 二分变种 |
| 56 | Merge Intervals | 排序 + 一次遍历 |
| 215 | Kth Largest Element in an Array | 快排 partition / 堆 PriorityQueue |

---

## 五、动态规划

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 70 | Climbing Stairs | 斐波那契 dp[i]=dp[i-1]+dp[i-2] |
| 53 | Maximum Subarray | Kadane: dp[i]=max(nums[i], dp[i-1]+nums[i]) |
| 322 | Coin Change | 完全背包 |
| 198 | House Robber | 状态转移 dp[i]=max(dp[i-1], dp[i-2]+nums[i]) |
| 300 | Longest Increasing Subsequence | dp[i]=max(dp[j]+1) for j<i, nums[j]<nums[i] |

---

## 六、栈 / 单调栈

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 20 | Valid Parentheses | 栈匹配 |
| 739 | Daily Temperatures | 单调递减栈 |
| 155 | Min Stack | 辅助栈存最小值 |

---

## 七、堆 / PriorityQueue

| 题号 | 题名 | 核心套路 |
|------|------|----------|
| 347 | Top K Frequent Elements | HashMap 计数 + 小顶堆 |
| 23 | Merge k Sorted Lists | 小顶堆持续 poll 最小节点 |

---

## HackerRank 备忘

- 切中文：右上角语言选择
- 开头模板：`import java.util.*; public class Solution { public static void main(String[] args) { Scanner sc = new Scanner(System.in); ... } }`
- 先看输入输出示例，比读英文描述快
- 时间充足先在本地 IDEA 跑通再粘贴
