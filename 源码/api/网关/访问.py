'非所有者访问判定要碰到的资源。在查找和 Context 解析之前，从已校验参数读出'

全局资源=({'kind':'global'},)#没有具体资源时只碰到全局

def 读取(读取器,参数,缺席):
    '跑一个读取器。undefined 用缺席；空列表算无效'
    try:#读取器可以抛
        值=读取器(*参数)#展开位置参数
    except Exception:#说不出资源
        return 'invalid'#无效
    if 值 is None:#没给出
        return 缺席#由调用方决定
    if not isinstance(值,list):#单个标识
        return [值]#收成列表
    if len(值)==0:#空列表不许
        return 'invalid'#无效
    return 值#若干标识

def 收集(资源列表,种类,标识列表):
    '把一种资源的标识追加进去。任一畸形则整次无效'
    if 标识列表=='invalid':#已经无效
        return False#失败
    for 标识 in 标识列表:#逐个
        if not isinstance(标识,str) or 标识=='':#必须是非空字符串
            return False#失败
        资源列表.append({'kind':种类,'id':标识})#一条
    return True#这一类过了

def 调用资源(typert,读取器表,描述符,参数,信号):
    '一次调用碰到的资源。无效时返回 None；什么都没碰到时只返回全局'
    来源={}#种类到产出函数，后写的盖住先写的，但种类位置按首次插入
    for 条目 in typert.resources.entries():#默认字段
        种类=条目['kind'] if isinstance(条目,dict) else 条目[0]#种类
        字段=条目['field'] if isinstance(条目,dict) else 条目[1]#字段
        def 取默认(描述符=描述符,参数=参数,字段=字段):
            '默认字段恰好一个标识；数组算无效'
            if any(项['wire']==字段 for 项 in 描述符['parameters']):#顶层参数
                标识=参数.get(字段)#直接取
            else:#否则找第一个对象参数上的字段
                标识=None#没有
                找到=False#是否见过对象
                for 项 in 描述符['parameters']:#按参数顺序
                    值=参数.get(项['wire'])#参数值
                    if not isinstance(值,dict):#不是对象
                        continue#下一个
                    找到=True#见过
                    if 字段 not in 值:#对象上没有这个字段
                        标识=None#缺席
                    else:#有
                        标识=值[字段]#取出
                    break#只用第一个对象
                if not 找到:#没有对象参数
                    标识=None#缺席
            if isinstance(标识,list):#默认字段不许是数组
                return 'invalid'#无效
            if 标识 is None:#没有
                return []#这一类没有
            return [标识]#一个
        来源[种类]=取默认#盖住同一种
    标识表={}#查找与 Context 按种类收集
    def 添加(种类,标识):
        '同一种按出现顺序追加'
        已有=标识表.get(种类)#已有列表
        if 已有 is None:#第一次
            标识表[种类]=[标识]#新建
        else:#已有
            已有.append(标识)#追加
    接收=描述符['invocation']#接收方
    if 接收['kind']=='context':#Context 身份在查找之前
        宿主=typert.contexts.getHost(接收['context'])#宿主适配器
        种类=None if 宿主 is None else 宿主.get('resource')#资源种类
        if 种类 is not None:#声明了种类
            添加(种类,参数.get(接收['wire']))#身份必须出现
    for 项 in 描述符['parameters']:#查找参数按顺序
        if 项.get('lookup') is None:#不是查找
            continue#下一个
        提供方=typert.lookups.get(项['lookup'])#提供方
        种类=None if 提供方 is None else 提供方.get('resource')#种类
        标识=参数.get(项['wire'])#线路值
        if 种类 is not None and 标识 is not None:#省略的可选查找不命名资源
            添加(种类,标识)#记下
    for 种类,标识列表 in 标识表.items():#盖住默认字段
        def 取查找(标识列表=标识列表):
            '这一类的查找标识'
            return 标识列表#已收集
        来源[种类]=取查找#替换
    位置参数=None#读取器共用的位置参数，第一次才组
    for 种类,读取器 in (读取器表 or {}).items():#方法自己的读取器最后盖住
        def 取读取(读取器=读取器):
            '展开成位置参数再读'
            nonlocal 位置参数#共用
            if 位置参数 is None:#还没组
                位置参数=[参数.get(项['wire']) for 项 in 描述符['parameters']]#按描述符顺序
                if 描述符.get('cancellation') is not None:#取消槽
                    位置参数.append(信号)#放在最后
            return 读取(读取器,位置参数,[])#没有则空，不当成全局
        来源[种类]=取读取#替换
    资源=[]#结果
    for 种类,产出 in 来源.items():#按种类位置
        if not 收集(资源,种类,产出()):#任一无效
            return None#整次无效
    if len(资源)==0:#什么都没碰到
        return 全局资源#只有全局
    return 资源#碰到的资源

def 事件资源(读取器表,参数):
    '一条转发通知碰到的资源。读取器返回空则通知无效，而不是全局'
    声明=list((读取器表 or {}).items())#声明的读取器
    if len(声明)==0:#没有读取器，含空表
        return 全局资源#全局
    资源=[]#结果
    for 种类,读取器 in 声明:#每一种都要能命名
        if not 收集(资源,种类,读取(读取器,参数,'invalid')):#缺席也无效
            return None#无效
    return 资源#碰到的资源

__all__=['调用资源','事件资源']#公开名
