from ..约定.槽 import 对话错误
import json

__all__=['会话组注册表']

class 会话组注册表:
    """每个目标一份分组定义；登记不实例化其构建器。"""
    def __init__(自身,上下文,视图):
        """视图为已登记目标构建器定义表。"""
        自身.上下文=上下文
        自身.视图=视图
        自身.定义表={}

    def 条目表(自身):
        """已登记分组定义。"""
        return list(自身.定义表.values())

    def 登记(自身,定义):
        """为已有目标登记分组规则；返回副作用拥有的幂等拆除器。定义为 dict。"""
        目标=定义['target']
        已有目标=False
        for 视图 in 自身.视图.entries():
            if 视图['target']==目标:
                已有目标=True
                break
        if not 已有目标:
            raise 对话错误('conversation group target "'+目标+'" is not registered')
        if 目标 in 自身.定义表:
            raise 对话错误('conversation group target "'+目标+'" is already registered')
        def 效应():
            """写入表；拆除时删除。"""
            自身.定义表[目标]=定义
            def 拆除():
                """幂等摘掉本次登记。"""
                if 目标 in 自身.定义表 and 自身.定义表[目标] is 定义:
                    del 自身.定义表[目标]
            return 拆除
        return 自身.上下文.副作用(效应,'uiConversation.groups.register('+json.dumps(目标,ensure_ascii=False,separators=(',',':'),allow_nan=False)+')')

    def 按目标(自身,目标):
        """查找一项目标的分组规则。"""
        return 自身.定义表[目标] if 目标 in 自身.定义表 else None
