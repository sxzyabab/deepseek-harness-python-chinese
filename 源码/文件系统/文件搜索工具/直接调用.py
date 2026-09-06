"""搜索结果溢出时共用的顶层调用事后策略选择。"""

def 已接受直调值(上下文,工具,执行,结果,决策):#判断是否仍可投影本工具的规范值
    """仅当本工具仍拥有一次直接成功的顶层调用、且下游策略未替换任一投影时，返回已接受的规范值。

    @param 上下文 用于解析当前作用域所有者的工具插件上下文
    @param 工具 可能被投影的已注册定义（必须精确匹配）
    @param 执行 已完成的执行身份
    @param 结果 应用事后策略之前的规范结果
    @param 决策 组合后的下游事后策略决策
    @returns 要投影的规范值；必须推迟溢出时为 None
    """
    种类=决策['kind'] if 'kind' in 决策 else None#决策种类
    内容=决策['content'] if 'content' in 决策 else None#已改content
    父=执行['parent'] if 'parent' in 执行 else None#父调用
    执行名=执行['name'] if 'name' in 执行 else None#执行工具名
    智能体=执行['agent'] if 'agent' in 执行 else None#作用域智能体
    是错误=False#默认非错误
    if 'isError' in 结果 and 结果['isError']:#已是错误
        是错误=True#错误结果
    if (种类!='accept'#决策不是接受
        or 内容 is not None#已改 content
        or 'value' in 决策#已改 value
        or 父 is not None#不是顶层调用
        or 执行名!=工具['name']#名字不符
        or 是错误#已是错误
        or 上下文.tools.获取(执行名,智能体) is not 工具):#实时注册表所有者已不是本工具
        return None#推迟溢出
    return 结果['value']#仍由本工具拥有的成功规范值
