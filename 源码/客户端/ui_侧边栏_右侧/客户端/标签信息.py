from ...ui_停靠套件.引擎 import 查找标签窗格
from .约定.槽位 import 右侧侧栏错误

__all__=['标签信息工厂','向导标签信息工厂']


def 标签信息工厂(标准,上下文):
    """绑定一出现次的读面；工厂求值期不订阅、不建记录。返回 取标签信息。"""
    会话标识=标准['sessionId']#会话
    标签标识=上下文['tabId']#签
    是标题=上下文['title']#是否标题席
    全屏=上下文['fullscreen']#全屏
    活动=上下文['active'] if 'active' in 上下文 else True
    信号=上下文['signal']#寿命
    动作=上下文['actions']#自动作
    用存储=上下文['useStore']#存储选择
    用导航=上下文['useTabNavigation']#导航选择

    def 取标签信息():
        """当前侧栏呈现、所在窗与活动签面。"""
        布局=用存储(lambda 态:态['bySession'][会话标识]['layout'] if 会话标识 in 态['bySession'] else None)#布局
        导航=用导航(标签标识)#导航
        if 布局 is None or 标签标识 not in 布局['tabs'] or 导航 is None:#未提交
            raise 右侧侧栏错误('标签 "'+str(标签标识)+'" 未在会话 "'+str(会话标识)+'" 中提交')
        签=布局['tabs'][标签标识]#记录
        窗=查找标签窗格(布局,标签标识)#窗
        可见=活动 and (窗['host']=='float' or (布局['expanded'] and (是标题 or 窗['activeTabId']==标签标识)))#可见
        return {#标签信息
            'sidebar':{'expanded':布局['expanded'],'fullscreen':全屏},
            'panel':{'id':窗['id']},
            'tab':{**签,'visible':可见,'navigation':导航,'signal':信号,'actions':动作},
        }#信息

    return 取标签信息#钩


def 向导标签信息工厂(_标准,取标签信息):
    """把外层标签读面转给向导替换。"""
    return 取标签信息#原样
