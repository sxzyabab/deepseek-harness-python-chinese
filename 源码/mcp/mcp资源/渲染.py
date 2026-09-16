import json#紧凑 JSON

__all__=['渲染资源结果']#仅中文公开名

def 替换二进制(值):#把 blob 字符串换成说明
    """字符串 blob 换成长度说明，其余原样。"""
    if isinstance(值,dict):#对象
        结果={}#输出
        for 键,项 in 值.items():#逐键
            if 键=='blob' and isinstance(项,str):#二进制载荷
                结果[键]='[binary resource: '+str(len(项))+' base64 characters; available to programmatic callers]'#说明
            else:#其余
                结果[键]=替换二进制(项)#递归
        return 结果#对象
    if isinstance(值,list):#数组
        return [替换二进制(项) for 项 in 值]#递归
    return 值#标量

def 渲染资源结果(服务器,值):#给模型看的文本块
    """渲染资源 JSON，原始二进制只留给程序化调用方。"""
    渲染=json.dumps(替换二进制(值),ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON
    return [{'type':'text','text':'MCP server: '+服务器+'\n'+渲染}]#归属文本
