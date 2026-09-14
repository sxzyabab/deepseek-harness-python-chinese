from ..约定.类型 import 停靠模式推挤,窗格宿主停靠#约定

__all__=['创建标识铸造','创建初始状态']#仅中文公开名


def 创建标识铸造(种子=0):
    """创建单调标识源；返回可调用 铸造(前缀)->str，形如 `<前缀><n>`。"""
    计数=[种子]#可变闭包

    def 铸造(前缀):
        """下一标识；前缀命名种类。"""
        计数[0]+=1#递增
        return 前缀+str(计数[0])#拼接

    return 铸造#可调用


def 创建初始状态(铸造,造初签=None,模式=停靠模式推挤):
    """折叠单停靠窗初态；造初签可选，省略则空窗格。"""
    窗格标识=铸造('pane')#窗格
    初签=造初签(铸造('tab')) if 造初签 is not None else None#可选签
    return {#布局状态
        'nodes':{#节点表
            窗格标识:{#窗格
                'kind':'pane',
                'id':窗格标识,
                'host':窗格宿主停靠,
                'tabs':[] if 初签 is None else [初签['id']],
                'activeTabId':None if 初签 is None else 初签['id'],
                'rect':None,
            },
        },
        'tabs':{} if 初签 is None else {初签['id']:初签},
        'rootId':窗格标识,
        'floats':[],
        'activePaneId':窗格标识,
        'expanded':False,
        'mode':模式,
    }#初态结束
