# -*- coding: utf-8 -*-
"""
Python 基础语法教程 - C# 开发者对比版
=====================================
本文件专为有 C# / Unity 背景的开发者编写，对比两种语言的语法差异。

C# 特点速查:
    - 静态类型语言: int x = 5;
    - 类是引用类型 (class) 或值类型 (struct)
    - 使用 { } 定义代码块
    - 必须显式定义方法可见性: public, private, protected
    - 枚举: enum Type { A, B }
    - 接口: interface IName { }
    - 属性: public int Age { get; set; }
    - Lambda: (x, y) => x + y
"""

# =============================================================================
# 01. 变量与数据类型
# =============================================================================

# ---------- Python: 动态类型 (赋值时自动推断) ----------
# C#:   int age = 30;
#       string name = "Alice";
# Python: 类型是可选的，Python 3.6+ 支持类型注解 (类似 TS 的写法)
name: str = "Alice"  # 类型注解只是提示，不强制
age: int = 30
height: float = 1.75
is_active: bool = True

# ---------- Python 无需分号，换行即语句结束 ----------
# C# 语句以分号 ; 结束
# Python 无分号，通过换行识别语句结束
# 如果一行太长，用 \ 续行 (不推荐，更推荐括号包裹)

# ---------- 内置数据类型对比 ----------
# C#                      Python
# int                     int (无 long/short 区分，精度无限)
# float/double           float (统一双精度，约 1.8e+308)
# decimal                Decimal (精确小数，用于金融计算)
# bool                    bool
# char                    str (单字符也是 str，长度为1)
# string                  str
# object                  object
# byte[], char[]          bytes, bytearray

# ---------- 字符串 ----------

# C#: $"Hello, {name}"
# Python: f-string (Python 3.6+)，语法更简洁
greeting: str = f"Hello, {name}, age is {age}"
print(greeting)  # Hello, Alice, age is 30

# 多行字符串
multiline: str = """
    这是第一行
    这是第二行
    这是第三行
"""
# C#: 使用 @"..." 或 stringBuilder

# ---------- 类型转换 ----------
# C#: int.Parse("42"), (int)3.14, Convert.ToInt32(3.14)
# Python: 直接函数转换
int("42")       # str -> int
str(123)        # int -> str
float("3.14")   # str -> float
bool(0)         # 0 为 False，非0为 True
bool("")        # 空字符串为 False
bool(None)      # None 相当于 C# 的 null

# ---------- None (空值) ----------
# C#: null
# Python: None (单例对象)
nothing: None = None

# ========== 【注意事项】==========
# 1. Python 的整数没有溢出问题，精度无限
# 2. Python 的 float 是双精度，与 C# 的 double 相同
# 3. Python 没有 char 类型，单字符也是 str
# 4. Python 的布尔值 True/False (首字母大写)，不是 true/false


# =============================================================================
# 02. 运算符
# =============================================================================

# ---------- 算术运算符 ----------
# C# 和 Python 基本相同: + - * / // % **
# 区别: Python 有 ** 幂运算符
result: float = 2 ** 3  # 8，等价于 C# 的 Math.Pow(2, 3)
result = 10 // 3        # 3，整除 (C#: 10 / 3 = 3.333... 但整数除法 10 / 3 = 3)
result = 10 % 3         # 1，取余

# ---------- 比较运算符 ----------
# C#: == != > < >= <=
# Python: 完全相同

# ---------- 逻辑运算符 ----------
# C#: && || !
# Python: and or not
if age > 18 and name == "Alice":
    print("Alice is adult")

if not is_active:
    print("Inactive")

# ---------- 身份运算符 (Python 特有) ----------
# is  : 判断两个对象是否是同一个引用 (相当于 C# 的 ReferenceEquals)
# is not: 判断两个对象是否不是同一个引用
a: list = [1, 2, 3]
b: list = a       # b 和 a 指向同一个对象
c: list = [1, 2, 3]  # c 是新对象，内容相同但引用不同

print(a is b)    # True，同一个引用
print(a is c)    # False，不同引用
print(a == c)    # True，内容相同 (调用了 __eq__)

# ---------- 成员运算符 (Python 特有) ----------
# in : 判断元素是否在容器中
# not in
if "a" in "abc":
    print("Found")

if 1 in [1, 2, 3]:
    print("In list")

# ========== 【注意事项】==========
# 1. Python 没有 ++ 和 -- 运算符，使用 += 1 或 -= 1
# 2. Python 的 / 是精确除法 (float)，// 是整除
# 3. is 比较引用，== 比较值，不要混淆


# =============================================================================
# 03. 条件语句
# =============================================================================

# ---------- if-elif-else ----------
# C#: if () { } else if () { } else { }
# Python: 用 elif 而不是 else if，没有大括号
score: int = 85

if score >= 90:
    grade: str = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "D"

# ---------- Python 没有 switch ----------
# C# 有 switch-case
# Python 用字典或 if-elif 模拟
day: int = 3
day_name: str
if day == 1:
    day_name = "Monday"
elif day == 2:
    day_name = "Tuesday"
# ... 较长

# 更 Python 的写法: 字典映射
days: dict = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday"}
day_name = days.get(day, "Unknown")  # get 方法，默认值

# ---------- 三元表达式 ----------
# C#: string result = condition ? "yes" : "no";
# Python: 语法略有不同
result: str = "yes" if score > 60 else "no"

# ---------- match (Python 3.10+) ----------
# 类似于 C# 的 switch，但更强大
match day:
    case 1:
        day_name = "Monday"
    case 2:
        day_name = "Tuesday"
    case 3:
        day_name = "Wednesday"
    case _:
        day_name = "Unknown"

# ========== 【注意事项】==========
# 1. Python 用缩进 (4空格) 而不是大括号定义代码块
# 2. 不要忘记冒号 : ，每个 if/for/def 等语句后都要加
# 3. 条件表达式不加括号，但可以加括号提高可读性


# =============================================================================
# 04. 循环语句
# =============================================================================

# ---------- for 循环 ----------
# C#: for (int i = 0; i < 10; i++) { }
# Python: 更像 foreach
# C#: foreach (var item in collection) { }
# Python: for item in collection:
for i in range(10):  # 0-9
    print(i)

for i in range(5, 10):  # 5-9
    print(i)

for i in range(0, 10, 2):  # 0,2,4,6,8
    print(i)

# 遍历列表 (类似 C# List<T>)
fruits: list = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# 带索引遍历
for index, fruit in enumerate(fruits):
    print(f"{index}: {fruit}")

# ---------- while 循环 ----------
# C# 和 Python 语法几乎相同
count: int = 0
while count < 5:
    print(count)
    count += 1

# ---------- break, continue, else ----------
# Python 的 for 和 while 循环可以带 else 子句
# else 在循环正常结束时执行 (不是 break 退出时)
for i in range(5):
    if i == 3:
        break  # 跳出循环，不执行 else
    print(i)
else:
    print("Loop completed normally")  # 不会打印，因为被 break 跳过

# continue 示例
for i in range(5):
    if i == 2:
        continue  # 跳过本次迭代，继续下一次
    print(i)  # 0,1,3,4

# ---------- 列表推导式 (Python 特有) ----------
# C#: var squares = Enumerable.Range(0, 10).Select(x => x * x).ToList();
# Python: 更简洁
squares: list = [x ** 2 for x in range(10)]        # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
even_squares: list = [x ** 2 for x in range(10) if x % 2 == 0]  # 偶数的平方

# ========== 【注意事项】==========
# 1. Python 没有 i++，必须用 i += 1
# 2. Python 没有 foreach 关键字，直接 for ... in
# 3. 列表推导式很强大，但复杂时影响可读性，适度使用


# =============================================================================
# 05. 字符串操作
# =============================================================================

# ---------- 基本操作 ----------
s: str = "Hello, World!"

# 长度 (C#: s.Length)
length: int = len(s)

# 索引访问 (C#: s[0])
char: str = s[0]   # 'H'
char = s[-1]       # '!' (倒数第一个)

# 切片 (Python 特有，C# 没有直接等价物)
sub: str = s[0:5]      # 'Hello' (索引0到4)
sub = s[7:]            # 'World!' (索引7到末尾)
sub = s[:5]            # 'Hello' (开头到索引4)
sub = s[::2]           # 'Hlo ol!' (步长2)
sub = s[::-1]          # '!dlroW ,olleH' (反转字符串)

# ---------- 查找和替换 ----------
# C#: s.IndexOf("World"), s.Replace("World", "Python")
s.find("World")     # 7，返回索引，未找到返回 -1
s.index("World")    # 7，类似 find，但未找到抛出异常
s.replace("World", "Python")  # 'Hello, Python!'
s.count("l")        # 2，统计出现次数

# ---------- 分割和连接 ----------
# C#: s.Split(','), string.Join(",", array)
parts: list = s.split(",")          # ['Hello', ' World!']
joined: str = "-".join(["a", "b", "c"])  # 'a-b-c'

# ---------- 大小写 ----------
# C#: s.ToLower(), s.ToUpper()
s.lower()   # 'hello, world!'
s.upper()   # 'HELLO, WORLD!'
s.capitalize()  # 'Hello, world!' (首字母大写)
s.title()   # 'Hello, World!' (每个单词首字母大写)

# ---------- 去除空白 ----------
# C#: s.Trim(), s.TrimStart(), s.TrimEnd()
s.strip()   # 去除两端空白
s.lstrip()  # 去除左端
s.rstrip()  # 去除右端

# ---------- 格式化 ----------
# C#: string.Format("Hello {0}", name), $"Hello {name}"
# Python: f-string (推荐), str.format(), % 格式化 (不推荐)
name = "Alice"
age = 30

# f-string (Python 3.6+，最推荐)
formatted = f"{name} is {age} years old"

# format 方法
formatted = "{} is {} years old".format(name, age)
formatted = "{0} is {1} years old".format(name, age)  # 位置参数
formatted = "{name} is {age} years old".format(name=name, age=age)  # 命名参数

# 格式化数字
pi: float = 3.14159
formatted = f"Pi is {pi:.2f}"  # 'Pi is 3.14' (保留2位小数)
formatted = f"Pi is {pi:10.2f}"  # 右对齐，总宽度10

# ---------- 字符串判定 ----------
# C#: string.IsNullOrEmpty(s), s.StartsWith("Hello")
s.isdigit()       # 是否全是数字
s.isalpha()       # 是否全是字母
s.isalnum()       # 是否全是字母或数字
s.isspace()       # 是否全是空白
s.startswith("Hello")  # 是否以 Hello 开头
s.endswith("!")   # 是否以 ! 结尾

# ========== 【注意事项】==========
# 1. Python 字符串是不可变的 (immutable)，所有"修改"操作返回新字符串
# 2. 切片是左闭右开 [start:end)，end 位置的字符不包含
# 3. 负数索引从 -1 开始，-1 是最后一个元素
# 4. f-string 中用 {{ 和 }} 表示字面的大括号


# =============================================================================
# 06. 列表 (List)
# =============================================================================

# ---------- 创建 ----------
# C#: var list = new List<int> { 1, 2, 3 };
# Python: 直接用方括号
nums: list = [1, 2, 3, 4, 5]
mixed: list = [1, "hello", 3.14, True]  # 可以混合类型 (不推荐)

# ---------- 索引和切片 ----------
# C#: list[0], list[0..2] (C# 8.0+ 范围)
first: int = nums[0]   # 1
last: int = nums[-1]  # 5
slice_list: list = nums[1:4]  # [2, 3, 4]

# ---------- 修改 ----------
# C#: list.Add(), list.Insert(), list.Remove(), list.RemoveAt()
nums.append(6)    # 末尾添加
nums.insert(0, 0) # 在索引0插入
nums.extend([7, 8])  # 末尾添加多个
nums.remove(3)    # 删除第一个匹配的值为 3 的元素
nums.pop()        # 弹出并返回最后一个元素
nums.pop(0)       # 弹出并返回索引0的元素
del nums[0]       # 删除索引0的元素

# ---------- 查找 ----------
# C#: list.Contains(), list.IndexOf()
index: int = nums.index(3)  # 找到返回索引，未找到抛出异常
exists: bool = 3 in nums    # True，成员检查

# ---------- 排序 ----------
# C#: list.Sort(), list.OrderBy()
nums.sort()       # 原地排序 (修改原列表)
sorted_nums: list = sorted(nums)  # 返回新的排序列表

# 降序
nums.sort(reverse=True)
sorted_nums = sorted(nums, reverse=True)

# 按绝对值排序
abs_sorted = sorted([-3, -1, 2, -2], key=abs)

# ---------- 反转 ----------
# C#: list.Reverse()
nums.reverse()  # 原地反转

# ---------- 列表推导式 ----------
squares: list = [x ** 2 for x in range(10)]
matrix: list = [[i * j for j in range(3)] for i in range(3)]  # 3x3 矩阵

# ---------- 其他方法 ----------
nums: list = [1, 2, 3, 4, 5]
len(nums)     # 5，长度
nums.count(2) # 1，统计元素出现次数
nums.clear()  # 清空列表

# ---------- 解包 (Unpacking) ----------
a, b, c = [1, 2, 3]  # 对应赋值
first, *rest = [1, 2, 3, 4]  # first=1, rest=[2,3,4]

# 交换变量 (不需要临时变量)
a, b = 1, 2
a, b = b, a  # a=2, b=1

# ========== 【注意事项】==========
# 1. 列表是动态数组，不是链表，索引访问 O(1)，插入/删除 O(n)
# 2. 列表可以包含任意对象，包括函数、类等
# 3. 列表引用是浅拷贝，要深拷贝用 copy 模块
# 4. *rest 在函数参数中叫星号参数，用于收集剩余参数


# =============================================================================
# 07. 元组 (Tuple)
# =============================================================================

# ---------- 创建 ----------
# C#: ValueTuple<int, string> tuple = (1, "hello");
# Python: 用圆括号，与列表相似但不可变
point: tuple = (3, 4)
colors: tuple = ("red", "green", "blue")

# 可以不用括号，但建议加
point = 3, 4  # 也是元组

# ---------- 索引和切片 ----------
# 与列表相同
x: int = point[0]  # 3
y: int = point[1]  # 4

# ---------- 解包 ----------
# C#: var (x, y) = point; (C# 7.0+)
x, y = point  # x=3, y=4

# 交换变量
a, b = 1, 2

# ---------- 命名元组 (Named Tuple) ----------
from collections import namedtuple

Point = namedtuple('Point', ['x', 'y'])
p: Point = Point(3, 4)
print(p.x, p.y)  # 3 4，像对象一样用点访问

# ---------- 返回多个值 ----------
# Python 函数可以返回元组，实现多返回值
def get_stats(numbers: list) -> tuple:
    return min(numbers), max(numbers), sum(numbers)

min_val, max_val, total = get_stats([1, 2, 3, 4, 5])

# ========== 【注意事项】==========
# 1. 元组是不可变的，创建后不能修改 (类似 C# 的 Tuple)
# 2. 元组比列表更轻量，性能更好
# 3. 元组可以作为字典的键 (因为不可变)，列表不行
# 4. 单元素元组需要加逗号: (1,) 而不是 (1)


# =============================================================================
# 08. 字典 (Dictionary)
# =============================================================================

# ---------- 创建 ----------
# C#: var dict = new Dictionary<string, int> { { "a", 1 }, { "b", 2 } };
# Python: 键值对，用大括号
ages: dict = {"Alice": 30, "Bob": 25, "Charlie": 35}

# 键值对可以是任意不可变对象
mixed: dict = {"int": 1, "float": 2.5, "tuple": (1, 2)}

# 字典推导式
squares_dict: dict = {x: x ** 2 for x in range(5)}  # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# ---------- 访问 ----------
# C#: dict["key"], dict.TryGetValue()
age: int = ages["Alice"]  # 30
# C#: dict.ContainsKey() 检查键存在
# Python: in 检查键
if "Alice" in ages:
    print(ages["Alice"])

# get 方法 (推荐，更安全)
age = ages.get("Alice")           # 30
age = ages.get("Unknown", 0)       # 0，键不存在返回默认值

# ---------- 添加和修改 ----------
ages["David"] = 40  # 添加新键值对
ages["Alice"] = 31  # 修改已有键的值

# update 批量更新
ages.update({"Alice": 32, "Bob": 26})

# ---------- 删除 ----------
# C#: dict.Remove("key")
del ages["Charlie"]  # 删除键值对
removed = ages.pop("Bob")  # 删除并返回值

# 清空
ages.clear()

# ---------- 遍历 ----------
ages: dict = {"Alice": 30, "Bob": 25, "Charlie": 35}

# 遍历键
for key in ages:
    print(key)

# 遍历值
for value in ages.values():
    print(value)

# 遍历键值对
for key, value in ages.items():
    print(f"{key}: {value}")

# ---------- 其他方法 ----------
len(ages)       # 3，键值对数量
keys = ages.keys()    # dict_keys(['Alice', 'Bob', 'Charlie'])
values = ages.values()  # dict_values([30, 25, 35])
items = ages.items()   # dict_items([('Alice', 30), ...])

# copy
ages_copy = ages.copy()  # 浅拷贝

# ========== 【注意事项】==========
# 1. 字典的键必须是不可变对象 (str, int, tuple 等)
# 2. 字典保持插入顺序 (Python 3.7+)
# 3. 字典查找是 O(1) 平均复杂度
# 4. 不要用字典的键值作为默认参数传递


# =============================================================================
# 09. 集合 (Set)
# =============================================================================

# ---------- 创建 ----------
# C#: var set = new HashSet<int> { 1, 2, 3 };
# Python: 用大括号，但没有键值对就是集合
nums: set = {1, 2, 3, 4, 5}
# 空集合创建
empty_set: set = set()  # 不能用 {}，那是空字典

# ---------- 操作 ----------
# C#: set.Add(), set.Remove(), set.Contains()
nums.add(6)         # 添加
nums.remove(3)      # 删除，不存在会抛出异常
nums.discard(3)     # 删除，不存在不报错
exists: bool = 3 in nums  # 成员检查

# ---------- 集合运算 ----------
a: set = {1, 2, 3, 4}
b: set = {3, 4, 5, 6}

union = a | b           # 并集: {1, 2, 3, 4, 5, 6}
intersection = a & b   # 交集: {3, 4}
difference = a - b     # 差集: {1, 2}
symmetric_diff = a ^ b # 对称差集: {1, 2, 5, 6}

# ---------- 集合方法 ----------
a.union(b)             # 返回并集
a.intersection(b)      # 返回交集
a.difference(b)        # 返回差集
a.symmetric_difference(b)  # 返回对称差集

# 判断关系
a.issubset(b)          # a 是否是 b 的子集
a.issuperset(b)        # a 是否是 b 的超集
a.isdisjoint(b)        # a 和 b 是否没有交集

# ========== 【注意事项】==========
# 1. 集合中的元素必须是不可变的 (可哈希的)
# 2. 集合不保持顺序，不支持索引访问
# 3. 集合主要用于去重和成员测试 (O(1) 复杂度)
# 4. 集合运算是 Python 特有的优雅语法


# =============================================================================
# 10. 函数
# =============================================================================

# ---------- 基本定义 ----------
# C#: int Add(int a, int b) { return a + b; }
# Python: def 函数名(参数):
def add(a: int, b: int) -> int:
    return a + b

# ---------- 默认参数 ----------
# C#: void Greet(string name = "World")
def greet(name: str = "World") -> str:
    return f"Hello, {name}!"

# 注意: 默认参数必须是不可变对象，不要用列表或字典作为默认参数
# 错误示例: def func(items=[])  # 危险!

# ---------- 可变参数 ----------
# C#: params int[] nums
# Python: 用 *args 收集位置参数
def sum_all(*args) -> int:
    total = 0
    for num in args:
        total += num
    return total

result = sum_all(1, 2, 3, 4, 5)  # 15

# 用 **kwargs 收集关键字参数
def print_info(**kwargs):
    for key, value in kwargs.items():
        print(f"{key}: {value}")

print_info(name="Alice", age=30, city="Beijing")

# ---------- 解包参数 ----------
# 将列表或元组解包为位置参数
nums: list = [1, 2, 3]
print(*nums)  # 相当于 print(1, 2, 3)

# 将字典解包为关键字参数
config: dict = {"host": "localhost", "port": 8080}
# def connect(host, port): ...
# connect(**config)  # 相当于 connect(host="localhost", port=8080)

# ---------- 匿名函数 (Lambda) ----------
# C#: Func<int, int, int> add = (a, b) => a + b;
# Python: lambda 参数: 表达式
add: function = lambda a, b: a + b
add(1, 2)  # 3

# 多行 lambda 不推荐，应该用 def
# lambda 常用场景: 排序、回调、函数参数
pairs: list = [(1, "one"), (3, "three"), (2, "two")]
pairs.sort(key=lambda x: x[0])  # 按第一个元素排序

# ---------- 装饰器 (Decorator) ----------
# Python 特有，C# 有特性 (Attribute) 但不完全相同
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("Before function")
        result = func(*args, **kwargs)
        print("After function")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()

# ---------- 闭包 (Closure) ----------
# C# 的闭包类似
def make_multiplier(factor: int):
    def multiplier(x: int) -> int:
        return x * factor
    return multiplier

times3 = make_multiplier(3)
print(times3(5))  # 15

# ---------- 生成器 (Generator) ----------
# Python 特有，用于惰性求值
def count_up_to(n: int):
    i = 1
    while i <= n:
        yield i  # C# 用 yield return
        i += 1

for num in count_up_to(5):
    print(num)

# ========== 【注意事项】==========
# 1. Python 函数是一等公民，可以作为参数、返回值、赋值给变量
# 2. 函数没有返回类型声明 (只有 -> 注解)，不强制返回值类型
# 3. 默认参数不要用可变对象 (list, dict, set)
# 4. *args 和 **kwargs 可以同时使用
# 5. Python 没有方法重载 (同名方法只保留最后一个)，用默认参数或 *args 模拟


# =============================================================================
# 11. 类和对象
# =============================================================================

# ---------- 基本定义 ----------
# C#: public class Person { private string name; public Person(string name) { this.name = name; } }
# Python: 没有 public/private 关键字，用约定 (单下划线 _ 和双下划线 __)

class Person:
    # 类属性 (相当于 C# 的静态字段)
    species: str = "Homo sapiens"

    # 构造函数 (Python 用 __init__)
    def __init__(self, name: str, age: int = 0):
        # 实例属性 (相当于 C# 的字段)
        self.name = name  # self 相当于 C# 的 this
        self.age = age
        self._private_field = "private"  # 单下划线: 约定私有 (仍然可访问)
        self.__very_private = "very private"  # 双下划线: 名称重整，更难访问

    # 实例方法 (第一个参数必须是 self)
    def greet(self) -> str:
        return f"Hello, I'm {self.name}"

    # 魔术方法 (Magic Methods，相当于 C# 的运算符重载或特殊方法)
    def __str__(self) -> str:
        return f"Person({self.name}, {self.age})"

    def __repr__(self) -> str:
        return f"Person(name='{self.name}', age={self.age})"

    # 运算符重载
    def __add__(self, other):
        return Person(self.name + " & " + other.name, self.age + other.age)

    # 比较方法
    def __eq__(self, other):
        return self.name == other.name and self.age == other.age

    # 属性 (Python 的 @property 类似于 C# 的属性)
    @property
    def age_in_months(self) -> int:
        return self.age * 12

    # 静态方法 (不需要 self)
    @staticmethod
    def create_child(name: str) -> "Person":
        return Person(name, 0)

    # 类方法 (第一个参数是类本身，类似于 C# 的静态工厂方法)
    @classmethod
    def from_birth_year(cls, name: str, birth_year: int) -> "Person":
        import datetime
        age = datetime.datetime.now().year - birth_year
        return cls(name, age)


# ---------- 继承 ----------
# C#: class Student : Person
class Student(Person):
    def __init__(self, name: str, age: int, grade: int):
        super().__init__(name, age)  # 调用父类构造函数
        self.grade = grade

    def greet(self) -> str:
        # 调用父类方法
        base_greeting = super().greet()
        return f"{base_greeting}, I'm in grade {self.grade}"


# ---------- 多继承 ----------
# C# 不支持多继承，但支持多接口
# Python 支持多继承 (注意菱形继承问题)
class Teacher(Person):
    def __init__(self, name: str, age: int, subject: str):
        super().__init__(name, age)
        self.subject = subject


class TeachingAssistant(Student, Teacher):
    def __init__(self, name: str, age: int, grade: int, subject: str):
        Student.__init__(self, name, age, grade)
        Teacher.__init__(self, name, age, subject)


# ---------- 抽象类 ----------
from abc import ABC, abstractmethod

# C#: abstract class Shape { public abstract double Area { get; } }
class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return 3.14159 * self.radius ** 2

    @property
    def name(self) -> str:
        return "Circle"


# ---------- 数据类 (Python 3.7+) ----------
# C# 有 record (C# 9+)
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

    def distance_to_origin(self) -> float:
        return (self.x ** 2 + self.y ** 2) ** 0.5


p = Point(3, 4)
print(p)  # Point(x=3, y=4)
print(p.distance_to_origin())  # 5.0

# ---------- 使用示例 ----------
person = Person("Alice", 30)
print(person.greet())
print(person.age_in_months)  # 用属性方式访问

student = Student("Bob", 15, 10)
print(student.greet())

# 多态
def introduce(obj: Person):
    print(obj.greet())

introduce(person)   # Hello, I'm Alice
introduce(student) # Hello, I'm Bob, I'm in grade 10

# ========== 【注意事项】==========
# 1. Python 没有访问修饰符 (public/private/protected)，用约定管理可见性
# 2. 单下划线 _ 开头的属性表示"不应该从外部访问"
# 3. 双下划线 __ 开头的属性会被名称重整 (Name Mangling)
# 4. super() 不需要传 self
# 5. Python 支持多继承，C# 不支持
# 6. @property 让方法可以像属性一样访问
# 7. dataclass 自动生成 __init__, __repr__, __eq__ 等方法


# =============================================================================
# 12. 异常处理
# =============================================================================

# ---------- 基本语法 ----------
# C#: try { ... } catch (Exception ex) { ... } finally { ... }
# Python: try-except-else-finally，else 是可选的

try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Cannot divide by zero: {e}")
except Exception as e:
    print(f"Other error: {e}")
else:
    print("No exception occurred")  # 没有异常时执行
finally:
    print("Always executes")  # 无论是否有异常都执行

# ---------- 常见异常类型 ----------
# C# 有很多具体异常类型: NullReferenceException, ArgumentException, InvalidOperationException...
# Python 常见异常:
#   Exception - 基类
#   TypeError - 类型错误
#   ValueError - 值错误
#   KeyError - 字典键不存在
#   IndexError - 索引越界
#   AttributeError - 属性不存在
#   ImportError / ModuleNotFoundError - 导入错误
#   FileNotFoundError - 文件不存在
#   ZeroDivisionError - 除零错误
#   StopIteration - 迭代器耗尽

# ---------- 抛出异常 ----------
# C#: throw new Exception("message");
# Python: raise Exception("message")
def validate_age(age: int):
    if age < 0:
        raise ValueError("Age cannot be negative")
    if age > 150:
        raise ValueError("Age is unrealistic")


# ---------- 自定义异常 ----------
class MyException(Exception):
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


# ---------- 异常链 ----------
# Python 3 可以在 raise 时保留原始异常
try:
    raise ValueError("Original error")
except ValueError as e:
    raise TypeError("New error") from e

# ========== 【注意事项】==========
# 1. Python 的 else 和 finally 是可选的
# 2. 可以一次捕获多种异常: except (TypeError, ValueError)
# 3. 异常是类，继承自 BaseException
# 4. 不要用异常做流程控制，影响性能


# =============================================================================
# 13. 文件操作
# =============================================================================

# ---------- 读取文件 ----------
# C#: File.ReadAllText(path), File.ReadLines(path), StreamReader

# 整个文件读取 (小文件)
with open("example.txt", "r", encoding="utf-8") as f:
    content: str = f.read()

# 按行读取
with open("example.txt", "r", encoding="utf-8") as f:
    lines: list = f.readlines()  # 返回列表，每行一个元素

# 迭代器方式读取 (推荐，大文件也适用)
with open("example.txt", "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())

# ---------- 写入文件 ----------
# C#: File.WriteAllText(path, content), StreamWriter
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, World!\n")
    f.write("Second line")

# 追加模式
with open("output.txt", "a", encoding="utf-8") as f:
    f.write("\nAppended line")

# ---------- JSON 文件 ----------
import json

# 写入 JSON
data: dict = {"name": "Alice", "age": 30, "scores": [90, 85, 88]}
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# 读取 JSON
with open("data.json", "r", encoding="utf-8") as f:
    loaded_data = json.load(f)

# ========== 【注意事项】==========
# 1. with 语句自动关闭文件，类似于 C# 的 using
# 2. encoding="utf-8" 很重要，不指定可能在不同系统出问题
# 3. 读取二进制文件用 "rb"，写入用 "wb"
# 4. 文件操作后不要忘记 close()，用 with 更安全


# =============================================================================
# 14. 模块和包
# =============================================================================

# ---------- 导入 ----------
# C#: using MyNamespace;
# Python:
import math  # 导入整个模块
from math import sqrt, pi  # 导入特定函数/变量
from math import sqrt as s  # 起别名
from package import module  # 从包导入模块
from . import sibling  # 相对导入 (包内使用)
from .. import parent  # 向上相对导入

# ---------- 模块搜索路径 ----------
# Python 从以下位置搜索模块:
# 1. 当前目录
# 2. PYTHONPATH 环境变量
# 3. Python 安装目录
import sys
print(sys.path)

# ---------- 包 ----------
# 目录包含 __init__.py 就会被当作包
# __init__.py 可以为空，也可以包含包的初始化代码

# ---------- __name__ ----------
# C# 有 Main 方法入口
# Python:
# __name__ == "__main__" 时表示直接运行此文件
# 被导入时 __name__ 是模块名

if __name__ == "__main__":
    print("Running directly")
else:
    print(f"Imported as module: {__name__}")

# ========== 【注意事项】==========
# 1. 避免循环导入 (A 导入 B，B 导入 A)
# 2. __all__ 列表定义 from module import * 时导出的内容
# 3. 模块只加载一次，多次 import 不会重复执行


# =============================================================================
# 15. 迭代器和生成器
# =============================================================================

# ---------- 迭代器 ----------
# C#: IEnumerable<T>, IEnumerator<T>
# Python: 实现 __iter__ 和 __next__ 的对象

class Counter:
    def __init__(self, max_val: int):
        self.max_val = max_val
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current >= self.max_val:
            raise StopIteration
        self.current += 1
        return self.current - 1


for i in Counter(5):
    print(i)

# ---------- 生成器 ----------
# Python 特有，比迭代器更简洁
# C# 有 yield return，概念类似

def countdown(n: int):
    while n > 0:
        yield n
        n -= 1

for num in countdown(5):
    print(num)

# 生成器表达式 (类似列表推导式，但惰性求值)
# 列表: [x**2 for x in range(1000000)]  # 创建大列表
# 生成器: (x**2 for x in range(1000000))  # 惰性，不占内存

gen = (x ** 2 for x in range(1000000))
print(next(gen))  # 0
print(next(gen))  # 1

# ========== 【注意事项】==========
# 1. 生成器是迭代器的一种，只能遍历一次
# 2. 生成器惰性求值，适合处理大数据
# 3. next() 在耗尽后抛出 StopIteration


# =============================================================================
# 16. 上下文管理器 (Context Manager)
# =============================================================================

# ---------- with 语句 ----------
# C# 有 using，Python 有 with，概念相同

# 使用 with 打开文件 (自动关闭)
with open("test.txt", "w") as f:
    f.write("Hello")

# ---------- 自定义上下文管理器 ----------
# 方式1: 实现 __enter__ 和 __exit__
class MyContext:
    def __enter__(self):
        print("Entering context")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exiting context")
        return False  # 返回 True 抑制异常

with MyContext() as ctx:
    print("Inside context")


# 方式2: 使用 contextmanager 装饰器
from contextlib import contextmanager

@contextmanager
def my_context():
    print("Entering")
    try:
        yield "resource"
    finally:
        print("Exiting")

with my_context() as res:
    print(f"Using {res}")

# ========== 【注意事项】==========
# 1. __exit__ 的返回值控制是否抑制异常
# 2. contextlib 模块提供了很多有用的上下文管理器工具


# =============================================================================
# 17. 类型注解 (Type Hints)
# =============================================================================

# Python 3.5+ 支持类型注解，不强制但有助于 IDE 和代码可读性
# C# 有静态类型检查，Python 的类型注解更像是文档

# ---------- 基本注解 ----------
name: str = "Alice"
age: int = 30
scores: list = [90, 85, 88]
scores: list[int] = [90, 85, 88]  # Python 3.9+
person: dict = {"name": "Alice", "age": 30}

# ---------- 函数注解 ----------
def greet(name: str, times: int = 1) -> str:
    return (f"Hello, {name}! " * times).strip()


# ---------- 泛型 ----------
from typing import List, Dict, Tuple, Optional, Union, Callable

# Optional[X] 相当于 Union[X, None] (类似 C# 的 X?)
# Callable[[参数类型], 返回类型]
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# ---------- 类型别名 ----------
# 类似 C# 的 using
Vector = List[float]
Matrix = List[List[float]]

# ========== 【注意事项】==========
# 1. 类型注解不影响运行时，只是提示
# 2. 可以用 mypy 进行静态类型检查
# 3. Python 3.9+ 原生支持 list[int] 语法，之前需用 List[int]


# =============================================================================
# 18. 常用内置函数
# =============================================================================

# ---------- 数学相关 ----------
abs(-5)           # 5，绝对值
round(3.14159, 2) # 3.14，四舍五入
min(1, 2, 3)      # 1
max(1, 2, 3)      # 3
sum([1, 2, 3, 4]) # 10
pow(2, 3)         # 8，幂运算

# ---------- 类型相关 ----------
type(123)         # <class 'int'>
isinstance(123, int)  # True，检查类型
isinstance("123", str)  # True

# ---------- 转换相关 ----------
int("123")        # 123
float("3.14")     # 3.14
str(123)          # "123"
list("abc")       # ['a', 'b', 'c']
set([1, 2, 2, 3])  # {1, 2, 3}
tuple([1, 2, 3])  # (1, 2, 3)
dict([("a", 1), ("b", 2)])  # {'a': 1, 'b': 2}

# ---------- 可迭代对象相关 ----------
len([1, 2, 3])    # 3
list(range(10))   # [0,1,2,3,4,5,6,7,8,9]
enumerate(["a", "b", "c"])  # [(0,'a'), (1,'b'), (2,'c')]
zip([1, 2], ["a", "b"])  # [(1,'a'), (2,'b')]
reversed([1, 2, 3])  # [3, 2, 1]
sorted([3, 1, 2])  # [1, 2, 3]
all([True, True, False])  # False，是否全部为 True
any([True, False, False])  # True，是否任一为 True

# ---------- 字符串相关 ----------
chr(65)           # 'A'，数字转字符
ord('A')           # 65，字符转数字
hex(255)           # '0xff'
bin(8)             # '0b1000'
oct(8)             # '0o10'

# ---------- 对象相关 ----------
id(obj)            # 返回对象唯一标识 (内存地址)
hash(obj)          # 返回哈希值 (用于字典键)
dir(obj)           # 返回对象的属性和方法列表
help(func)         # 显示帮助信息
vars(obj)          # 返回对象的 __dict__


# =============================================================================
# 19. Python 与 C# 关键语法差异总结
# =============================================================================

# | 特性           | C#                           | Python                          |
# |----------------|------------------------------|---------------------------------|
# | 类型声明        | 必须: int x = 5;             | 可选: x = 5 或 x: int = 5       |
# | 代码块         | { }                         | 缩进 (4空格)                    |
# | 语句结束       | 分号 ;                       | 换行                            |
# | 字符串格式化    | $"Hello {name}"             | f"Hello {name}"                 |
# | 可见性         | public/private/protected    | 约定 (_protected, __private)    |
# | 继承           | class A : B, I1, I2         | class A(B, I1, I2)             |
# | 接口           | interface IName { }         | class Name(ABC): (抽象类)       |
# | 枚举           | enum Type { A, B }          | class Type: (或 Enum类)         |
# | 泛型           | List<T>, Dictionary<K,V>    | list[T], dict[K,V] (3.9+)       |
# | Lambda         | (a, b) => a + b             | lambda a, b: a + b             |
# | 空值           | null                        | None                            |
# | 布尔值         | true/false                  | True/False                     |
# | 循环变量增量   | i++                         | i += 1                          |
# | foreach       | foreach (var item in list)  | for item in list:              |
# | 异常           | try { } catch { }           | try: except:                   |
# | 参数默认值     | void F(int x = 5)           | def F(x=5):                    |
# | 多返回值       | out, Tuple                  | return a, b (返回 tuple)       |
# | 属性           | public int Age { get; set;} | @property                      |
# | 静态成员       | static void F()             | @staticmethod                   |
# | 模块导入       | using Namespace;            | import module / from x import y |
# | 抽象类         | abstract class               | class(ABC) + @abstractmethod    |
# | 运算符重载     | public static operator+      | def __add__(self, other)       |
# | 集合字面量     | var list = new[] {1,2,3}    | [1, 2, 3]                       |
# | 字典字面量     | var dict = new(){...}       | {key: value}                   |


# =============================================================================
# 20. 实用技巧与常见错误
# =============================================================================

# ---------- 浅拷贝 vs 深拷贝 ----------
import copy

original = [[1, 2], [3, 4]]

# 浅拷贝: 只拷贝一层
shallow = original.copy()        # 列表的 copy 方法
shallow = list(original)       # 构造方法
shallow = original[:]           # 切片
shallow = copy.copy(original)   # copy 模块

# 深拷贝: 递归拷贝所有层级
deep = copy.deepcopy(original)

# ---------- == vs is ----------
# == 比较值是否相等
# is 比较引用是否相同 (相当于 C# 的 ReferenceEquals)
a = [1, 2]
b = [1, 2]
c = a

print(a == b)  # True，值相等
print(a is b)  # False，不同对象
print(a is c)  # True，同一个对象

# ---------- 可变默认参数问题 ----------
# 错误示例:
def add_item(item, items=[]):  # 危险!
    items.append(item)
    return items

# 正确做法:
def add_item_fixed(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# ---------- 字符串不可变 ----------
# C# string 是不可变的，Python str 也是不可变的
s = "hello"
# s[0] = 'H'  # TypeError: 'str' object does not support item assignment
s = "H" + s[1:]  # 创建新字符串

# ---------- 链式赋值 ----------
# Python 支持链式比较
x = 5
print(1 < x < 10)  # True，等价于 1 < x and x < 10

# ---------- 链式调用 ----------
# Python 不支持 C# 那种连续点链式调用
# 但可以返回 self 实现链式方法
class Builder:
    def __init__(self):
        self.value = ""

    def add(self, s):
        self.value += s
        return self

result = Builder().add("Hello").add(" World").value

# ---------- pass 语句 ----------
# C# 的空方法必须写 {}
# Python 用 pass 占位
def empty_method():
    pass

# ---------- 删除列表元素 ----------
# C#: list.RemoveAll(x => x > 2) 或 list.RemoveAt(i)
# Python:
nums = [1, 2, 3, 4, 5]
nums = [x for x in nums if x <= 3]  # 列表推导式
# 或
del nums[0]  # 删除索引0
nums.pop()   # 删除最后一个


# =============================================================================
# 21. Pythonic 风格建议
# =============================================================================

# Python 社区推崇的写法，叫 "Pythonic"

# 1. 交换变量
a, b = b, a  # 而不是用临时变量

# 2. 列表推导式
squares = [x**2 for x in range(10)]

# 3. 使用 enumerate
for i, item in enumerate(items):
    print(f"{i}: {item}")

# 4. 使用 zip 同时遍历多个列表
for name, age in zip(names, ages):
    print(f"{name} is {age}")

# 5. 使用上下文管理器
with open("file.txt") as f:
    content = f.read()

# 6. 使用 with 交换 (walrus operator Python 3.8+)
if (n := len(data)) > 10:
    print(f"List has {n} elements")

# 7. 使用 dataclass 简化类定义
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

# 8. 使用 pdb/IPDB 调试
# import pdb; pdb.set_trace()

# 9. 使用 type hints
def greet(name: str) -> str:
    return f"Hello, {name}"

# 10. 使用装饰器复用代码
def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Took {time.time() - start:.2f}s")
        return result
    return wrapper


# =============================================================================
# 22. 快速查询表
# =============================================================================

# C#                      Python
# -----                   ------
# ;                        (换行)
# { }                      缩进
# var x = 5               x = 5
# int.Parse()             int()
# ToString()              str()
# Length                  len()
# .Contains()             in
# .IndexOf()              .find() / in
# .Trim()                 .strip()
# String.Format()         f-string / .format()
# foreach (var i in l)    for i in l:
# for (int i=0;...)      for i in range(n):
# Array.Resize()         (不需要)
# List<T>                list
# Dictionary<K,V>        dict
# HashSet<T>             set
# LINQ                   内置函数 / 列表推导式
# async/await            async/await
# lock                   threading.Lock (需导入)
# using                  with
# throw                  raise
# try-catch              try-except
# public/private         (无，用约定)
# namespace              module
# class                  class
# interface              ABC / 协议
# static                 @staticmethod
# const                  (无) - 用 ALL_CAPS
# readonly               (无) - 用 property 或 __setattr__
# typeof                 type()
# as (cast)              as (异常处理)
# is (cast)              isinstance()


# =============================================================================
# 结束
# =============================================================================
