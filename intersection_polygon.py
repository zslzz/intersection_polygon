class Point(object):
    """
    点 默认为（-1，-1）
    """

    def __init__(self, x=-1, y=-1):
        self.x = x
        self.y = y


class Line(object):
    """
    由两点确定的直线
    a,b,c
    """

    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2


class SdPolygon(object):
    """
    不规范的标注的点 生成的符合规范的 多边形。
    点所形成的线段可能相交。

    算法流程：  假设存在点A，B，C，D，E，F，G，H，围成内交多边形（intersection-polygon）其中EF交CD于M。
    则计算流程为：
        按照顺序依次遍历各个点，将尚未围成多边形的点加入current_points，则current_points=[ABCDE],当加入EF时，判断可知EF于CD交于M，
        将MED所围成的多边形剪下，添加到sd_polygons中。则current_points=[ABCMF],sd_polygon.append(MED)
        尚未围成 多边形的点，继续遍历，直到遍历完所有的点，则最后围成多边形的点所生成的pylogon
    points:[(x1,y1),(x2,y2)] 所有点
    current_points:[(x1,y1)] 当前尚未围成多边形的点
    sd_polygons: 多个多边形的数组。
    """

    def __init__(self, points=None):
        points = self.parafloat(points)
        self.points = points
        self.current_points = []
        self.sd_polygons = []
        self.gene_polygon()
        from shapely.ops import cascaded_union
        self.sd_polygon = cascaded_union(self.sd_polygons)

    def parafloat(self, points):
        """
        为保证准确，将所有的浮点数转化为整数
        :return:
        """
        para_point = [(int(x), int(y)) for x, y in points]
        return para_point

    def gene_polygon(self):
        for point in self.points:
            self.add_point_to_current(point)  # 依次将点加入数组
        self.add_point_to_current(self.points[0])  # 最后将第一个数加入
        p0 = Polygon(self.current_points)
        self.sd_polygons.append(p0)

    def add_point_to_current(self, point):
        """
        将该点加入到current_points 中，倒序遍历current_points中的点，如果能围成多边形，则将所围成的点弹出
        :param point:
        :return:
        """
        if len(self.current_points) <= 2:
            self.current_points.append(point)
            return
        cross_point_dict = {}  # 记录线段与其他点的相交点，{0:P1,6:P2}
        l0 = Line(Point(point[0], point[1]), Point(self.current_points[-1][0], self.current_points[-1][1]))
        for i in range(0, len(self.current_points) - 1):
            line = Line(Point(self.current_points[i][0], self.current_points[i][1]),
                        Point(self.current_points[i + 1][0], self.current_points[i + 1][1]))
            cross_point = self.get_cross_point(l0, line)  # 获取相交点
            if self.is_in_two_segment(cross_point, l0, line):  # 如果相交点在两个线段上
                cross_point_dict.update({i: cross_point})
        flag_dict = {}  # 保存剪下点的信息
        cross_points_list = sorted(cross_point_dict.items(), key=lambda item: item[0], reverse=True)  # [(3,P),(1,P)]
        for cross_point_info in cross_points_list:
            cross_i, cross_point = cross_point_info[0], cross_point_info[1]
            if flag_dict:  # 对应需要剪下多个多边形的情形，
                points = self.current_points[cross_i + 1:flag_dict['index'] + 1]
                points.append((flag_dict['point'].x, flag_dict['point'].y))
                points.append((cross_point.x, cross_point.y))
                p = Polygon(points)
                self.sd_polygons.append(p)
            else:
                points = self.current_points[cross_i + 1:]
                points.append((cross_point.x, cross_point.y))
                if len(points)<=2:
                    continue
                p = Polygon(points)
                self.sd_polygons.append(p)  # 将生成的polygon保存
            flag_dict.update(index=cross_i, point=cross_point)
        if flag_dict:
            point_list = self.current_points[:flag_dict['index'] + 1]  # 还未围成多边形的数组
            point_list.append((flag_dict['point'].x, flag_dict['point'].y))  # 加上交点
            self.current_points = point_list
        self.current_points.append(point)

    def is_in_segment(self, point, point1, point2):
        """
        交点是否在线段上
        :param point:(x,y)
        :param point1:[(x1,y1),(x2,y2)]
        :param point2:
        :return:
        """
        if point1.x > point2.x:
            minx = point2.x
            maxx = point1.x
        else:
            minx = point1.x
            maxx = point2.x
        if point1.y > point2.y:
            miny = point2.y
            maxy = point1.y
        else:
            miny = point1.y
            maxy = point2.y
        if minx <= point.x <= maxx and miny <= point.y <= maxy:
            return True
        return False

    def is_in_two_segment(self, point, l1, l2):
        """
        点 是否在两段 线段中间
        :param point:
        :param l1:
        :param l2:
        :return:
        """

        def is_same_point(p1, p2):
            """
            判断点是否相同
            :param p1:
            :param p2:
            :return:
            """
            if abs(p1.x - p2.x) < 0.1 and abs(p1.y - p2.y) < 0.1:
                return True
            return False

        if self.is_in_segment(point, l1.p1, l1.p2) and self.is_in_segment(point, l2.p1, l2.p2):
            # if (is_same_point(point, l1.p1) or is_same_point(point, l1.p2)) and (
            #             is_same_point(point, l2.p1) or is_same_point(point, l2.p2)):
            # 判断是否在两条线段的端点上
            # return False
            return True
        return False

    def get_line_para(self, line):
        """
        规整line
        :param line:
        :return:
        """
        line.a = line.p1.y - line.p2.y
        line.b = line.p2.x - line.p1.x
        line.c = line.p1.x * line.p2.y - line.p2.x * line.p1.y

    def get_cross_point(self, l1, l2):
        """
        得到交点
        :param l1: 直线Line
        :param l2:
        :return: 交点坐标Point
        """
        self.get_line_para(l1)
        self.get_line_para(l2)
        d = l1.a * l2.b - l2.a * l1.b
        p = Point()
        if d == 0:
            return p
        p.x = (l1.b * l2.c - l2.b * l1.c) / d
        p.y = (l1.c * l2.a - l2.c * l1.a) / d
        return p


# 测试方法，待完善后删除
if __name__ == '__main__':
    def test_cross():
        p = SdPolygon().get_cross_point(Line(Point(1, 0), Point(0, 1)), Line(Point(1, 1), Point(1, 2)))
        flag = SdPolygon().is_in_segment(p, Point(1, 0), Point(0, 1)) and SdPolygon.is_in_segment(p, Point(1, 1),
                                                                                                  Point(1, 2))
        print(flag)
        print(p)


    def test_pylogon():
        task_info = '{"point": [{"value": "1", "color": "red", "points": [{"x": 1883.33, "y": 1139.58}, {"x": 1866.67, "y": 1210.42}, {"x": 1906.25, "y": 1212.5}, {"x": 1970.83, "y": 1218.75}, {"x": 2187.5, "y": 1222.92}, {"x": 2212.5, "y": 1231.25}, {"x": 2247.92, "y": 1231.25}, {"x": 2262.5, "y": 1204.17}, {"x": 2302.08, "y": 1195.83}, {"x": 2302.08, "y": 1143.75}, {"x": 2256.25, "y": 1118.75}, {"x": 2168.75, "y": 1093.75}, {"x": 2052.08, "y": 1097.92}, {"x": 1993.75, "y": 1122.92}]}, {"value": "1", "color": "red", "points": [{"x": 2360.89, "y": 1120.71}, {"x": 2377.96, "y": 1171.91}, {"x": 2440.53, "y": 1183.29}, {"x": 2514.49, "y": 1183.29}, {"x": 2560, "y": 1183.29}, {"x": 2582.76, "y": 1183.29}, {"x": 2605.51, "y": 1177.6}, {"x": 2622.58, "y": 1177.6}, {"x": 2639.64, "y": 1115.02}, {"x": 2594.13, "y": 1075.2}, {"x": 2497.42, "y": 1058.13}, {"x": 2400.71, "y": 1080.89}]}, {"value": "1", "color": "red", "points": [{"x": 1012.62, "y": 1046.76}, {"x": 1012.62, "y": 1154.84}, {"x": 1058.13, "y": 1194.67}, {"x": 1137.78, "y": 1194.67}, {"x": 1206.04, "y": 1194.67}, {"x": 1166.22, "y": 1029.69}, {"x": 1103.64, "y": 1029.69}, {"x": 1041.07, "y": 1029.69}, {"x": 1018.31, "y": 1029.69}]}]}'
        task_info = '{"point": [{"value": "1", "color": "red", "points": [{"x": 1883.33, "y": 1139.58}, {"x": 1866.67, "y": 1210.42}, {"x": 1906.25, "y": 1212.5}, {"x": 1970.83, "y": 1218.75}, {"x": 2187.5, "y": 1222.92}, {"x": 2212.5, "y": 1231.25}, {"x": 2247.92, "y": 1231.25}, {"x": 2262.5, "y": 1204.17}, {"x": 2302.08, "y": 1195.83}, {"x": 2302.08, "y": 1143.75}, {"x": 2256.25, "y": 1118.75}, {"x": 2168.75, "y": 1093.75}, {"x": 2052.08, "y": 1097.92}, {"x": 1993.75, "y": 1122.92}]}, {"value": "1", "color": "red", "points": [{"x": 2360.89, "y": 1120.71}, {"x": 2377.96, "y": 1171.91}, {"x": 2440.53, "y": 1183.29}, {"x": 2514.49, "y": 1183.29}, {"x": 2560, "y": 1183.29}, {"x": 2582.76, "y": 1183.29}, {"x": 2605.51, "y": 1177.6}, {"x": 2622.58, "y": 1177.6}, {"x": 2639.64, "y": 1115.02}, {"x": 2594.13, "y": 1075.2}, {"x": 2497.42, "y": 1058.13}, {"x": 2400.71, "y": 1080.89}]}]}'
        task_info = '[{"value": "red", "color": "red", "points": [{"x": 631.34, "y": 285.04}, {"x": 977.65, "y": 356.96}, {"x": 948.34, "y": 564.74}, {"x": 735.23, "y": 599.38}]},{"value": "red", "color": "red", "points": [{"x": 631.34, "y": 285.04}, {"x": 977.65, "y": 356.96}, {"x": 948.34, "y": 564.74}, {"x": 735.23, "y": 599.38}]}]'
        import json
        info = json.loads(task_info)
        get_points_in_keypoints(info)
        points = [(0, 0), (0, 1), (1, 0), (1, 1)]
        pylogon = Polygon(points)
        print(pylogon.area)


    def test_lambda():
        dicta = {1: 'asd', 5: 'ddd', 2: 'www', 0: 'pppp'}
        cross_points_list = sorted(dicta.items(), key=lambda item: item[0])
        print(cross_points_list)


    def test_truple():
        a = (2, 3)
        print(a[0])


    def test_dict():
        i = 3
        dicta = {}
        p = Point(1, 2)
        dicta.update({i: p})
        i += 1
        dicta.update({i: p})
        print(dicta)


    def test_sdpolygon():
        points = [(1, 1), (1, 5), (4, 5), (4, 3)]  # 正常多边形测试
        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (3, 5), (3, 1)]  # 内交一个点 的多边形
        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (3, 5), (3, 3), (3, 1)]  # 内交一个点 的多边形 area =8
        # points = [(1, 1), (1, 3), (5, 3), (5, 5), (1, 5), (1, 7), (3, 7), (3, 1)]  # 内交两个点的多边形
        sdpolygon = SdPolygon(points).sd_polygon
        print(sdpolygon.area)


    def test_inter():
        points = [(728.05, 428.57), (1287.57, 428.57), (1042.33, 835.71),
                  (1072.33, 875.71), (1272.33, 1075.71)]
        # points = [(0, 0), (1, 0), (1, 1), (2, 1)]
        sd = SdPolygon(points).sd_polygon
        print(sd.area)


    test_inter()
