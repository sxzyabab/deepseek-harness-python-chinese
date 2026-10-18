from ...异常 import 右侧侧栏错误

__all__=['向导种类','页面地址','默认种子']

向导种类='guide'


def 页面地址(种类):
    '页面签记录地址 sidebar://<kind>。调用方只点种类'
    return 'sidebar://'+种类


def 默认种子(标签表):
    '零个或多个入口时用向导，只有一个入口时用那个种类'
    入口表=标签表.向导()
    仅有=入口表[0] if len(入口表)>0 else None
    其余=入口表[1:]
    单独=仅有 is not None and len(其余)==0
    种类=仅有['kind'] if 单独 else 向导种类
    定义=标签表.取(种类)
    if 定义 is None:
        raise 右侧侧栏错误('sidebarRight: default tab kind "'+种类+'" is not registered')
    return {'kind':种类,'title':定义['title'](页面地址(种类))}
