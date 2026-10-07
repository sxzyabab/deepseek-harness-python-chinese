from ....基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from ...存储 import 创建快照存储

__all__=['在应用中打开路径控制器']

class 在应用中打开路径控制器:
    '页面寿命内的桌面可用性与打开/揭示载体'
    def __init__(自身,远程):
        自身.远程=远程
        自身.桌面=创建快照存储(None)
        自身.加载中=None

    def 加载(自身):
        if 自身.加载中 is None:
            自身.跑()
            自身.加载中=True
        return

    def 打开路径(自身,路径,动作,应用=None):
        '返回期约：成功解决 None，失败解决错误文案键'
        请求={'path':路径,'action':动作} if 动作=='reveal' else {'path':路径}
        if 动作!='reveal' and 应用 is not None:
            请求['application']=应用
        结算=期约()#本次打开
        失败文案='openError' if 动作=='open' else 'revealError'#失败键
        def 失败(_错误):
            '当失败'
            结算.解决(失败文案)#错误键
        def 已应答(应答):
            'ok 则无错误键'
            if isinstance(应答,dict) and 应答.get('ok') is True:#成功
                结算.解决(None)#无错误
                return
            失败(None)#失败
        try:#打开
            接上(自身.远程.session.openWorkspacePath(请求),已应答,失败)#期约
        except Exception:#同步失败
            失败(None)#失败
        return 结算#期约

    def 应用列表(自身,路径,信号):
        '返回期约，失败解决 None'
        结算=期约()#本次列表
        def 失败(_错误):
            '当无列表'
            结算.解决(None)#无
        def 已应答(应答):
            'ok 则取 value'
            if isinstance(应答,dict) and 应答.get('ok') is True:#成功
                结算.解决(应答.get('value'))#表
                return
            失败(None)#失败
        try:#列举
            接上(自身.远程.session.workspacePathApplications({'path':路径},信号),已应答,失败)#期约
        except Exception:#同步失败
            失败(None)#失败
        return 结算#期约

    def 跑(自身):
        '可用性落到桌面快照'
        def 发布(可用):
            '写入快照'
            自身.桌面.set(可用)#发布
        def 失败(_错误):
            '不可用'
            发布(False)#不可用
        def 已应答(应答):
            'ok 且值为真才可用'
            发布(isinstance(应答,dict) and 应答.get('ok') is True and 应答.get('value') is True)#可用
        try:#探测
            接上(自身.远程.session.canOpenWorkspacePath(),已应答,失败)#期约
        except Exception:#同步失败
            失败(None)#不可用

def 接上(产出,成功,失败):
    '期约走 然后，上游 then 走 then；已是值则直接成功'
    if hasattr(产出,'然后'):#本层期约
        产出.然后(成功,失败)#接上
        return
    if hasattr(产出,'then'):#上游期约
        产出.then(成功,失败)#接上
        return
    成功(产出)#已是值
