'浏览器本地的麦克风偏好，设置预览和听写共用'
from ....客户端.存储 import 创建快照存储#可持久化的快照

__all__=['创建麦克风设备存储']#导出的存储工厂


def 创建麦克风设备存储():
    '恢复浏览器偏好。空 id 跟随系统输入，标签只存浏览器给出的名字'
    存储=创建快照存储({'id':'','label':''},{'persist':{'name':'dsh.voice-input.microphone'}})#按这个名字持久化
    已存=存储.getSnapshot()#读回来的值
    标识可用=isinstance(已存,dict) and 'id' in 已存 and isinstance(已存.get('id'),str)#id 必须是字符串
    标签可用=isinstance(已存,dict) and 'label' in 已存 and isinstance(已存.get('label'),str)#label 必须是字符串
    if 已存 is None or 标识可用 is False or 标签可用 is False:#坏数据退回系统默认
        存储.set({'id':'','label':''})#清空
    return 存储#共享这一份
