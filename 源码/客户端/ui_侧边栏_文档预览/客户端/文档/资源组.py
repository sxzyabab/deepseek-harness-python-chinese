'一个预览标签依赖的文件资源。成员元数据变了就通知正文'
class 资源组:
    '转发成员元数据变化'
    def __init__(自身,资源,已变):
        '资源是共享文件源。已变把所属预览标成过期'
        自身.资源=资源
        自身.已变=已变
        自身.成员={}

    def 添加(自身,地址):
        '订阅一次。初次元数据当作后来变化的基线'
        if 地址 in 自身.成员:
            return
        源=自身.资源.source(地址)
        先前={'值':None,'有过':False}
        def 观察():
            '活着或失败才比较。键变了就通知'
            下个=源.getSnapshot()
            状态=下个['status'] if isinstance(下个,dict) else getattr(下个,'status',None)
            if 状态!='live' and 状态!='failed':
                return
            if 状态=='live':
                值=下个['value'] if isinstance(下个,dict) else getattr(下个,'value',None)
                版本=值['version'] if isinstance(值,dict) and 'version' in 值 else getattr(值,'version',None)
                键='live:'+str(版本)
            else:
                失败=下个['failure'] if isinstance(下个,dict) else getattr(下个,'failure',None)
                码=失败['code'] if isinstance(失败,dict) and 'code' in 失败 else getattr(失败,'code',None)
                键='failed:'+str(码)
            变了=先前['有过'] and 键!=先前['值']
            先前['值']=键
            先前['有过']=True
            if 变了:
                自身.已变()
        自身.成员[地址]=源.subscribe(观察)
        观察()

    def 设置(自身,地址列表):
        '放开当前文档里没有的依赖'
        保留=set(地址列表)
        for 地址 in 保留:
            自身.添加(地址)
        for 地址,释放 in list(自身.成员.items()):
            if 地址 in 保留:
                continue
            del 自身.成员[地址]
            释放()

    def 关闭(自身):
        '标签结束时放开每一个成员'
        自身.设置([])
