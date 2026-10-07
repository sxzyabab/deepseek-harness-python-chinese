from ..cordis.读取器 import cordis运行时树读取器#树读取器基类

__all__=['创建查询cordis运行时树读取器']#仅中文公开名

def 创建查询cordis运行时树读取器(请求器):#创建查询读取器
    '创建一个通过类型化 Inspector 查询协议获取树的读取器'
    class _读取器(cordis运行时树读取器):#查询适配读取器
        def 获取树(自身):#获取树
            '返回期约，查询结果到达后以整棵树解决'
            def 取出树(结果):#查询结果到达后的回调
                '从查询结果取出 tree 字段'
                return 结果['tree']#树
            return 请求器.请求({'op':'cordis-tree/get'}).然后(取出树)#查询完成后再取树
    return _读取器()#返回结束
