from .解析 import 第一方命令名#第一方定义名

__all__=['内置行面','分区行']#仅中文公开名

分区行名={#各分区行名，使用频次高的在前
    'add':('file','goal','plan','feedback'),#添加区
    'commands':('compact','permission','model','export'),#指令区
}#分区行名结束

宿主面={#第一方名 → 文案键与字形名
    'goal':{'label':'label.goal','description':'description.goal','icon':'IconGoalOutline16'},#目标
    'plan':{'label':'label.plan','description':'description.plan','icon':'IconPlanOutline14'},#计划
    'feedback':{'label':'label.feedback','description':'description.feedback','icon':'IconPaperPlaneOutline14'},#反馈
    'compact':{'label':'label.compact','description':'description.compact','icon':'IconCompactOutline16'},#压缩
    'permission':{'label':'label.permission','description':'description.permission','icon':'IconShieldOutline16'},#权限
    'export':{'label':'label.export','description':'description.export','icon':'IconDownloadOutline16'},#导出
}#宿主面结束

def 内置行面(描述符,翻译):
    """一条目录行的本地化菜单面。其它行返回 None，保留目录说明。描述符为 dict。"""
    名=第一方命令名(描述符)#第一方名
    if 名 is None:#非第一方
        return None#缺席
    面=宿主面[名] if 名 in 宿主面 else None#查面
    if 面 is None:#无面
        return None#缺席
    return {'label':翻译(面['label']),'description':翻译(面['description']),'icon':面['icon']}#译出标签说明并带字形

def 分区行(行表,翻译):
    """空查询菜单：先添加区再指令区；未列入的行按输入顺序收在指令区末尾。行表为 dict 列表。"""
    已列=set(分区行名['add'])|set(分区行名['commands'])#两区已列名
    按名={}#名 → 行
    for 行 in 行表:#建索引
        按名[行['name']]=行#记下
    def 挑出(名表):
        """按名挑出仍可见的行。"""
        选出=[]#缓冲
        for 名 in 名表:#逐名
            if 名 in 按名:#仍可见
                选出.append(按名[名])#收下
        return 选出#行表
    添加=[]#添加区
    for 行 in 挑出(分区行名['add']):#添加区行
        拷=dict(行)#拷
        拷['section']=翻译('section.add')#分区标题
        添加.append(拷)#收下
    指令=[]#指令区
    for 行 in 挑出(分区行名['commands']):#表内指令
        拷=dict(行)#拷
        拷['section']=翻译('section.commands')#分区标题
        指令.append(拷)#收下
    for 行 in 行表:#未列行
        if 行['name'] not in 已列:#表外
            拷=dict(行)#拷
            拷['section']=翻译('section.commands')#收在指令区
            指令.append(拷)#收下
    return 添加+指令#添加区后接指令区
