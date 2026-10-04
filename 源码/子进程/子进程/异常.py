class 可执行未找到错误(Exception):#可执行查找未找到文件
    '可执行查找完成但没有找到可执行文件'
    def __init__(自身,消息,原因=None):#记下诊断
        '记下提供方查找诊断与可选原始失败'
        super().__init__(消息)#英文诊断
        自身.name='SubprocessExecutableNotFoundError'#错误名
        if 原因 is not None:#有原因
            自身.__cause__=原因#链上原因
