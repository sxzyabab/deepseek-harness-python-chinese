from ...存储 import 创建快照存储#快照仓

__all__=['创建轨迹时长存储']

def 创建轨迹时长存储():
    '浏览器范围内共享的实测时长偏好'
    return 创建快照存储(False,{'persist':{'name':'dsh.trajectory.duration'}})
