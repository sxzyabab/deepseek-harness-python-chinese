'展开 JSON 字符串时的默认折行偏好'
from ...存储 import 创建快照存储

__all__=['创建轨迹字符串换行存储']

def 创建轨迹字符串换行存储():
    '带 getSnapshot 和 subscribe 的快照存储'
    return 创建快照存储(False,{'persist':{'name':'dsh.trajectory.jsonStringWrapping'}})
