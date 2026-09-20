"""把 HMR 构建失败记成警告；有源位置时带代码框。"""
__all__=['处理错误']

def 是否构建失败(错误):
    """带 errors 列表、且每条都有 text 的错误来自构建工具。"""
    列表=getattr(错误,'errors',None)
    if not isinstance(列表,list) or len(列表)==0:
        return False
    for 项 in 列表:
        if not isinstance(项,dict) or 'text' not in 项 or not isinstance(项['text'],str):
            return False
    return True

def 格式化代码框(源码,行号,列号,消息):
    """按行列拼出带上下文的代码框。"""
    行表=源码.splitlines()
    起始=max(0,行号-2)
    结束=min(len(行表),行号+1)
    行号宽=len(str(max(结束,1)))
    片段=[]
    for 下标 in range(起始,结束):
        是当前行=下标+1==行号
        片段.append(('>' if 是当前行 else ' ')+' '+str(下标+1).rjust(行号宽)+' | '+行表[下标])
        if 是当前行:
            片段.append('  '+' '*行号宽+' | '+' '*(max(列号,1)-1)+'^ '+消息)
    return '\n'.join(片段)

def 处理错误(上下文,错误):
    """把构建失败记成警告，有源位置的带上代码框。"""
    if not 是否构建失败(错误):
        上下文.日志.警告(错误)
        return
    for 项 in 错误.errors:
        位置=项['location'] if 'location' in 项 else None
        if 位置 is None:
            上下文.日志.警告(项['text'])
            continue
        try:
            with open(位置['file'],'r',encoding='utf-8') as 文件:
                源码=文件.read()
            代码框=格式化代码框(源码,位置['line'],位置['column'],项['text'])
            上下文.日志.警告(代码框)
        except OSError as 原因:
            上下文.日志.警告(原因)
        except KeyError as 原因:
            上下文.日志.警告(原因)
