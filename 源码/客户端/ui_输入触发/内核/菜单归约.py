'菜单名册的纯数据。归约本体只被控制器用一次，写在控制器里'
__all__=['源字段','菜单关闭','铺分组','精确匹配']

菜单关闭={#关闭着的初态，世代为 0
    'open':False,#未打开
    'hit':None,#没有命中
    'generation':0,#世代
    'groups':[],#没有分组
    'highlight':None,#没有高亮
}

def 源字段(源,键):
    '触发源是字典或对象。没有这个字段则为 None'
    if isinstance(源,dict):#字典源
        if 键 in 源:#有这个键
            return 源[键]#值
        return None#缺席
    return getattr(源,键,None)#对象属性

def 铺分组(状态,源列表):
    '按名册换成等待中的分组，并清掉高亮'
    组列=[]#新名册
    for 源 in 源列表:#登记顺序
        组={'source':源字段(源,'name'),'status':'pending','items':[]}#等待中，先不带候选项
        if 源字段(源,'showGroupTitle') is False:#源不要组标题
            组['showGroupTitle']=False#只有明确关掉才写上
        组列.append(组)#放进名册
    下一=dict(状态)#抄一份状态
    下一['groups']=组列#换名册
    下一['highlight']=None#高亮清掉
    return 下一#新状态

def 精确匹配(组列表,源名,名字):
    '在一个源的就绪组里按名字精确查找。组不在、未就绪或没有这个名字则为 None'
    组=None#目标组
    for 项 in 组列表:#按组找
        if 项['source']==源名:#这个源
            组=项#记下
            break#找到了
    if 组 is None or 组['status']!='ready':#没有或还在等
        return None#对不上
    for 候选 in 组['items']:#就绪候选项
        if 候选['name']==名字:#名字相同
            return 候选#这一行
    return None#没有这个名字
