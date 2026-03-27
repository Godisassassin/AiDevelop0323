name="Alice"
print(f"hello,{name}!")
length: int = len(name)
print(f"the length of name is {length}.")
print(f"{name.find("iceb")}")
array=["a","b","c"]
print(f"{"-".join(array)}")
text="  这是 一段 测试 文 本   !  "
print(f"{len(text.strip())}")
print(f"{len(text.lstrip())}")
print(f"{len(text.rstrip())}")