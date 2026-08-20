"""搜索结果溢出时共用的顶层调用事后策略选择。"""

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 有自有(对象,键):#对齐 Object.hasOwn
    """对齐 Object.hasOwn。"""
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 键 in 字典#自有

def 已接受直调值(上下文,工具,执行,结果,决策):#判断是否仍可投影本工具的规范值
    """仅当本工具仍拥有一次直接成功的顶层调用、且下游策略未替换任一投影时，返回已接受的规范值。

    @param 上下文 用于解析当前作用域所有者的工具插件上下文
    @param 工具 可能被投影的已注册定义（必须精确匹配）
    @param 执行 已完成的执行身份
    @param 结果 应用事后策略之前的规范结果
    @param 决策 组合后的下游事后策略决策
    @returns 要投影的规范值；必须推迟溢出时为 None
    """
    if (取字段(决策,'kind')!='accept'#决策不是接受
        or 取字段(决策,'content') is not None#已改 content
        or 有自有(决策,'value')#已改 value
        or 取字段(执行,'parent') is not None#不是顶层调用
        or 取字段(执行,'name')!=取字段(工具,'name')#名字不符
        or 取字段(结果,'isError')#已是错误
        or 上下文.tools.get(取字段(执行,'name'),取字段(执行,'agent')) is not 工具):#实时注册表所有者已不是本工具
        return None#推迟溢出
    return 取字段(结果,'value')#仍由本工具拥有的成功规范值
