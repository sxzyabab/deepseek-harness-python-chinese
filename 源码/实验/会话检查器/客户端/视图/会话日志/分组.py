'Turn 与 Step 的 start/end 区间只补祖先，不发明也不重排日志记录'

__all__=['会话日志分组']

class 会话日志分组:
    '对已加载日志走一遍；缺失的 start 不制造合成表头'
    def __init__(自身):
        '当前打开的 Turn 和 Step'
        自身.回合=None
        自身.步=None

    def 追加(自身,行,事件):
        '把记录放进打开的 Step 或 Turn，end 记录留在最后的子行'
        类型=事件['type'] if isinstance(事件,dict) else 事件.type
        if 类型=='turn/start':
            自身.步=None
            自身.回合={**行,'disclosure':'open'}
            return 自身.回合
        if 类型=='step/start':
            自身.步={**自身._子行(行,自身.回合),'disclosure':'open'}
            return 自身.步
        if 类型=='step/end':
            结果=自身._子行(行,自身.步 if 自身.步 is not None else 自身.回合)
            自身.步=None
            return 结果
        if 类型=='turn/end':
            结果=自身._子行(行,自身.回合)
            自身.步=None
            自身.回合=None
            return 结果
        return 自身._子行(行,自身.步 if 自身.步 is not None else 自身.回合)

    def _子行(自身,行,父):
        '没有父级时保持原行'
        if 父 is None:
            return 行
        return {**行,'parent':父['key'],'depth':父['depth']+1}
