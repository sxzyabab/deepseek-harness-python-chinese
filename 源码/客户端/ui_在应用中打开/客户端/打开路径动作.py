"""文件关联适配：文档头与不可预览空态共用打开控件。"""
from .文件应用 import 使用文件应用#联想查询
from .打开目标按钮 import 打开目标按钮#共享分体按钮

__all__=['文件打开目标','打开路径动作']#仅中文公开名

class 文件打开目标:#文件路径 → 共享打开控件
    """解析文件关联并适配操作，不把平台行为嵌进控件。
    无桌面时渲染 None。
    """

    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#props
        自身._按钮=None#子控件

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#最新
        自身._按钮=None#重建

    def _读桌面(自身):
        """经 useOpenInAppDesktop。"""
        用=自身.属性['useOpenInAppDesktop'] if 'useOpenInAppDesktop' in 自身.属性 else None#钩子
        if 用 is not None:#有
            return 用(lambda 值:值)#原样
        return None#缺席

    def _确保桌面(自身):
        """桌面未知时触发加载。"""
        if 自身._读桌面() is None:#未知
            加载=自身.属性['loadDesktop'] if 'loadDesktop' in 自身.属性 else None#加载
            if 加载 is not None:#有
                加载()#拉桌面

    def 渲染(自身):
        """共享打开控件，或无桌面时 None。"""
        自身._确保桌面()#拉
        if 自身._读桌面() is not True:#非桌面
            return None#不渲染
        属性=自身.属性#props
        路径=属性['absolutePath']#绝对路径
        查询=属性['applications']#联想查询
        联想=使用文件应用(路径,查询,True)#联想
        默认标识=None#默认应用
        for 应用 in 联想['apps']:#找 Host 默认
            if 应用.get('default') is True:#默认
                默认标识=应用['id']#记下
                break#止
        空态=属性['empty'] is True if 'empty' in 属性 else False#不可预览大钮
        def 执行(操作):
            """转 openPath 契约。"""
            动作='reveal' if 操作['kind']=='reveal' else 'open'#动作
            应用=操作['id'] if 操作['kind']=='application' else None#应用 id
            return 属性['openPath'](路径,动作,应用)#跑
        面={#按钮 props
            'kind':'file',#文件
            'applications':[{'id':应用['id'],'name':应用['name'] if 'name' in 应用 else 应用['id'],'icon':应用['icon'] if 'icon' in 应用 else None} for 应用 in 联想['apps']],#应用
            'defaultId':默认标识,#默认
            'loading':联想['loading'],#加载
            'failed':联想['failed'],#失败
            'prominent':空态,#大钮
            't':属性['t'],#文案
            'refresh':联想['refresh'],#刷新
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

class 打开路径动作:#文档头贡献
    """在文档头渲染文件适配器。"""

    def __init__(自身,属性):
        """记下 props。"""
        自身.目标=文件打开目标(属性)#目标

    def 更新(自身,属性):
        """刷新。"""
        自身.目标.更新(属性)#透传

    def 渲染(自身):
        """共享分体按钮。"""
        return 自身.目标.渲染()#渲染

    def __call__(自身,属性=None):
        """刷新后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
