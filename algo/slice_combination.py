# coding=utf-8
"""
author = neo
"""

import math
import time


def slice_combination(array=[], need_print=False):
    """
    算法思路：利用进制和位数进行巧妙遍历
        数组的行数作为一个整数的位数
        列数作为进制数
        比如10行3列的数组，则组合结果有3的10次方种

        此时遍历0到3^10，根据数值取其对应的位数和第几位的数值即可
        比如数值为12，用三进制表示为110，则对应的数组为【第3行的第1个元素，第二行的第1个元素，第1行的第0个元素】

    :param array: []， 二维数组
    :param need_print: bool, 是否需要输出组合结果
    :return:
    """
    # 因为组合结果可能很大，此处结果不直接返回，改为直接print输出
    if not array or not isinstance(array[0], list):
        return

    row_num = len(array)   # 可以作为位数
    col_num = len(array[0])  # 可以作为进制数
    radix_digit = int(math.pow(col_num, row_num))

    result_num = 0
    for digit in range(radix_digit):
        temp_combination = []
        for i in range(row_num):  # 遍历位数
            temp = digit % col_num   # 获取取第几个数
            digit = int(digit / col_num)
            temp_combination.append(array[i][temp])
        if need_print:
            print(temp_combination)     # 如果要输出结果，打开慈航注释即可
        result_num += 1

    return result_num


if __name__ == "__main__":
    row_num = 10
    col_num = 3
    a = []
    for i in range(row_num):
        a.append([])
        for j in range(col_num):
            a[i].append(i + 0.1*j % 1)


    s1 = time.time()
    result_num = slice_combination(a, need_print=False)
    s2 = time.time()
    print("{}行{}列的组合数总共有{}种，耗时{}s".format(row_num, col_num, result_num, s2-s1))


    row_num = 3
    col_num = 3
    a = []
    for i in range(row_num):
        a.append([])
        for j in range(col_num):
            a[i].append(i + 0.1 * j % 1)

    s1 = time.time()
    result_num = slice_combination(a, need_print=True)
    s2 = time.time()
    print("{}行{}列的组合数总共有{}种，耗时{}s".format(row_num, col_num, result_num, s2 - s1))


    



