"""审阅标签视图态：选中文件、左右/单栏、是否换行。"""
__all__=['创建审阅存储']#仅中文公开名

def 初值():#空表
    """按标签 id 分桶。"""
    return {'byTab':{}}#初值

def _桶(草稿,标签标识):#取桶
    """无桶则抛。"""
    表=草稿['byTab']#表
    if 标签标识 not in 表:#无
        raise KeyError('ui-deliverables: no review state for tab "'+str(标签标识)+'"')#缺
    return 表[标签标识]#桶

def 已导航(草稿,标签标识,修订,下标):#应用导航
    """首次建桶，之后改下标与修订。"""
    表=草稿['byTab']#表
    if 标签标识 not in 表:#首导航
        表[标签标识]={'index':下标,'split':False,'wrap':False,'navigated':修订}#建
    else:#已有
        桶=表[标签标识]#桶
        桶['index']=下标#下标
        桶['navigated']=修订#修订

def 已选(草稿,标签标识,下标):#选手动文件
    """改展示下标。"""
    _桶(草稿,标签标识)['index']=下标#写

def 切换左右(草稿,标签标识):#翻转 split
    """单栏↔左右。"""
    桶=_桶(草稿,标签标识)#桶
    桶['split']=not 桶['split']#翻

def 切换换行(草稿,标签标识):#翻转 wrap
    """换行开关。"""
    桶=_桶(草稿,标签标识)#桶
    桶['wrap']=not 桶['wrap']#翻

def 遗忘(草稿,标签标识):#标签结束
    """丢掉该桶。"""
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}#过滤

def 创建审阅存储():#声明 store
    """登记为独占 store，每会话一实例。"""
    return {#规格
        'init':初值,#初值
        'actions':{#动作
            'navigated':已导航,#导航
            'selected':已选,#选择
            'toggledSplit':切换左右,#左右
            'toggledWrap':切换换行,#换行
            'forget':遗忘,#遗忘
        },#动作结束
    }#规格结束
