"""已存与已采纳布局的元数据清单，不挂载其内容。"""
from ...存储 import 创建快照存储#快照存储
from .持久化 import 读侧栏布局,侧栏持久化前缀#读布局与前缀

__all__=['侧栏标签清单']#仅中文公开名

class 侧栏标签清单:#标签清单
    """仅派生成员关系；布局存储仍是持久化权威。"""

    def __init__(自身,存储=None):#构造时扫描
        """在根服务发布前读一次已存布局。"""
        自身.会话表={}#按会话
        自身.快照=创建快照存储([])#可观察快照
        自身.源=自身.快照#源
        if 存储 is None:#无存储
            return#空
        try:#扫描键
            长度=存储.length
            for 下标 in range(长度):
                键=存储.key(下标)
                if 键 is None or not 键.startswith(侧栏持久化前缀+'.'):
                    continue
                会话标识=键[len(侧栏持久化前缀)+1:]
                已存=读侧栏布局(会话标识,存储)
                if 已存 is not None:
                    布局=已存['layout']
                    原表=布局['tabs'] if 'tabs' in 布局 else None
                    标签表={} if 原表 is None else 原表
                    自身.会话表[会话标识]=[{
                        'sessionId':会话标识,
                        'tabId':标签['id'],
                        'kind':标签['kind'],
                        'contentId':标签['contentId'],
                    } for 标签 in 标签表.values()]
            自身.发布()
        except (TypeError,AttributeError):
            pass

    def 更新(自身,会话标识,标签表):
        """用窗口内权威存储替换成员关系。"""
        自身.会话表[会话标识]=[{#行
            'sessionId':会话标识,
            'tabId':标签['id'],
            'kind':标签['kind'],
            'contentId':标签['contentId'],
        } for 标签 in 标签表]
        自身.发布()#发布

    def 移除(自身,会话标识):
        """忘记永久清空的作用域。"""
        if 会话标识 in 自身.会话表:#有
            del 自身.会话表[会话标识]#删
        自身.发布()#发布

    def 发布(自身):
        """发布扁平表。"""
        下一批=[]#扁平
        for 表 in 自身.会话表.values():#逐会话
            下一批.extend(表)#展平
        if 下一批!=自身.快照.getSnapshot():#有变
            自身.快照.set(下一批)#写
