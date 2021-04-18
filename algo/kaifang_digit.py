# coding=utf-8
"""
author = neo
"""

import math


def kai_fang_digit(digit, bit_num):
    """
    求保留指定小数位数的数的开方值, 时间复杂度 O(N), 空间复杂度 O(1)
    :param digit:  number
    :param bit_num: int
    :return: number
    """
    if 0 > digit:
        print("负数没有开方值")
        return None

    # 先确定整数部分
    int_part = 0
    for i in range(math.ceil(digit)+1):
        if digit == i*i:
            return i
        if digit < i*i:
            int_part = i-1
            break

    result = int_part

    # 定位小数部分
    for i in range(1, int(bit_num)+1):
        temp = math.pow(10, -i)
        for j in range(1, 11):
            temp2 = result + temp*j
            # print(temp2)
            if digit == temp2 * temp2:
                return temp2
            if digit < temp2 * temp2:
                result += temp * (j-1)
                break
    return result


if __name__ == "__main__":
    print(kai_fang_digit(2, 3))
    print(kai_fang_digit(2, 10))
    print(kai_fang_digit(287, 3))
    print(kai_fang_digit(-10, 10))
    print(kai_fang_digit(1.2, 3))
