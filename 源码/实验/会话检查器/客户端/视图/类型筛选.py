'已确认的类型筛选保留查看匹配嵌套行所需的祖先'

import re
from .....基础设施.js特性 import PromiseEX as 期约#候选列表延后到下一拍

__all__=['检查器类型筛选']

def 去掉两侧星号(查询):
    '去掉可选的两侧星号，保留输入的大小写'
    return re.sub(r'^\*+|\*+$','',查询.strip()).strip()

class 检查器类型筛选:
    '大小写不敏感的包含筛选；两侧星号与省略同义'
    def __init__(自身,查询):
        '查询为类型片段；空文本或只有星号则清除筛选'
        自身.查询=去掉两侧星号(查询)
        自身._针=自身.查询.lower()

    @property
    def 活动(自身):
        '区分类型限制与空查询或全星号查询'
        return 自身._针!=''

    def 匹配(自身,类型):
        '按大小写不敏感包含匹配；筛选未激活时接受全部类型'
        return (not 自身.活动) or (类型 is not None and 自身._针 in 类型.lower())

    def 应用(自身,行表,取类型):
        '保留匹配行及其祖先；匹配后代即使位于闭合块下也起始可见'
        if not 自身.活动:
            return {'rows':行表,'matches':{行['key'] for 行 in 行表}}
        匹配集={行['key'] for 行 in 行表 if 自身.匹配(取类型(行['key']))}
        按键={行['key']:行 for 行 in 行表}
        保留=set(匹配集)
        for 键 in 匹配集:
            父=按键[键].get('parent') if 键 in 按键 else None
            while 父 is not None and 父 not in 保留:
                保留.add(父)
                父=按键[父].get('parent') if 父 in 按键 else None
        分支=set()
        for 键 in 保留:
            父=按键[键].get('parent') if 键 in 按键 else None
            if 父 is not None:
                分支.add(父)
        结果行=[]
        for 行 in 行表:
            if 行['key'] not in 保留:
                continue
            纯={键:值 for 键,值 in 行.items() if 键!='disclosure'}
            if 行['key'] in 分支:
                纯['disclosure']='open'
            结果行.append(纯)
        return {'matches':匹配集,'rows':结果行}

    def 建议(自身,行表,取类型):
        '从全部已加载行异步解析候选，不是已筛选子集。返回期约，兑现值为确定顺序的类型列表'
        def 收集(结果=None):
            '去重后排序'
            类型集=set()
            for 行 in 行表:
                类型=取类型(行['key'])
                if 类型 is not None and 自身.匹配(类型):
                    类型集.add(类型)
            return sorted(类型集)
        起点=期约()
        兑现=起点.然后(收集)
        起点.解决(None)
        return 兑现
