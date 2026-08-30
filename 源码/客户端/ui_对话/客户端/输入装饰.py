"""草稿装饰纯核心：芯片、认领令牌、纯文本引用、幽灵提示。

对齐上游 `ui-conversation/src/client/input/decorations.ts`。公开面仅中文名。
零 React — 骨架渲染这些指令。
"""
import re#纯文本引用扫描

__all__=['扫描文本引用','派生装饰','惰性装饰','空词表']#仅中文公开名

文本引用正则=re.compile(r'(^|\s)([/@])([\w-]+)')#触发符+名字
空词表={}#缺省无 / @ 词表
惰性装饰={'token':None,'chips':[],'textRefs':[],'hint':None}#无会话装饰

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 扫描文本引用(草稿,词表=None):#扫描纯文本引用
    """词边界：行首或空白后的触发符；名字须在词表精确命中。"""
    if 词表 is None:#缺省
        词表=空词表#空
    if not 词表 or 草稿=='':#无
        return []#空
    出=[]#命中
    for 匹配 in 文本引用正则.finditer(草稿):#逐候选
        触发=匹配.group(2)#触发符
        名=匹配.group(3) or ''#名字
        表=词表.get(触发) if isinstance(词表,dict) else None#该触发词表
        if 表 is None and hasattr(词表,'get'):#Map 形
            表=词表.get(触发)#取
        if 表 is not None and 名 in 表:#精确成员
            起点=匹配.start()+len(匹配.group(1) or '')#跳过空白
            出.append({'start':起点,'end':起点+1+len(名),'trigger':触发})#区间
    return 出#顺序

def 派生装饰(状态,词表=None):#从输入状态推导镜像装饰
    """令牌范围、芯片、文本引用、幽灵提示。"""
    if 词表 is None:#缺省
        词表=空词表#空
    草稿=取字段(状态,'draft') or ''#草稿
    认领=取字段(状态,'claim')#认领
    相位=取字段(状态,'phase')#相位
    出现们=取字段(状态,'occurrences') or []#出现表
    认领活=(相位 in ('claimed','submitting')) and 认领 is not None and 草稿.startswith(取字段(认领,'token') or '')#前缀监视
    令牌={'start':0,'end':len(取字段(认领,'token') or '')} if 认领活 else None#高亮
    芯片=[]#指令
    for 项 in 出现们:#投影
        芯片.append({#芯片
            'occurrenceId':取字段(项,'occurrenceId'),#身份
            'offset':取字段(项,'offset'),#偏移
            'label':取字段(项,'label'),#标签
            'invalid':取字段(项,'invalid') is True,#显式无效
        })#结束
    提示=None#幽灵
    if 认领活:#仍认领
        提示文=取字段(认领,'hint')#提示
        尾=草稿[len(取字段(认领,'token') or ''):].strip()#令牌后
        if 提示文 is not None and 尾=='':#参数空白
            提示=提示文#展示
    return {'token':令牌,'chips':芯片,'textRefs':扫描文本引用(草稿,词表),'hint':提示}#四件
