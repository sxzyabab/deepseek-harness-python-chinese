'一次由界面发起的授权，单独持有预开的浏览器标签'
from ...模块.客户端.通告 import 取握手窗口

__all__=['浏览器登录']

失败阶段=('failed','expired','cancelled')

class 浏览器登录:
    '预开的标签和宿主授权状态分开记'
    def __init__(自身,目的地):
        '目的地在标签真正跳转时才把授权地址换成要打开的页'
        自身.目的地=目的地
        自身.弹窗=None
        自身.已跳转=False
        自身.尝试=None

    def 开始(自身,请求,最新):
        '先占住用户点击里的标签，再跟上宿主返回的这次尝试'
        自身.预开()
        try:
            自身.跟随(请求())
            自身.更新(最新())
        except Exception:
            自身.拆除()
            raise

    def 预开(自身):
        '在点击里打开空白标签。被拦截时改走复制链接'
        自身.拆除()
        窗口=取握手窗口()
        自身.弹窗=窗口.open('about:blank','_blank')
        if 自身.弹窗:
            自身.弹窗.opener=None

    def 跟随(自身,视图):
        '把预开的标签绑到这次尝试'
        尝试=None
        if isinstance(视图,dict):
            尝试=视图.get('attempt')
        自身.尝试=尝试.get('id') if isinstance(尝试,dict) else None
        自身.更新(视图)

    def 更新(自身,视图):
        '尝试变化时跳转或关掉还没打开的标签'
        尝试=None
        if isinstance(视图,dict):
            尝试=视图.get('attempt')
        标识=尝试.get('id') if isinstance(尝试,dict) else None
        if 标识!=自身.尝试:
            return
        阶段=尝试.get('phase') if isinstance(尝试,dict) else None
        if 阶段 in 失败阶段:
            自身.拆除()
            return
        if 阶段=='succeeded':
            if 自身.已跳转 is not True and 自身.弹窗 is not None:
                自身.弹窗.close()
            自身.弹窗=None
            自身.尝试=None
            return
        授权=尝试.get('authorizeUrl') if isinstance(尝试,dict) else None
        if not 授权 or 自身.已跳转:
            return
        自身.已跳转=True
        if 自身.弹窗 is not None and 自身.弹窗.closed is not True:
            自身.弹窗.location.replace(自身.目的地(授权))

    def 拆除(自身):
        '关掉自己打开的授权标签，不再跟这次尝试'
        if 自身.弹窗 is not None:
            自身.弹窗.close()
        自身.弹窗=None
        自身.尝试=None
        自身.已跳转=False
