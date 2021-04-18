#! -*- coding: utf-8 -*-
# __file__  : test516
# __author__: NeoWong
# __date__  : 2021-04-16 10:05


def is_square(points):
    size = len(points)
    points_set = set(map(tuple, points))
    # print(points_set)

    res = float("inf")
    for i in range(size):
        [x1, y1] = points[i]
        for j in range(i+1, size):
            if j == i:
                continue
            [x2, y2] = points[j]
            for k in range(j+1, size):
                if k == j:
                    continue
                [x3, y3] = points[k]
                x4 = x2 + x3 - x1
                y4 = y2 + y3 - y1
                if (x4, y4) in points_set:
                    v21 = (x2 - x1, y2 - y1)
                    v31 = (x3 - x1, y3 - y1)
                    if v21[0] * v31[0] + v21[1] * v31[1] == 0:
                        square_area = (v21[0] ** 2 + v21[1] ** 2) ** 0.5 * (v31[0] ** 2 + v31[1] ** 2) ** 0.5
                        if square_area < res:
                            res = square_area

    return res if res != float("inf") else 0



if __name__ == '__main__':
    test = [
        [[1,2], [2,1],[1,0],[0,1]],
        [[0,1], [2,1],[1,1],[1,0],[2,0]],
        [[0,3], [1,2],[3,1],[1,3], [2,1]],
        [[3,1],[1,1],[0,1],[2,1],[3,3],[3,2],[0,2],[2,3]],
    ]
    for i in test:
        res = is_square(i)
        print(res)

