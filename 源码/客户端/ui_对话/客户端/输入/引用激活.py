
__all__=['登记引用激活']#仅中文公开名

def 登记引用激活(编辑器,打开):
    """为原子芯片与可编辑引用令牌安装预览激活。打开(来源,引用)→是否打开；False 保留普通处理。"""
    def 处理点击(事件):
        """左键单击；未折叠选区放行。事件为 dict。"""
        if 事件['target'] is None:#无目标
            return False#放行
        if 事件['button']!=0:#非左键
            return False#放行
        if 事件['detail']>1:#连点
            return False#放行
        选区=编辑器.取选区()#当前选区
        if 选区 is not None and 选区.是范围选区() and 选区.已折叠() is False:#未折叠范围
            return False#放行
        节点=编辑器.从节点取最近(事件['target'])#最近节点
        if 节点 is None:#无
            return False#放行
        if 节点.是引用芯片() is True:#点在芯片
            if 节点.已无效() is True:#无效
                return False#不打开
            外观=节点.取外观()#可选外观
            引用={'ref':节点.取引用()}#引用 id
            if 外观 is not None:#有外观
                引用['appearance']=外观#带上
            return 打开(节点.取来源(),引用) is True#带上来源
        if 节点.是文本引用() is False:#非文本引用
            return False#放行
        return 打开(None,{'ref':节点.取文本()}) is True#无来源，ref 为节点文本
    return 编辑器.登记命令('click',处理点击)#拆除器
