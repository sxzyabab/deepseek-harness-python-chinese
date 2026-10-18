'按文件后缀登记预览实现。正文组件走带键的文档槽'
from .后缀 import 文档文件名,规范化后缀,匹配后缀长度

__all__=['匹配文档预览','二进制文档路径','文档预览注册表']

def 匹配文档预览(定义列表,路径):
    '外部实现优先，然后更长的后缀，然后登记顺序'
    名=文档文件名(路径)
    候选=[]
    序号=0
    for 定义 in 定义列表:
        长度=匹配后缀长度(名,定义['extensions'])
        if 长度<=0:
            序号=序号+1
            continue
        档=0 if 定义.get('priority')=='builtin' else 1
        候选.append({'definition':定义,'order':序号,'rank':档,'length':长度})
        序号=序号+1
    def 次序(项):
        '外部档优先，其次更长后缀，其次更早登记'
        return (-项['rank'],-项['length'],项['order'])
    候选.sort(key=次序)
    结果=[]
    for 项 in 候选:
        结果.append(项['definition'])
    return 结果

def 二进制文档路径(定义列表,路径):
    '有没有实现把这个文件名的后缀声明成二进制'
    名=文档文件名(路径)
    for 定义 in 定义列表:
        二进制=定义['binaryExtensions'] if 'binaryExtensions' in 定义 and 定义['binaryExtensions'] is not None else []
        if 匹配后缀长度(名,二进制)>0:
            return True
    return False

class 文档预览注册表:
    '当前还活着的全部实现，含优先级较低的备选'
    def __init__(自身):
        '空登记'
        自身.已登记={}
        自身.监听=set()
        自身.快照=[]

    def 取快照(自身):
        '登记变化前保持同一份列表'
        return 自身.快照

    def 订阅(自身,监听):
        '观察登记变化。返回拆除器'
        自身.监听.add(监听)
        def 拆除():
            '卸下这个观察者'
            自身.监听.discard(监听)
        return 拆除

    def 登记(自身,定义):
        '登记元数据。重复的实现名，或 binaryExtensions 不在 extensions 里，都抛错'
        if 定义['id'] in 自身.已登记:
            raise ValueError('documentPreviews: duplicate implementation "'+定义['id']+'"')
        已声明=set()
        for 扩展 in 定义['extensions']:
            已声明.add(规范化后缀(扩展))
        二进制=定义['binaryExtensions'] if 'binaryExtensions' in 定义 and 定义['binaryExtensions'] is not None else []
        for 扩展 in 二进制:
            if 规范化后缀(扩展) not in 已声明:
                raise ValueError('documentPreviews: "'+定义['id']+'" declares binary suffix "'+扩展+'" outside its extensions')
        自身.已登记[定义['id']]=定义
        自身.发布()
        活动={'值':True}
        def 拆除():
            '再调一次没有事'
            if 活动['值'] is False:
                return
            活动['值']=False
            del 自身.已登记[定义['id']]
            自身.发布()
        return 拆除

    def 候选(自身,路径):
        '按自动选择的顺序列出全部匹配实现'
        return 匹配文档预览(自身.快照,路径)

    def 发布(自身):
        '换成新快照并通知。一个监听失败不挡住其余'
        自身.快照=list(自身.已登记.values())
        for 监听 in list(自身.监听):
            try:
                监听()
            except Exception as 错误:
                print('[document-previews] registry subscriber failed:',错误)

文档预览注册表.getSnapshot=文档预览注册表.取快照
文档预览注册表.subscribe=文档预览注册表.订阅
文档预览注册表.register=文档预览注册表.登记
文档预览注册表.candidates=文档预览注册表.候选
