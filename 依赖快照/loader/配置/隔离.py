"""按条目或标签隔离服务实现。"""
import cordis

class 原型字典(dict):
    """用 `_原型` 模拟 Object.create 的自有键与原型链查找。"""
    def __init__(自身,原型=None):
        """空自有键，缺失时落到原型。"""
        dict.__init__(自身)#空表
        自身._原型=原型#原型对象

    def __getitem__(自身,键):
        """先自有键，再原型链。"""
        if dict.__contains__(自身,键):
            return dict.__getitem__(自身,键)#自有
        if 自身._原型 is not None:
            return 自身._原型[键]#原型
        raise KeyError(键)#没有

    def __contains__(自身,键):
        """自有键或原型链上有该键。"""
        if dict.__contains__(自身,键):
            return True#自有
        return 自身._原型 is not None and 键 in 自身._原型#原型

def 交换(目标,源=None):
    """清空目标自有键，再把源的自有键拷进去。"""
    for 键 in list(dict.keys(目标)):
        dict.__delitem__(目标,键)#删自有键
    if 源 is None:
        源={}#source || {}
    for 键 in dict.keys(源):
        目标[键]=源[键]#拷自有键

class 隔离符号:
    """隔离表里使用的唯一标签。"""
    def __init__(自身,名称):
        """保存调试名。"""
        自身.名称=名称#Symbol description

    def __repr__(自身):
        """检查器显示为 Symbol(名称)。"""
        return 'Symbol('+自身.名称+')'#展示

class 领域:
    """按条目或标签隔离服务实现的符号域。"""
    def __init__(自身):
        """空存储。"""
        自身.store={}#键到符号

    def 访问(自身,键,创建=False):
        """取出或按需创建该键的隔离符号。"""
        if 创建:
            if 键 not in 自身.store:
                自身.store[键]=隔离符号(键+自身.后缀)#create 则写入
            return 自身.store[键]#已有或新建
        if 键 in 自身.store:
            return 自身.store[键]#已有
        return 隔离符号(键+自身.后缀)#不写入的临时符号

    def 删除(自身,键):
        """删掉该键的隔离符号。"""
        自身.store.pop(键,None)#删除

    @property
    def size(自身):
        """存储中的键数量。"""
        return len(自身.store)#Object.keys length

    @property
    def 后缀(自身):
        """符号名后缀，由子类提供。"""
        raise NotImplementedError#abstract

class 本地领域(领域):
    """条目本地隔离域。"""
    def __init__(自身,条目对象):
        """绑到条目。"""
        领域.__init__(自身)#空存储
        自身.entry=条目对象#所属条目

    @property
    def 后缀(自身):
        """#id。"""
        return '#'+str(自身.entry.options.get('id'))##id

class 全局领域(领域):
    """同标签条目共享的隔离域。"""
    def __init__(自身,label):
        """保存标签。"""
        领域.__init__(自身)#空存储
        自身.label=label#共享标签

    @property
    def 后缀(自身):
        """@label。"""
        return '@'+str(自身.label)#@label

def 隔离(ctx):
    """安装应用 intercept / isolate 条目选项的加载器钩子。"""
    领域表={}#标签到全局域
    分隔符表={}#服务名到分隔符

    def 访问(条目对象,名称,创建=False):
        """按 isolate 选项解析该服务名的隔离符号。"""
        标签=(条目对象.options.get('isolate') or {}).get(名称)#true 或标签
        if not 标签:
            return None#未隔离
        if 标签 is True:
            领域对象=getattr(条目对象,'realm',None)#本地域
            if 领域对象 is None:
                领域对象=本地领域(条目对象)#新建
                条目对象.realm=领域对象#挂上
        elif 创建:
            领域对象=领域表.get(标签)#全局域
            if 领域对象 is None:
                领域对象=全局领域(标签)#新建
                领域表[标签]=领域对象#登记
        else:
            领域对象=领域表.get(标签)#已有全局域
        if 领域对象:
            return 领域对象.访问(名称,创建)#取符号
        return None#没有域

    def 条目初始化(条目对象):
        """为条目上下文建立带原型的隔离表与拦截表。"""
        旧拦截=条目对象.ctx.__dict__.get(cordis.上下文.拦截) or {}#当前拦截表
        旧隔离=条目对象.ctx.__dict__.get(cordis.上下文.隔离) or {}#当前隔离表
        条目对象.ctx.__dict__[cordis.上下文.拦截]=原型字典(旧拦截)#Object.create
        条目对象.ctx.__dict__[cordis.上下文.隔离]=原型字典(旧隔离)#Object.create
    ctx.on('loader/entry-init',条目初始化)

    def 补丁上下文(条目对象,下一步):
        """按 isolate/intercept 生成新表、重载光纤并迁移实现。"""
        父隔离=条目对象.parent.ctx.__dict__.get(cordis.上下文.隔离) or {}#父隔离表
        新表=原型字典(父隔离)#Object.create(parent.isolate)
        for 名称 in dict.keys(条目对象.options.get('isolate') or {}):
            新表[名称]=访问(条目对象,名称,True)#本层隔离符号
        差异={}#服务名到符号四元组
        旧表=条目对象.ctx.__dict__.get(cordis.上下文.隔离) or {}#旧隔离表
        合并名称={}#newMap 与 delims 的键
        for 名称 in dict.keys(新表):
            合并名称[名称]=True#新表自有键
        for 名称 in 分隔符表:
            合并名称[名称]=True#分隔符键
        for 名称 in 合并名称:
            新符号=新表[名称] if 名称 in 新表 else None#含原型
            旧符号=旧表[名称] if 名称 in 旧表 else None#含原型
            if 新符号 is 旧符号:
                continue#没变
            分隔符=分隔符表.get(名称)#已有分隔符
            if 分隔符 is None:
                分隔符=隔离符号('delim:'+名称)#新建
                分隔符表[名称]=分隔符#登记
            条目对象.ctx.__dict__[分隔符]=隔离符号(名称+'#'+str(条目对象.id))#本条目旗标
            for 符号 in (旧符号,新符号):
                if not 符号:
                    continue#没有符号
                实现=条目对象.ctx.reflect.存储.get(符号)#按标签取实现
                if not 实现:
                    continue#尚未提供
                光纤=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
                if not 光纤:
                    条目对象.ctx.logger.warn(Exception('expected service '+名称+' to be implemented'))#缺少实现
                    continue#下一项
                旗一=条目对象.ctx.__dict__.get(分隔符)#本条目旗标
                旗二=光纤.ctx.__dict__.get(分隔符)#实现方旗标
                差异[名称]=(旧符号,新符号,旗一,旗二)#记下四元组
                if 旗一 is not 旗二:
                    break#旗标不同则不再看第二个符号
        隔离表=条目对象.ctx.__dict__[cordis.上下文.隔离]#当前隔离表
        拦截表=条目对象.ctx.__dict__[cordis.上下文.拦截]#当前拦截表
        if isinstance(隔离表,原型字典):
            隔离表._原型=条目对象.parent.ctx.__dict__.get(cordis.上下文.隔离)#setPrototypeOf isolate
        if isinstance(拦截表,原型字典):
            拦截表._原型=条目对象.parent.ctx.__dict__.get(cordis.上下文.拦截)#setPrototypeOf intercept
        交换(隔离表,新表)#换上新隔离自有键
        交换(拦截表,条目对象.options.get('intercept'))#换上拦截配置
        下一步()#reload fiber
        存储=条目对象.ctx.reflect.存储#实现存储
        for 符号1,符号2,旗1,旗2 in 差异.values():
            if 旗1 is 旗2 and 存储.get(符号1) and not 存储.get(符号2):
                存储[符号2]=存储[符号1]#迁到新标签
                存储.pop(符号1,None)#删旧标签
        def 过滤器(上下文对象,名称):
            """同一隔离符号且旗标相对实现方发生变化。"""
            符号1,符号2,旗1,旗2=差异[名称]#四元组
            隔离映射=上下文对象.__dict__.get(cordis.上下文.隔离) or {}#对方隔离表
            符号3=隔离映射[名称] if 名称 in 隔离映射 else None#对方符号
            旗3=上下文对象.__dict__.get(分隔符表[名称])#对方旗标
            return (符号1 is 符号3 or 符号2 is 符号3) and (旗1 is 旗3)!=(旗1 is 旗2)#命中条件
        ctx.reflect.通知(list(差异.keys()),过滤器)#刷新依赖方
        for 名称 in 分隔符表:
            if 名称 not in dict.keys(新表):
                条目对象.ctx.__dict__.pop(分隔符表[名称],None)#清掉多余旗标
    ctx.on('loader/patch-context',补丁上下文)

    def 部分拆除(条目对象,遗留,活动):
        """全局域失去引用时回收符号。"""
        for 名称,标签 in (遗留.get('isolate') or {}).items():
            if 标签 is True:
                continue#本地域不走全局回收
            if 活动 and (条目对象.options.get('isolate') or {}).get(名称) is 标签:
                continue#仍在用同一标签
            领域对象=领域表.get(标签)#全局域
            if not 领域对象:
                continue#没有该域
            for 条目 in ctx.loader.条目们():
                if (条目.options.get('isolate') or {}).get(名称)==领域对象.label:
                    return#仍有引用则整段返回
            领域对象.删除(名称)#去掉该服务键
            if not 领域对象.size:
                领域表.pop(领域对象.label,None)#空域删除
    ctx.on('loader/partial-dispose',部分拆除)

Realm=领域#英文别名
LocalRealm=本地领域#英文别名
GlobalRealm=全局领域#英文别名
isolate=隔离#英文别名
领域.access=领域.访问#英文别名
领域.delete=领域.删除#英文别名
领域.suffix=领域.后缀#英文别名
本地领域.suffix=本地领域.后缀#英文别名
全局领域.suffix=全局领域.后缀#英文别名
