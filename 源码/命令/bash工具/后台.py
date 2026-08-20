"""后台 bash 进程句柄的通用任务适配。对齐上游 `tool-bash/src/background.ts`。公开面仅中文名。"""

__all__=['进程结果']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 进程结果(进程):#映射后台进程结果
    """把已结算的后台进程映射到通用任务结果词。

    `killed` 仍是 killed（详情为已知信号），其余为带退出码详情的 completed。
    非零命令退出只报告、不算失败，与前台渲染一致。
    """
    if 取字段(进程,'status')=='killed':#被杀死
        信号=取字段(进程,'signal')#终止信号
        if 信号 is not None:#有信号
            return {'status':'killed','detail':'signal: '+str(信号)}#写入信号
        return {'status':'killed','detail':'killed before exit'}#提前杀死
    退出码=取字段(进程,'exitCode')#退出码
    if 退出码 is None:#尚未记下则按 0
        退出码=0#默认 0
    return {'status':'completed','detail':'exit code: '+str(退出码)}#其余一律 completed
