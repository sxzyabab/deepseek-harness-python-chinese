'原文里已确认的技能名。斜杠和词边界保持原文'
import re

__all__=['技能引用规则']

令牌=re.compile(r'(?<!\S)/([A-Za-z0-9_-]+)(?!\S)')#词边界上的 /名字

def 匹配(文本,从,上下文):
    '最近一个已确认的斜杠技能名，保留原来的词边界'
    名称列=None#事实还没读
    命中=令牌.search(文本,从)#从游标往后
    while 命中 is not None:#逐个斜杠词
        if 名称列 is None:#第一次才读事实
            名称列=上下文['read']('skillNames')#已确认的名字
            if 名称列 is None or len(名称列)==0:#没有确认名
                return None#不标技能
        名=命中.group(1)#去掉斜杠的名字
        if 名 in 名称列:#这一条被确认过
            return {#命中
                'id':'skill',#规则标识
                'start':命中.start(),#含斜杠
                'end':命中.end(),#词尾
                'data':{'name':名},#不含斜杠
            }
        命中=令牌.search(文本,命中.end())#下一个
    return None#没有确认名

技能引用规则={#登记给用户文本
    'id':'skill',#规则标识
    'order':20,#顺序
    'match':匹配,#匹配
}
