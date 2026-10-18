from ...存储 import 创建快照存储#快照仓

__all__=['创建轨迹字符串换行存储']

def 创建轨迹字符串换行存储():
    '浏览器范围内展开 JSON 字符串时的默认折行偏好'
    return 创建快照存储(False,{'persist':{'name':'dsh.trajectory.jsonStringWrapping'}})
