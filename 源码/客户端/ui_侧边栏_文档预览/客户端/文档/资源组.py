__all__=['资源组']

class 资源组:
    """一份文档预览的文件资源成员与失效。"""
    def __init__(自身,资源,已变):
        """记下共享源与失效回调。"""
        自身.资源=资源
        自身.已变=已变
        自身.成员={}

    def add(自身,地址):
        """订阅一次；初值建立后续变更基线。"""
        if 地址 in 自身.成员:
            return
        源=自身.资源.source(地址)
        前=[None]
        def 观察():
            下一=源.getSnapshot()
            状态=下一.get('status') if isinstance(下一,dict) else None
            if 状态!='live' and 状态!='failed':
                return
            if 状态=='live':
                值=下一.get('value') if isinstance(下一,dict) else None
                版本=None if not isinstance(值,dict) else 值.get('version')
                键='live:'+str(版本)
            else:
                失败=下一.get('failure') if isinstance(下一,dict) else None
                码=None if not isinstance(失败,dict) else 失败.get('code')
                键='failed:'+str(码)
            变了=前[0] is not None and 键!=前[0]
            前[0]=键
            if 变了:
                自身.已变()
        自身.成员[地址]=源.subscribe(观察)
        观察()

    def set(自身,地址表):
        """释放当前文档不再依赖的成员。"""
        留下=set(地址表)
        for 地址 in 留下:
            自身.add(地址)
        for 地址 in list(自身.成员.keys()):
            if 地址 in 留下:
                continue
            释放=自身.成员.pop(地址)
            释放()

    def close(自身):
        """标签结束时释放全部成员。"""
        自身.set(())
