class 补丁解析错误(Exception):#本包异常基类
    '补丁语法非法。消息含原始输入行号，reason 与 lineNumber 供调用方读取'
    def __init__(自身,行号,原因):
        '行号从 1 计，含包装行。原因保持上游英文诊断'
        super().__init__('Invalid patch at line '+str(行号)+': '+原因)#英文诊断
        自身.行号=行号#原始输入行
        自身.原因=原因#如何修正
