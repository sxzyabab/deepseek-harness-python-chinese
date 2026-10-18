'两张虚拟表共用的行身份和原始值'

def 检查器行已折叠(行,选择):
    '手动选择只在当时的展开状态还在时有效，否则用块自己的默认'
    已选=选择.get(行['key'])#这个键上的手动选择
    if 已选 is not None and 已选.get('state')==行.get('disclosure'):#还是做出选择时的状态
        return 已选['collapsed'] is True#用手动结果
    return 行.get('disclosure')=='closed'#默认合上才藏后代

class 检查器表格层级:
    '按深度优先顺序藏起合上的后代，并记下粘性祖先'
    def __init__(自身,行列表,选择):
        '行列表是完整的深度优先顺序，选择是这张表自己的展开覆盖'
        可见=[]#折叠后还看得到的行
        自身.按下标={}#键到可见下标
        自身.分支=set()#有后代或显式展开状态的键
        隐藏深度=None#当前被藏住的深度
        for 行 in 行列表:#按原顺序走
            父=行.get('parent')#父键
            if 父 is not None:#有父
                自身.分支.add(父)#父拥有后代
            if 行.get('disclosure') is not None:#自己有展开状态
                自身.分支.add(行['key'])#也算分支
            if 隐藏深度 is not None and 行['depth']>隐藏深度:#还在被藏的块里
                continue#不进入可见表
            if 检查器行已折叠(行,选择):#这一行合着
                隐藏深度=行['depth']#更深的都藏
            else:#开着或没有展开控件
                隐藏深度=None#后代可见
            自身.按下标[行['key']]=len(可见)#记下可见位置
            可见.append(行)#留下
        自身.行=可见#可见顺序

    def 是分支(自身,键):
        '这一行有没有展开控件'
        return 键 in 自身.分支#有后代或显式状态

    def 粘性下标(自身,下标):
        '视口第一行之上要钉住的祖先，自己是头时也包括自己'
        结果=[]#从近到远，最后再倒过来
        if 下标<0 or 下标>=len(自身.行):#没有这一行
            return 结果#空
        行=自身.行[下标]#当前可见行
        if 自身.是分支(行['key']):#自己就是头
            结果.append(下标)#先留下
        while 行.get('parent') is not None:#还有父
            父下标=自身.按下标.get(行['parent'])#父在可见表里的位置
            if 父下标 is None:#父被折叠藏掉了
                break#停
            结果.append(父下标)#钉住父
            行=自身.行[父下标]#继续往上
        结果.reverse()#外层祖先在前
        return 结果#有序下标

class 检查器记录源:
    '输入没变时沿用上一次投影，不换快照身份'
    def __init__(自身,源,投影):
        '源是已有的按键业务源，投影只在输入变了之后才跑'
        自身.源=源#业务源
        自身.投影=投影#变成表格记录
        自身.先前=未读#还没有读过
        自身.快照=None#当前记录

    def getSnapshot(自身):
        '当前原始值对应的稳定记录。值还是同一个对象就不再投影'
        if isinstance(自身.源,dict):#字典形源
            值=自身.源['getSnapshot']()#读快照
        else:#对象形源
            值=自身.源.getSnapshot()#读快照
        if 值 is not 自身.先前:#输入换了
            自身.先前=值#记下这一份
            if 值 is None:#记录没了
                自身.快照=None#空
            else:#还有值
                自身.快照=自身.投影(值)#只在变化后投影
        return 自身.快照#同一引用直到值变

    def subscribe(自身,监听):
        '行失效时通知。退订交给底层源'
        if isinstance(自身.源,dict):#字典形源
            return 自身.源['subscribe'](监听)#订
        return 自身.源.subscribe(监听)#订

未读=object()#区分「还没读」和快照就是 None
