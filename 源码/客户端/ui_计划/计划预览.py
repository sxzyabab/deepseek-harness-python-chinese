from nicegui import ui as 界面
from .失败行 import 计划失败行#失败行
from .审阅预览 import 是否审阅预览地址#临时审阅

__all__=['计划预览','计划标题']#仅中文公开名

def 恒等翻译(键,参数=None):
    '无文案表时返回键'
    return 键#键

class 计划预览:
    '已记录或临时审阅的只读 Markdown 查看器'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        if 'useTabInfo' in 自身.属性 and 'useResource' in 自身.属性:#槽位份额齐了
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '计划文档或加载/失败态'
        属性=自身.属性#props
        用标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None#标签
        用资源=属性['useResource'] if 'useResource' in 属性 else None#资源
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        if 用标签 is None or 用资源 is None:#缺
            return None#无
        标签=用标签()#标签信息
        导航=标签['tab']['navigation'] if 'tab' in 标签 and 'navigation' in 标签['tab'] else {}#导航
        地址=导航['address'] if 'address' in 导航 else ''#地址
        资源=用资源(地址)#资源
        临时=是否审阅预览地址(地址)#临时
        参数=导航['params'] if 'params' in 导航 else None#参数
        if 临时:#临时
            计划=参数['planReview'] if isinstance(参数,dict) and 'planReview' in 参数 else None#审阅
        else:#已记录
            计划=资源['value'] if isinstance(资源,dict) and 'value' in 资源 else None#值
        if 计划 is None:#无计划
            if 临时:#过期
                文案=翻译('preview.expired')#过期
            elif isinstance(资源,dict) and 资源.get('status')=='none':#不可用
                文案=翻译('preview.unavailable')#不可用
            elif isinstance(资源,dict) and 资源.get('status')=='failed':#失败
                文案=翻译('preview.failed')#失败
            else:#加载
                文案=翻译('preview.loading')#加载
            界面.label(文案)
            if not 临时 and isinstance(资源,dict) and 资源.get('failure') is not None:
                失败文=计划失败行(翻译,资源['failure'])#行
                if isinstance(失败文,str) and 失败文!='':
                    界面.label(失败文)
            return
        标题=计划.get('title')
        正文=计划.get('markdown')
        with 界面.column().classes('plan-preview'):
            if isinstance(标题,str) and 标题!='':
                界面.label(标题)
            if isinstance(正文,str):
                界面.markdown(正文)

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()

class 计划标题:
    '侧栏标签标题：图标 + 恢复标题'
    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        if 'useTabInfo' in 自身.属性:
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '标题文本'
        属性=自身.属性#props
        用标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None#标签
        用资源=属性['useResource'] if 'useResource' in 属性 else None#资源
        if 用标签 is None:#缺
            return None#无
        标签=用标签()#信息
        导航=标签['tab']['navigation'] if 'tab' in 标签 and 'navigation' in 标签['tab'] else {}#导航
        地址=导航['address'] if 'address' in 导航 else ''#地址
        参数=导航['params'] if 'params' in 导航 else None#参数
        if 是否审阅预览地址(地址):#临时
            计划=参数['planReview'] if isinstance(参数,dict) and 'planReview' in 参数 else None#审阅
        else:#已记录
            资源=用资源(地址) if 用资源 is not None else {}#资源
            计划=资源['value'] if isinstance(资源,dict) and 'value' in 资源 else None#值
        标题=计划['title'] if isinstance(计划,dict) and 'title' in 计划 else 标签['tab'].get('title')#标题
        with 界面.row().classes('plan-title'):
            界面.icon('description', size='16px')
            if 标题 is not None and str(标题)!='':
                界面.label(str(标题))

    def __call__(自身,属性=None):
        '对齐'
        if 属性 is not None:
            自身.更新(属性)#刷
        return 自身.渲染()
