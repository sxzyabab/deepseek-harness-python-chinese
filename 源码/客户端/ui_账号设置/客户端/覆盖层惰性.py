'重叠的账号覆盖层共同占有背景的 inert'

__all__=['取得覆盖层惰性']

持有者=[]

def 查找(元素):
    '按节点身份找占有记录'
    for 项 in 持有者:
        if 项['元素'] is 元素:
            return 项
    return None

def 取得覆盖层惰性(元素):
    '挡住背景。最后一个占有者放开时恢复原来的 inert'
    状态=查找(元素)
    if 状态 is None:
        状态={'元素':元素,'count':0,'previous':元素.inert}
        持有者.append(状态)
    状态['count']+=1
    元素.inert=True
    已放开={'值':False}
    def 放开():
        '重复放开无效。计数到零才恢复'
        if 已放开['值']:
            return
        已放开['值']=True
        状态['count']-=1
        if 状态['count']==0:
            元素.inert=状态['previous']
            if 状态 in 持有者:
                持有者.remove(状态)
    return 放开
