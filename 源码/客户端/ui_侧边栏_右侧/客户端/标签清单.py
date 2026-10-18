'已存和已采纳布局里打开了哪些签，不把正文挂出来'
from ...模块.客户端.通告 import 取握手窗口
import json
from ...存储 import 创建快照存储
from .持久化 import 读侧栏布局,侧栏持久化前缀

__all__=['侧栏标签清单']


class 侧栏标签清单:
    '成员关系从各会话布局摊平。布局存储仍是权威'

    def __init__(自身):
        '发布根服务之前先扫一遍已存布局'
        自身.会话表={}
        自身.快照=创建快照存储(())
        自身.源=自身.快照
        try:
            存储=取握手窗口().localStorage
            长度=存储['length']
            序号=0
            while 序号<长度:
                键=存储.key(序号)
                序号+=1
                if 键 is None or not str(键).startswith(侧栏持久化前缀+'.'):
                    continue
                会话标识=str(键)[len(侧栏持久化前缀)+1:]
                已存=读侧栏布局(会话标识)
                if 已存 is None:
                    continue
                行=[]
                for 签 in 已存['layout']['tabs'].values():
                    行.append({
                        'sessionId':会话标识,
                        'tabId':签['id'],
                        'kind':签['kind'],
                        'contentId':签['contentId'],
                    })
                自身.会话表[会话标识]=tuple(行)
            自身._发布()
        except Exception:
            return

    def 更新(自身,会话标识,标签表):
        '用窗口里这份布局替换成员'
        行=[]
        for 签 in 标签表:
            行.append({
                'sessionId':会话标识,
                'tabId':签['id'],
                'kind':签['kind'],
                'contentId':签['contentId'],
            })
        自身.会话表[会话标识]=tuple(行)
        自身._发布()

    def 移除(自身,会话标识):
        '忘掉这个被清掉的作用域'
        if 会话标识 in 自身.会话表:
            del 自身.会话表[会话标识]
        自身._发布()

    def _发布(自身):
        '摊平。内容没变就不换引用'
        下一=[]
        for 行 in 自身.会话表.values():
            下一.extend(行)
        下一=tuple(下一)
        if json.dumps(下一,ensure_ascii=False)!=json.dumps(自身.快照.getSnapshot(),ensure_ascii=False):
            自身.快照.set(下一)
