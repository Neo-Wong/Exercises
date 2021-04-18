#! -*- coding: utf-8 -*-
# __file__  : test516
# __author__: NeoWong
# __date__  : 2021-04-16 10:05


def test(target_list, target):
    if not target_list:
        return False
    size = len(target_list)
    l, r = 0, size - 1
    while l < r:
        mid = (l + r) // 2
        if target_list[mid] == target:
            return True
        elif target_list[mid] < target:
            l = mid + 1
        else:
            r = mid

    return False


def bubble_sort(target_list):
    size = len(target_list)
    for i in range(size - 1):
        for j in range(size - i - 1):
            if target_list[j] > target_list[j + 1]:
                target_list[j], target_list[j + 1] = target_list[j + 1], target_list[j]

    return target_list


def count_A(filename):
    with open(filename, 'r')as f:
        file_data = f.read()
    count = 0
    for i in file_data:
        if ord("A") <= ord(i) <= ord("Z"):
            count += 1

    return count


if __name__ == '__main__':
    target_list = [13, 12, 11, 18, 19, 17, 15, 16, 10, ]
    target = 9
    filename = "test.txt"
    filename.isupper()
    res = test(target_list, target)
    res = bubble_sort(target_list)
    res = count_A(filename)
    print(res)
