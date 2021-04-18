# coding=utf-8
"""
author = neo
"""

# import a
# x=1
# def g():
#     print(a.f())


import time
start_time = time.time()

n = 1001
# 注意是三重循环
flag = false
for a in range(0, n):    # (0, n)
    if flag:
        break
    for b in range(0, n): # (0,n)
        for c in range(0, n): (0, n)
            if a**2 + b**2 == c**2 and a+b+c == 1000:
                print("a, b, c: %d, %d, %d" % (a, b, c))

end_time = time.time()
print("elapsed: %f" % (end_time - start_time))
print("complete!")
