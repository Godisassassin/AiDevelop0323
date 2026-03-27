nums=[1,5,9,84,55]
strs:list[str]=["hello","world","python"]

nums.extend([7,8])

print(nums)
print(strs)


squares: list = [x ** 2 for x in range(10)]
matrix: list = [[i * j for j in range(3)] for i in range(3)]  # 3x3 矩阵

print(squares)
print(matrix)

newlist=[1,2,3]
num1,num2,num3=newlist
print(num1,num2,num3)
first, *rest = newlist
print(first)
print(rest)

