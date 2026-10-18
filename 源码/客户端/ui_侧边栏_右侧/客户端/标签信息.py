'从存储和导航钩子读出一张签现在的信息'
from ...ui_停靠套件.引擎.树 import 查找标签窗格
from ..异常 import 右侧侧栏错误

__all__=['标签信息工厂','向导标签信息工厂']


def 标签信息工厂(标准,上下文):
    '工厂求值时不订阅。返回的函数才去读'
    会话标识=标准['sessionId']
    标签标识=上下文['tabId']
    是标题=上下文['title']
    全屏=上下文['fullscreen']
    活动=上下文['active']
    信号=上下文['signal']
    动作=上下文['actions']
    用存储=上下文['useStore']
    用导航=上下文['useTabNavigation']
    快捷键表=上下文['shortcuts']

    def 取布局(状态):
        '这个会话的布局'
        表面=状态['bySession'].get(会话标识)
        if 表面 is None:
            return None
        return 表面['layout']

    def 取标签信息():
        '侧栏呈现、所在窗和这张签'
        布局=用存储(取布局)
        导航=用导航(标签标识)
        签=None if 布局 is None else 布局['tabs'].get(标签标识)
        if 布局 is None or 签 is None or 导航 is None:
            raise 右侧侧栏错误('sidebarRight: tab "'+str(标签标识)+'" is not committed in session "'+str(会话标识)+'"')
        窗=查找标签窗格(布局,标签标识)
        可见=活动 and (窗['host']=='float' or (布局['expanded'] and (是标题 or 窗.get('activeTabId')==标签标识)))
        刷新键=None
        for 行 in 快捷键表:
            if 行.get('id')=='page.refresh':
                刷新键=行
                break
        结果=dict(签)
        结果['visible']=可见
        结果['navigation']=导航
        结果['signal']=信号
        结果['actions']=动作
        结果['refreshShortcut']=刷新键
        return {
            'sidebar':{'expanded':布局['expanded'],'fullscreen':全屏},
            'panel':{'id':窗['id']},
            'tab':结果,
        }

    return 取标签信息


def 向导标签信息工厂(_标准,取标签信息):
    '向导替换读的还是外层那张签'
    return 取标签信息
