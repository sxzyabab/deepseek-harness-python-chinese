"""源后端使用的、与界域无关的脚本元数据。

对齐上游 `shared/cdp/sources.ts`。公开面仅中文名。
"""
__all__=['运行时脚本']#仅中文公开名

class 运行时脚本:#运行时脚本
    """界域源目录中可见的一个脚本。"""
    def __init__(自身,scriptKey,url,hash,startLine,startColumn,endLine,endColumn,buildId=None,sourceMapUrl=None,executionContextId=None,isModule=None,length=None):#构造
        """保存脚本元数据字段。"""
        自身.scriptKey=scriptKey#脚本键
        自身.url=url#源URL
        自身.hash=hash#内容哈希
        自身.buildId=buildId#构建标识
        自身.sourceMapUrl=sourceMapUrl#source map URL
        自身.startLine=startLine#起始行
        自身.startColumn=startColumn#起始列
        自身.endLine=endLine#结束行
        自身.endColumn=endColumn#结束列
        自身.executionContextId=executionContextId#执行上下文id
        自身.isModule=isModule#是否模块
        自身.length=length#长度
