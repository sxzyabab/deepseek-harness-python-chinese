from ....客户端.模块 import 客户端 as 模块客户端命名空间#引导行静态命名空间
from ....客户端.模块.客户端 import 创建客户端模块系统#模块系统工厂
from .名册 import 客户端测试运行时错误#本包异常

__all__=['模块包名','装入插件模块','创建进程内模块']#仅中文公开名

模块包名='@deepseek-ai/dsh-client-modules'#模块包名

def 装入插件模块(计划):#装入插件模块
    """把名册每一行解析成插件模块：有提供表用它，否则导入 包名/client。"""
    模块表={}#包名 → 模块
    提供表=计划.提供#行替换
    for 行 in 计划.名册.行表:#逐行
        名=行.包名#包名
        已提供=提供表[名] if 提供表 is not None and 名 in 提供表 else None#计划替换
        if 名==模块包名:#引导行
            if 已提供 is not None:#禁止替换
                raise 客户端测试运行时错误('client-test-runtime: '+模块包名+' is the bootstrap module and cannot be provided')#英文诊断
            模块表[名]=模块客户端命名空间#静态命名空间
            continue#下一行
        模块表[名]=已提供 if 已提供 is not None else 导入客户端(名)#替换或导入
    return 模块表#返回

def 导入客户端(包名):#导入 /client
    """按包名装入 /client 模块。"""
    try:#导入
        return __import__(包名+'.client',fromlist=['client'])#动态导入
    except ImportError as 错误:#失败
        raise 客户端测试运行时错误('client-test-runtime: cannot import '+包名+'/client: '+str(错误),错误)#包一层

def 创建进程内模块(图,模块表):#创建进程内模块
    """在排队工厂上建造生产模块系统，工厂返回已装入的命名空间。"""
    目标={'mode':'queue','pendingQueue':[]}#登记槽
    def 未初始化加载(_登记=None):#未初始化
        """构造完成前的汇。"""
        raise 客户端测试运行时错误('client-test-runtime: module facade is not initialized')#英文诊断
    目标['load']=未初始化加载#未初始化汇
    def 创建系统(选项):#创建系统
        """把排队槽与引导命名空间交给模块系统工厂。"""
        return 创建客户端模块系统(目标,{'id':模块包名,'exports':模块客户端命名空间},选项)#创建
    目标['create']=创建系统#创建口
    for 标识,命名空间 in 模块表.items():#逐个模块
        if 标识==模块包名:#引导行
            continue#跳过
        def 固定工厂(导出=命名空间):#固定工厂
            """返回已装入命名空间。"""
            return 导出#命名空间
        目标['pendingQueue'].append({'id':标识,'factory':固定工厂})#排队工厂
    def 拒绝加载包(网址):#拒绝拉包
        """进程内模块从不拉捆绑。"""
        raise 客户端测试运行时错误('client-test-runtime: in-process modules never load bundles ('+网址+')')#英文诊断
    return 目标['create']({'boot':图,'staticModules':{},'loadBundle':拒绝加载包})#创建并切到 live
