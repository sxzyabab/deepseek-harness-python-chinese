__all__=['原子字符','作曲器布局','剪贴板偏移的探测偏移','探测点的探测偏移','投影作曲器']#仅中文公开名

原子字符='\uFFFC'#探测投影里一枚芯片占一个对象替换符

def 作曲器布局(编辑器):
    """走一遍作曲器文档，按文档序产出投影段。块与块之间两边投影都插一个换行空隙。"""
    段表=[]#段
    按键={}#叶键 → 段
    子表={}#元素键 → 子键序
    边界={}#元素键 → 探测起止
    探测=''#探测文本
    剪贴板=''#剪贴板文本
    def 推叶(种,节点,探测片,剪贴片):
        """记下一段叶。"""
        nonlocal 探测,剪贴板#写投影
        段={'kind':种,'node':节点,'detectStart':len(探测),'detectLength':len(探测片),'clipboardStart':len(剪贴板),'clipboardLength':len(剪贴片)}#段
        段表.append(段)#收下
        按键[节点.取键()]=段#按键
        探测+=探测片#叠探测
        剪贴板+=剪贴片#叠剪贴
    def 走元素(元素):
        """走一个块元素的子。"""
        起=len(探测)#起点
        孩子们=元素.取子()#子
        子表[元素.取键()]=[孩.取键() for 孩 in 孩子们]#子键
        for 孩 in 孩子们:#各子
            if 孩.是引用芯片() is True:#芯片
                推叶('chip',孩,原子字符,孩.取文本内容())#芯片
            elif 孩.是文本() is True:#文本
                文本=孩.取文本内容()#文本
                推叶('text',孩,文本,文本)#同文
            elif 孩.是换行() is True:#换行节点
                推叶('linebreak',孩,'\n','\n')#换行
            elif 孩.是元素() is True:#嵌套块
                走元素(孩)#再走
        边界[元素.取键()]={'start':起,'end':len(探测)}#内容界，不含空隙
    根=编辑器.取根()#根
    块表=根.取子()#块
    子表[根.取键()]=[块.取键() for 块 in 块表]#根的子
    根起=len(探测)#根起
    下标=0#游标
    while 下标<len(块表):#各块
        块=块表[下标]#本块
        if 下标>0:#块间空隙
            前=块表[下标-1]#前块
            段表.append({'kind':'gap','node':None,'detectStart':len(探测),'detectLength':1,'clipboardStart':len(剪贴板),'clipboardLength':1,'gapBetween':{'before':前.取键(),'after':块.取键()}})#空隙
            探测+='\n'#探测换行
            剪贴板+='\n'#剪贴换行
        if 块.是元素() is True:#块元素
            走元素(块)#走
        下标+=1#前进
    边界[根.取键()]={'start':根起,'end':len(探测)}#根界
    return {'segments':段表,'detectLength':len(探测),'detectText':探测,'clipboardText':剪贴板,'byKey':按键,'children':子表,'bounds':边界}#布局

def 剪贴板偏移的探测偏移(布局,剪贴板偏移):
    """把剪贴板投影偏移折成探测投影孪生偏移。落在芯片展开内的贴到芯片尾沿。"""
    for 段 in 布局['segments']:#各段
        止=段['clipboardStart']+段['clipboardLength']#剪贴止
        if 剪贴板偏移>止:#还在后面
            continue#下一段
        if 剪贴板偏移==止:#恰在段尾
            return 段['detectStart']+段['detectLength']#探测尾
        if 段['kind']=='chip':#芯片内
            return 段['detectStart']+段['detectLength']#贴尾
        return 段['detectStart']+(剪贴板偏移-段['clipboardStart'])#段内平移
    return 布局['detectLength']#文末

def 探测点的探测偏移(布局,点):
    """把选区锚/焦折成探测偏移；未知节点则 None。"""
    if 点['type']=='text':#文本点
        if 点['key'] not in 布局['byKey']:#未知
            return None#缺席
        段=布局['byKey'][点['key']]#段
        return 段['detectStart']+min(点['offset'],段['detectLength'])#夹取
    if 点['key'] not in 布局['children'] or 点['key'] not in 布局['bounds']:#未知元素
        return None#缺席
    孩子们=布局['children'][点['key']]#子键
    元素界=布局['bounds'][点['key']]#界
    if 点['offset']>=len(孩子们):#越过末子
        return 元素界['end']#元素尾
    子键=孩子们[点['offset']]#子
    if 子键 in 布局['byKey']:#叶
        return 布局['byKey'][子键]['detectStart']#叶起
    if 子键 not in 布局['bounds']:#未知块
        return None#缺席
    return 布局['bounds'][子键]['start']#块起

def 投影作曲器(编辑器,标识于):
    """投影作曲器文档与光标。标识于(键) 给出稳定出现 id。"""
    布局=作曲器布局(编辑器)#布局
    出现表=[]#出现
    for 段 in 布局['segments']:#各段
        节点=段['node']#节点
        if 段['kind']!='chip' or 节点 is None or 节点.是引用芯片() is False:#非芯片
            continue#下
        项={'occurrenceId':标识于(节点.取键()),'source':节点.取来源(),'ref':节点.取引用(),'offset':段['clipboardStart'],'length':段['clipboardLength'],'label':节点.取标签(),'clipboardText':节点.取文本内容()}#出现
        外观=节点.取外观()#外观
        if 外观 is not None:#有
            项['appearance']=外观#带上
        if 节点.已无效() is True:#失败旗
            项['invalid']=True#无效
        出现表.append(项)#收下
    选区=编辑器.取选区()#选区
    范围=None#范围
    if 选区 is not None and 选区.是范围选区() is True:#范围选区
        锚=探测点的探测偏移(布局,选区.锚点())#锚
        焦=探测点的探测偏移(布局,选区.焦点())#焦
        if 锚 is not None and 焦 is not None:#都认识
            范围={'start':min(锚,焦),'end':max(锚,焦)}#有序
    光标=None#塌缩光标
    if 范围 is not None and 范围['start']==范围['end']:#塌缩
        光标=范围['start']#光标
    return {'detectText':布局['detectText'],'clipboardText':布局['clipboardText'],'occurrences':出现表,'selection':范围,'caret':光标}#投影
