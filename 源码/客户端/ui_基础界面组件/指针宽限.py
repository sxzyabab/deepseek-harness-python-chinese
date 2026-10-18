from ..模块.客户端.通告 import 取握手窗口

__all__=['指针宽限毫秒','指针宽限']#仅中文公开名

指针宽限毫秒=200#宽限

class 指针宽限:#可取消延迟关闭
    'arm 调度；cancel 中止；卸载时丢弃'

    def __init__(自身,关闭):#构造
        '记下关闭回调'
        自身.关闭=关闭#关闭
        自身.定时=None#句柄

    def 武装(自身):#调度关闭
        '替换未触发的一次'
        自身.取消()#先取消
        def 到期():
            '宽限到点，执行最新关闭'
            自身.定时=None#清句柄
            if 自身.关闭 is not None:
                自身.关闭()#关
        自身.定时=取握手窗口().setTimeout(到期,指针宽限毫秒)#真正计时

    def 取消(自身):#中止
        '清待关闭'
        if 自身.定时 is not None:
            取握手窗口().clearTimeout(自身.定时)#卸定时
            自身.定时=None#清
    def 触发(自身):#宽限到期
        '执行最新关闭'
        自身.定时=None
        if 自身.关闭 is not None:
            自身.关闭()#关

    def 句柄(自身):#PointerGrace 形
        'arm/cancel'
        return {'arm':自身.武装,'cancel':自身.取消}#句柄
