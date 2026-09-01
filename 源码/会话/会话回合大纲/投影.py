"""`turnOutline` 投影单元（对齐上游 session-turn-outline/projection.ts）。"""
提示预览上限=50#导航卡片一行预算
回复预览上限=120#导航卡片至多三行预算
空大纲={'turns':[],'draft':''}#折叠初始状态
__all__=['轮次大纲投影定义','提示预览上限','回复预览上限']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 预览(内容,上限):#空格拼接文本块、折叠空白并截断
    """空格拼接文本块、折叠空白，超出上限时以省略号结尾。"""
    文本=''#累积文本
    未读完=False#是否因块过大而提前停止
    if 内容 is None:#无内容
        return ''#空预览
    for 块 in 内容:#逐块
        类型=取字段(块,'type')#块类型
        if 类型!='text':#只取文本块
            continue#跳过
        if len(文本)>=上限*2:#已够长
            未读完=True#标记未读完
            break#停止
        原文=取字段(块,'text','') or ''#块文本
        裁剪=len(原文)>上限*2#单块是否需截断
        片段=原文[:上限*2] if 裁剪 else 原文#截断片段
        文本=片段 if 文本=='' else 文本+' '+片段#拼接
        if 裁剪:#块过大
            未读完=True#标记
            break#停止
    归一=' '.join(文本.split())#折叠空白
    if len(归一)>上限-1:#超出预算
        return 归一[:上限-1].rstrip()+'…'#截断加省略号
    return 归一+'…' if 未读完 else 归一#未读完也加省略号

def 轮次大纲初始(头=None):#折叠初始状态
    """折叠初始状态。"""
    return {'turns':[],'draft':''}#空大纲

def 轮次大纲应用(状态,事件):#纯折叠 turnOutline
    """纯折叠 turnOutline。"""
    类型=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data',{}) or {}#事件载荷
    序号=取字段(事件,'seq',0)#事件序号
    轮次们=list(状态.get('turns') or [])#已开轮次
    草稿=状态.get('draft','') or ''#开放轮次回复草稿
    if 类型=='turn/start':#开轮边界
        末条=轮次们[-1] if len(轮次们)>0 else None#最新条目
        轮次号=取字段(数据,'turn')#轮次号
        if 末条 is not None and 轮次号 is not None and 轮次号<=末条['turn']:#未推进
            return 状态#保持引用
        return {'turns':[*轮次们,{'turn':轮次号,'seq':序号,'prompt':'','response':''}],'draft':''}#追加条目
    if 类型=='user/message':#人类提示
        来源=取字段(数据,'source',{}) or {}#消息来源
        if 取字段(来源,'kind')!='user':#非用户来源
            return 状态#忽略
        末条=轮次们[-1] if len(轮次们)>0 else None#最新条目
        if 末条 is None or 末条.get('prompt','')!='':#尚无条目或已有预览
            return 状态#保持
        提示=预览(取字段(数据,'content'),提示预览上限)#首条人类提示预览
        if 提示=='':#无合格文本
            return 状态#保持
        return {'turns':[*轮次们[:-1],{**末条,'prompt':提示}],'draft':草稿}#写入提示
    if 类型=='assistant/message':#助手消息
        消息=取字段(数据,'message',{}) or {}#助手消息
        新草稿=预览(取字段(消息,'content'),回复预览上限)#最新文本预览
        if 新草稿=='' or 新草稿==草稿:#无变化
            return 状态#保持
        return {'turns':轮次们,'draft':新草稿}#只改草稿
    if 类型=='turn/end':#轮次结束
        if 草稿=='':#无草稿
            return 状态#保持
        末条=轮次们[-1] if len(轮次们)>0 else None#最新条目
        if 末条 is None or 末条.get('response')==草稿:#已提交
            return {'turns':轮次们,'draft':''}#只清草稿
        return {'turns':[*轮次们[:-1],{**末条,'response':草稿}],'draft':''}#提交回复
    return 状态#其它事件

def 轮次大纲视图(状态):#wire 视图
    """wire 视图投影 turns 数组。"""
    return 状态.get('turns') or []#整值条目数组

轮次大纲投影定义={#注册表单元
    'key':'turnOutline',#投影键
    'stateVersion':2,#状态版本
    'stateSchema':None,#Python 侧不跑 zod
    'init':轮次大纲初始,#初始
    'apply':轮次大纲应用,#折叠
    'wire':{'viewSchema':None,'view':轮次大纲视图},#wire
}#定义结束
