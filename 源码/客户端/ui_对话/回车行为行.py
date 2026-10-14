
__all__=['回车行为行','选项表']#仅中文公开名

选项表=(#忙碌 Enter 选项
    {'id':'queue','label':'settings.enter.queue'},#排队
    {'id':'steer','label':'settings.enter.steer'},#插话
)#选项结束

from nicegui import ui as 界面
from .异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 恒等选(值):
    '选择器原样返回偏好'
    return 值#原样

class 回车行为行:
    '忙碌态纯 Enter 行为选择器'
    def __init__(自身,属性):
        '记下 props'
        自身.属性=属性#合成 props
        自身.打开=False#菜单开
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性#最新

    def 读行为(自身):
        '经 useBusyEnter'
        用=自身.属性['useBusyEnter'] if 'useBusyEnter' in 自身.属性 else None#选择器
        if 用 is not None:#有
            出=用(恒等选)#行为
            return 出 if 出 is not None else 'queue'#缺则排队
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}#hooks
        存储=钩['busyEnter'] if 'busyEnter' in 钩 else None#存储
        if 存储 is not None:#有
            return 存储.getSnapshot()#行为
        return 'queue'#默认

    def 切换菜单(自身):
        '翻转开合'
        自身.打开=not 自身.打开#翻

    def 关菜单(自身):
        '关闭'
        自身.打开=False#关

    def 选择(自身,标识):
        '写入并关菜单'
        自身.打开=False#关
        设=自身.属性['setBusyEnter'] if 'setBusyEnter' in 自身.属性 else None#写入
        if 设 is not None:#有
            设(标识)#写

    def 渲染(自身):
        '画出标题、说明和忙碌时的发送行为。'
        原译=自身.属性['t'] if 't' in 自身.属性 and 自身.属性['t'] is not None else None#宿主文案
        def 翻译(键,参数=None):
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
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('回车行为')#行
        def 重画():
            '按菜单开合重画。'
            自身.画面.clear()#清空
            行为=自身.读行为()#当前
            选中标签='settings.enter.queue' if 行为=='queue' else 'settings.enter.steer'#标签键
            with 自身.画面:#行
                贴出失败(自身)
                界面.label(翻译('settings.enter.title'))#标题
                界面.label(翻译('settings.enter.description')).classes('设置说明')#说明
                def 点菜单():
                    '翻转菜单。'
                    自身.切换菜单()#翻
                    重画()#重画
                界面.button(翻译(选中标签),on_click=点菜单)#当前
                if 自身.打开 is True:#菜单
                    for 项 in 选项表:#选项
                        def 造点(标识=项['id']):
                            '选中这一项并收起。'
                            def 点():
                                '写入行为。'
                                自身.选择(标识)#写
                                重画()#重画
                            return 点#回调
                        界面.button(翻译(项['label']),on_click=造点())#选项
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

from .客户端.文案 import 中文 as 对话文案#类先绑定，再装词表，避免和客户端包互相导入
