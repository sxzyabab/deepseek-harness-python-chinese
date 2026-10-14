
__all__=['详情面板']#仅中文公开名

from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

def 取选中(快照):
    '仓 selection'
    return 快照['selection'] if 快照 is not None and 'selection' in 快照 else None#选中

class 详情面板:
    '标题+关闭+工具席或空态'

    def __init__(自身,属性=None):
        '记下 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '详情结构'
        属性=自身.属性#props
        用存储=属性['useStore'] if 'useStore' in 属性 else None#存储
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        关闭=属性['closeDetails'] if 'closeDetails' in 属性 else None#关
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        选中=用存储(取选中) if 用存储 is not None else None#选中
        调用标识=选中['callId'] if 选中 is not None and 'callId' in 选中 else None#调用
        有选=选中 is not None and 调用标识 is not None#有调用
        工具名=选中['toolName'] if 选中 is not None and 'toolName' in 选中 else None#名
        if 有选 is False or 工具名 is None or 工具名=='':#无工具名
            标题=翻译('details.title')#默认标题
        else:#工具名
            标题=工具名#标题
        原译=翻译 if 翻译 is not 恒等翻译 else None#已取的宿主文案
        def 取文案(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        翻译=取文案#改走词典
        if 有选 is False or 工具名 is None or 工具名=='':#重算标题
            标题=翻译('details.title')#默认标题
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('详情面板')#面板
        自身.画面.clear()#清空
        with 自身.画面:#面板
            贴出失败(自身)
            with 界面.row().classes('标题行'):#标题
                界面.label(标题)#标题
                def 点关闭():
                    '关闭详情。'
                    if 关闭 is not None:#有
                        关闭()#关
                界面.button(翻译('details.close'),on_click=点关闭)#关闭
            if 有选 is False:#空
                界面.label(翻译('details.empty'))#空态
            else:#工具席自己画
                渲染槽('conversation.details.tool',{'selection':选中})#工具

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
