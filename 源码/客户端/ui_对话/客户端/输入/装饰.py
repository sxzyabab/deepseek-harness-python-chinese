"""草稿装饰纯核心：芯片、认领令牌、纯文本引用与幽灵提示。

对齐上游 `ui-conversation/src/client/input/decorations.ts`。公开面仅中文名。
零 DOM——骨架渲染这些指令。
"""
import re#扫描纯文本引用

__all__=['扫描文本引用','派生装饰','空词表','惰性装饰']#仅中文公开名

文本引用正则=re.compile(r'(^|\s)([/@])([\w-]+)')#触发符加名字

空词表={}#空的 / 与 @ 词表

惰性装饰={'token':None,'chips':[],'textRefs':[],'hint':None}#无会话空装饰

def 扫描文本引用(草稿,词表=None):#扫描草稿中的纯文本引用
    """词边界：触发符须在行首或空白后；名字须是词表精确成员。"""
    词表=词表 or 空词表#缺省空
    if not 词表 or 草稿=='':#无词表或空草稿
        return []#无区间
    出=[]#累积
    for 匹配 in 文本引用正则.finditer(草稿):#逐候选
        触发=匹配.group(2)#触发符
        名=匹配.group(3) or ''#名字
        名表=词表.get(触发)#该触发符词表
        if 名表 is not None and 名 in 名表:#精确成员
            起点=匹配.start()+len(匹配.group(1) or '')#跳过前导空白
            出.append({'start':起点,'end':起点+1+len(名),'trigger':触发})#区间
    return 出#草稿顺序

def 派生装饰(状态,词表=None):#从输入状态推导镜像层装饰
    """令牌范围 + 芯片指令 + 纯文本引用 + 幽灵提示。"""
    词表=词表 or 空词表#缺省
    草稿=状态.get('draft','') if isinstance(状态,dict) else getattr(状态,'draft','')#草稿
    认领=状态.get('claim') if isinstance(状态,dict) else getattr(状态,'claim',None)#认领
    相位=状态.get('phase') if isinstance(状态,dict) else getattr(状态,'phase',None)#相位
    出现表=状态.get('occurrences') if isinstance(状态,dict) else getattr(状态,'occurrences',None)#出现
    出现表=出现表 or []#缺省空
    令牌=认领.get('token') if isinstance(认领,dict) else getattr(认领,'token',None) if 认领 else None#令牌串
    提示=认领.get('hint') if isinstance(认领,dict) else getattr(认领,'hint',None) if 认领 else None#提示
    认领中=(相位 in ('claimed','submitting')) and 认领 is not None and 令牌 and 草稿.startswith(令牌)#监视
    令牌范围={'start':0,'end':len(令牌)} if 认领中 else None#高亮
    芯片=[]#指令
    for 项 in 出现表:#逐出现
        if isinstance(项,dict):#映射
            芯片.append({#指令
                'occurrenceId':项.get('occurrenceId'),#身份
                'offset':项.get('offset'),#偏移
                'label':项.get('label'),#标签
                'invalid':项.get('invalid') is True,#仅显式 true
            })#结束
        else:#对象
            芯片.append({#指令
                'occurrenceId':getattr(项,'occurrenceId',None),#身份
                'offset':getattr(项,'offset',None),#偏移
                'label':getattr(项,'label',None),#标签
                'invalid':getattr(项,'invalid',None) is True,#无效
            })#结束
    幽灵=None#缺省无
    if 认领中 and 提示 is not None and 草稿[len(令牌):].strip()=='':#参数全空白
        幽灵=提示#展示
    return {'token':令牌范围,'chips':芯片,'textRefs':扫描文本引用(草稿,词表),'hint':幽灵}#四件
