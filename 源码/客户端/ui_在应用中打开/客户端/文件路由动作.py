'把已授权投递与变更文件路由接到共享打开控件'
from ....基础设施.js特性 import 请求#上游 fetch
from ....基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from .文件应用 import 使用文件应用#联想查询
from .打开目标按钮 import 打开目标按钮#共享分体按钮

__all__=['查询路由','文件路由动作']#仅中文公开名

def 接上(产出,成功,失败):#期约或上游 then
    '本层期约走 然后，上游 fetch 期约走 then；已是值则直接成功'
    if hasattr(产出,'然后'):#本层期约
        产出.然后(成功,失败)#接上
        return
    if hasattr(产出,'then'):#上游 fetch 期约
        产出.then(成功,失败)#接上
        return
    成功(产出)#已是值

def 查询路由(网址,信号):
    '经授权路由拉文件关联；不可用或畸形则解决 None，回落揭示。返回期约'
    结算=期约()#本次查询
    def 失败(_错误):
        '不可用则回落'
        结算.解决(None)#回落揭示
    def 体已到(体):
        '列表或包装里的 applications'
        if isinstance(体,list):#已是应用表
            结算.解决(体)#原样
            return
        if isinstance(体,dict) and 'applications' in 体:#包装
            结算.解决(体['applications'])#表
            return
        结算.解决(None)#畸形
    def 已响应(应答):
        '非 OK 则空；否则读 json'
        if hasattr(应答,'ok') and not 应答.ok:#非 OK
            结算.解决(None)#无
            return
        if isinstance(应答,dict) and 'applications' in 应答:#已是包装
            体已到(应答)#直接
            return
        if isinstance(应答,list):#已是表
            体已到(应答)#直接
            return
        体=应答.json() if hasattr(应答,'json') else 应答#体
        接上(体,体已到,失败)#json 期约
    try:#请求
        接上(请求(网址,{'signal':信号}),已响应,失败)#请求
    except Exception:#不可用路由
        失败(None)#回落揭示
    return 结算#期约

class 文件路由动作:#投递文件动作席
    """不绕开所属会话的授权路由渲染文件动作。
    无桌面时 None
    """

    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#props
        自身._按钮=None#子控件

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#最新
        自身._按钮=None#重建

    def 渲染(自身):
        '紧凑共享控件，或不可用时 None'
        属性=自身.属性#props
        if not 属性.get('available'):#不可用
            return None#不渲染
        网址=属性['actionUrl']#授权路由
        联想=使用文件应用(网址,查询路由,True)#联想
        默认标识=None#默认
        for 应用 in 联想['apps']:#找默认
            if 应用.get('default') is True:#默认
                默认标识=应用['id']#记下
                break#止
        def 执行(操作):
            '转 onAction'
            动作='reveal' if 操作['kind']=='reveal' else 'open'#动作
            应用=操作['id'] if 操作['kind']=='application' else None#应用
            return 属性['onAction'](动作,应用)#跑
        面={#按钮 props
            'kind':'file',#文件
            'applications':[{'id':应用['id'],'name':应用['name'] if 'name' in 应用 else 应用['id'],'icon':应用['icon'] if 'icon' in 应用 else None} for 应用 in 联想['apps']],#应用
            'defaultId':默认标识,#默认
            'failed':联想['failed'],#失败
            'loading':联想['loading'],#加载
            'busy':属性['pending'] if 'pending' in 属性 else False,#在飞
            'refresh':联想['refresh'],#刷新
            't':属性['t'],#文案
            'execute':执行,#执行
        }#面结束
        if 自身._按钮 is None:#初建
            自身._按钮=打开目标按钮(面)#建
        else:#刷新
            自身._按钮.更新(面)#更
        return 自身._按钮.渲染()#渲染

    def __call__(自身,属性=None):
        '刷新后渲染'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
