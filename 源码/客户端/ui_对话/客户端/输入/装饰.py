"""草稿装饰纯核心：芯片、认领令牌、纯文本引用、幽灵提示。

对齐上游 `ui-conversation/src/client/input/decorations.ts`。公开面仅中文名。
零 DOM——骨架渲染这些指令。状态与词表为 dict。
"""
import re#扫描纯文本引用

__all__=['扫描文本引用','派生装饰','空词表','惰性装饰']#仅中文公开名

文本引用正则=re.compile(r'(^|\s)([/@])([\w-]+)',re.ASCII)#触发符加名字
空词表={}#空的 / 与 @ 词表
惰性装饰={'token':None,'chips':[],'textRefs':[],'hint':None}#无会话空装饰

def 扫描文本引用(草稿,词表=None):
    """词边界：触发符须在行首或空白后；名字须是词表精确成员。"""
    if 词表 is None:#缺省
        词表=空词表#空
    if len(词表)==0 or 草稿=='':#无词表或空草稿；判 length
        return []#无区间
    出=[]#累积
    for 匹配 in 文本引用正则.finditer(草稿):#逐候选
        触发=匹配.group(2)#触发符
        名=匹配.group(3)#名字
        if 名 is None:#无
            名=''#空
        名表=词表[触发] if 触发 in 词表 else None#该触发符词表
        if 名表 is not None and 名 in 名表:#精确成员
            前=匹配.group(1)#前导
            前长=len(前) if 前 is not None else 0#跳过前导空白
            起点=匹配.start()+前长#起点
            出.append({'start':起点,'end':起点+1+len(名),'trigger':触发})#区间
    return 出#草稿顺序

def 派生装饰(状态,词表=None):
    """令牌范围 + 芯片指令 + 纯文本引用 + 幽灵提示。状态为 dict。"""
    if 词表 is None:#缺省
        词表=空词表#空
    草稿=状态['draft'] if 状态 is not None and 'draft' in 状态 and 状态['draft'] is not None else ''#草稿
    认领=状态['claim'] if 状态 is not None and 'claim' in 状态 else None#认领
    相位=状态['phase'] if 状态 is not None and 'phase' in 状态 else None#相位
    出现表=状态['occurrences'] if 状态 is not None and 'occurrences' in 状态 and 状态['occurrences'] is not None else []#出现
    令牌=认领['token'] if 认领 is not None and 'token' in 认领 and 认领['token'] is not None else ''#令牌串
    提示=认领['hint'] if 认领 is not None and 'hint' in 认领 else None#提示
    认领中=(相位 in ('claimed','submitting')) and 认领 is not None and 令牌!='' and 草稿.startswith(令牌)#监视
    令牌范围={'start':0,'end':len(令牌)} if 认领中 is True else None#高亮
    芯片=[]#指令
    for 项 in 出现表:#逐出现
        芯片.append({#指令
            'occurrenceId':项['occurrenceId'] if 'occurrenceId' in 项 else None,#身份
            'offset':项['offset'] if 'offset' in 项 else None,#偏移
            'label':项['label'] if 'label' in 项 else None,#标签
            'invalid':项['invalid'] is True if 'invalid' in 项 else False,#仅显式 true
        })#结束
    幽灵=None#缺省无
    if 认领中 is True and 提示 is not None and 草稿[len(令牌):].strip()=='':#参数全空白
        幽灵=提示#展示
    return {'token':令牌范围,'chips':芯片,'textRefs':扫描文本引用(草稿,词表),'hint':幽灵}#四件
