import re#纯文本引用扫描

__all__=['扫描文本引用','派生装饰','惰性装饰','空词表']#仅中文公开名

文本引用正则=re.compile(r'(^|\s)([/@])([\w-]+)',re.ASCII)#触发符+名字
空词表={}#缺省无 / @ 词表
惰性装饰={'token':None,'chips':[],'textRefs':[],'hint':None}#无会话装饰

def 扫描文本引用(草稿,词表=None):
    """词边界：行首或空白后的触发符；名字须在词表精确命中。"""
    if 词表 is None:#缺省
        词表=空词表#空
    if len(词表)==0 or 草稿=='':#无
        return []#空
    出=[]#命中
    for 匹配 in 文本引用正则.finditer(草稿):#逐候选
        触发=匹配.group(2)#触发符
        名=匹配.group(3)#名字
        if 名 is None:#无
            名=''#空
        表=词表[触发] if 触发 in 词表 else None#该触发词表
        if 表 is not None and 名 in 表:#精确成员
            前=匹配.group(1)#空白
            前长=len(前) if 前 is not None else 0#跳过空白
            起点=匹配.start()+前长#起点
            出.append({'start':起点,'end':起点+1+len(名),'trigger':触发})#区间
    return 出#顺序

def 派生装饰(状态,词表=None):
    """令牌范围、芯片、文本引用、幽灵提示。"""
    if 词表 is None:#缺省
        词表=空词表#空
    草稿=状态['draft'] if 状态 is not None and 'draft' in 状态 and 状态['draft'] is not None else ''#草稿
    认领=状态['claim'] if 状态 is not None and 'claim' in 状态 else None#认领
    相位=状态['phase'] if 状态 is not None and 'phase' in 状态 else None#相位
    出现表=状态['occurrences'] if 状态 is not None and 'occurrences' in 状态 and 状态['occurrences'] is not None else []#出现表
    令牌文=认领['token'] if 认领 is not None and 'token' in 认领 and 认领['token'] is not None else ''#令牌文
    认领活=(相位 in ('claimed','submitting')) and 认领 is not None and 草稿.startswith(令牌文)#前缀监视
    令牌={'start':0,'end':len(令牌文)} if 认领活 is True else None#高亮
    芯片=[]#指令
    for 项 in 出现表:#投影
        芯片.append({#芯片
            'occurrenceId':项['occurrenceId'] if 'occurrenceId' in 项 else None,#身份
            'offset':项['offset'] if 'offset' in 项 else None,#偏移
            'label':项['label'] if 'label' in 项 else None,#标签
            'invalid':项['invalid'] is True if 'invalid' in 项 else False,#显式无效
        })#结束
    提示=None#幽灵
    if 认领活 is True:#仍认领
        提示文=认领['hint'] if 'hint' in 认领 else None#提示
        尾=草稿[len(令牌文):].strip()#令牌后
        if 提示文 is not None and 尾=='':#参数空白
            提示=提示文#展示
    return {'token':令牌,'chips':芯片,'textRefs':扫描文本引用(草稿,词表),'hint':提示}#四件
