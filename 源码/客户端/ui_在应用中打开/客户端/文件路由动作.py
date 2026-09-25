"""把已授权投递与变更文件路由接到共享打开控件。"""
import builtins#页面 fetch
from .文件应用 import 使用文件应用#联想查询
from .打开目标按钮 import 打开目标按钮#共享分体按钮

__all__=['查询路由','文件路由动作']#仅中文公开名

取=builtins.fetch if hasattr(builtins,'fetch') else None#页面 fetch

def 查询路由(网址,信号):
    """经授权路由拉文件关联；不可用或畸形则 None，回落揭示。"""
    try:#请求
        if 取 is None:#无 fetch
            return None#无
        应答=取(网址,{'signal':信号})#请求
        if hasattr(应答,'等待'):#异步
            应答=应答.等待()#等
        if hasattr(应答,'ok') and not 应答.ok:#非 OK
            return None#无
        体=应答.json() if hasattr(应答,'json') else 应答#体
        if hasattr(体,'等待'):#异步 json
            体=体.等待()#等
        if isinstance(体,list):#已是应用表
            return 体#原样
        if isinstance(体,dict) and 'applications' in 体:#包装
            return 体['applications']#表
        return None#畸形
    except Exception:#不可用路由
        return None#回落揭示

class 文件路由动作:#投递文件动作席
    """不绕开所属会话的授权路由渲染文件动作。
    无桌面时 None。
    """

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身._按钮=None#子控件

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#最新
        自身._按钮=None#重建

    def 渲染(自身):
        """紧凑共享控件，或不可用时 None。"""
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
            """转 onAction。"""
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
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
