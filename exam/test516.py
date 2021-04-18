#! -*- coding: utf-8 -*-
# __file__  : test516
# __author__: NeoWong
# __date__  : 2021-04-16 10:05


def is_close(word1, word2):
    size1, size2 = len(word1), len(word2)
    if size1 != size2:
        return False
    # 计数
    str_count1 = [0] * 26
    str_count2 = [0] * 26
    for s1 in word1:
        str_count1[ord(s1) - ord("a")] += 1
    for s2 in word2:
        str_count2[ord(s2) - ord("a")] += 1

    # 判断是否有不一样的字符
    for i in range(26):
        if (str_count1[i] == 0) ^ (str_count2[i] == 0):
            return False

    # 排序
    str_count1.sort()
    str_count2.sort()

    return str_count1 == str_count2


if __name__ == '__main__':
    test = [
        ["abc", "bca"],
        ["a", "aa"],
        ["cabbba", "abbccc"],
        ["cabbba", "aabbss"],
    ]
    for i in test:
        res = is_close(i[0], i[1])
        print(res)

