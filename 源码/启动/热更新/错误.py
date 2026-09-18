"""把 HMR 构建失败记成警告；有源位置时带代码框。"""
__all__=['处理错误']#仅中文公开名

def 是否构建失败(错误):
    """带 errors 列表、且每条都有 text 的错误来自构建工具。"""
    列表=getattr(错误,'errors',None)#构建工具给的错误列表
    if not isinstance(列表,list) or len(列表)==0:#不是构建失败
        return False#否
    for 项 in 列表:#逐条
        if not isinstance(项,dict) or 'text' not in 项 or not isinstance(项['text'],str):#缺 text
            return False#否
    return True#是

def 格式化代码框(源码,行号,列号,消息):
    """按行列拼出带上下文的代码框。"""
    行表=源码.splitlines()#源码逐行
    起始=max(0,行号-2)#上文起点
    结束=min(len(行表),行号+1)#下文终点
    行号宽=len(str(max(结束,1)))#行号列宽
    片段=[]#输出行
    for 下标 in range(起始,结束):#逐行
        是当前行=下标+1==行号#出错的那一行
        片段.append(('>' if 是当前行 else ' ')+' '+str(下标+1).rjust(行号宽)+' | '+行表[下标])#源码行
        if 是当前行:#指针
            片段.append('  '+' '*行号宽+' | '+' '*(max(列号,1)-1)+'^ '+消息)#列指针
    return '\n'.join(片段)#代码框

def 处理错误(上下文,错误):
    """把构建失败记成警告，有源位置的带上代码框。"""
    if not 是否构建失败(错误):#不是构建失败
        上下文.日志.警告(错误)#原样警告
        return#结束
    for 项 in 错误.errors:#逐条
        位置=项['location'] if 'location' in 项 else None#源位置
        if 位置 is None:#无位置
            上下文.日志.警告(项['text'])#只记文本
            continue#下一条
        try:#读源并拼代码框
            with open(位置['file'],'r',encoding='utf-8') as 文件:#打开
                源码=文件.read()#读源码
            代码框=格式化代码框(源码,位置['line'],位置['column'],项['text'])#代码框
            上下文.日志.警告('File: '+位置['file']+':'+str(位置['line'])+':'+str(位置['column'])+'\n'+代码框)#带位置
        except OSError as 原因:#读失败
            上下文.日志.警告(原因)#记下
        except KeyError as 原因:#位置字段残缺
            上下文.日志.警告(原因)#记下
