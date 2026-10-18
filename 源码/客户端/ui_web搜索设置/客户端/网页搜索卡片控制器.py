from ...ui_基础界面组件.表单模型 import 设置表单模型,设置数字字段,设置文本字段

__all__=['网页搜索命名空间','网页搜索卡片控制器']

网页搜索命名空间='web-search-deepseek'
默认密钥引用='DEEPSEEK_API_KEY'
密钥字段='apiKey'

def 引用于(快照):
    '本节点名的凭据引用。没写或空串时用提供方默认'
    值=快照.get('value')
    声明=None
    if isinstance(值,dict):
        声明=值.get('apiKeyEnv')
    if isinstance(声明,str) and len(声明)>0:
        return 声明
    return 默认密钥引用

class 网页搜索卡片控制器:
    '把 web-search-deepseek 作用域和凭据域接到本页'
    def __init__(自身,作用域,上下文):
        '绑定接口地址、搜索次数，并把密钥写成附加写入'
        自身.作用域=作用域
        自身.上下文=上下文
        自身.凭据={'ref':'','configured':False,'writable':True}
        自身.表单=设置表单模型(
            作用域,
            [设置文本字段('baseURL'),设置数字字段('maxUses')],
            [{'field':密钥字段,'write':自身.写密钥}],
        )
        自身.存储=自身.表单.绑定(自身.投影)
        自身.退订=作用域.subscribe(自身.读凭据)
        自身.读凭据()

    def 投影(自身):
        '外壳叠上接口地址、搜索次数、密钥草稿和徽章'
        return {
            **自身.表单.外壳(),
            'baseURL':自身.表单.字段('baseURL'),
            'maxUses':自身.表单.字段('maxUses'),
            'apiKey':自身.表单.字段(密钥字段),
            'apiKeyConfigured':自身.凭据['configured'],
            'apiKeyWritable':自身.凭据['writable'],
        }

    def 读凭据(自身):
        '按当前引用询问凭据域。引用已经变了的应答丢掉'
        引用=引用于(自身.作用域.getSnapshot())
        if 引用!=自身.凭据['ref']:
            自身.凭据={'ref':引用,'configured':False,'writable':True}
            自身.存储.set(自身.投影())
        应答=自身.上下文.remote.credentials.describe([引用])
        if not 应答['ok'] or 引用!=引用于(自身.作用域.getSnapshot()):
            return
        视图=应答['value'].get(引用)
        已配=False
        可写=True
        if 视图 is not None:
            if 视图.get('configured') is not None:
                已配=视图['configured']
            if 视图.get('writable') is not None:
                可写=视图['writable']
        if 已配==自身.凭据['configured'] and 可写==自身.凭据['writable']:
            return
        自身.凭据={'ref':引用,'configured':已配,'writable':可写}
        自身.存储.set(自身.投影())

    def 刷新凭据(自身,引用):
        '宿主报告本页正在看的引用变了，再读一次'
        if 引用!=自身.凭据['ref']:
            return
        自身.读凭据()

    def 注入(自身):
        '槽位登记用的快照和表单动作'
        return {'hooks':{'webSearchCard':自身.存储},**自身.表单.动作()}

    def 写密钥(自身,值):
        '写入暂存密钥，再回读宿主现在是否持有密钥'
        自身.上下文.remote.credentials.set(引用于(自身.作用域.getSnapshot()),值)
        自身.读凭据()
        return 自身.凭据['configured']

    def 拆除(自身):
        '释放配置订阅'
        自身.退订()
        自身.表单.拆除()
