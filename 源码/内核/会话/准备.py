class 会话准备:
    """一份尚未发表的精确会话，以及让它仍可使用的提供方状态。拆除同步且幂等。"""
    def __init__(自身,会话,选项):
        """记下尚未发表的会话与准备选项。"""
        自身.已释放=False
        自身.会话=会话
        自身._选项=选项

    @staticmethod
    def 创建(会话,选项=None):
        """把一份尚未发表的会话包进一次准备生命周期。"""
        if 选项 is None:
            选项={}
        return 会话准备(会话,选项)

    def 拆除(自身):
        """本准备离开调用方时只释放一次提供方状态。"""
        if 自身.已释放:
            return
        自身.已释放=True
        释放=自身._选项.get('release') if isinstance(自身._选项,dict) else None
        if 释放 is not None:
            释放()

    def __enter__(自身):
        """进入 with 块。"""
        return 自身

    def __exit__(自身,异常类型,异常,回溯):
        """离开 with 块时拆除。"""
        自身.拆除()
        return False

__all__=['会话准备']
