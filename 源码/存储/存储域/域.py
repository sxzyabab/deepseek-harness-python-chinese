"""一个已打开域的运行时：权威内存状态、单条写链与变更事件发射。"""
import asyncio#写链
from .错误 import 域错误#域错误
__all__=['域实现','键值表','域全局']#仅中文公开名

class 键值表:#表句柄
    """一张已声明表的句柄。"""
    def __init__(自身,宿主,表名,记录):#构造表句柄
        自身._宿主=宿主#域宿主
        自身._表名=表名#表名
        自身._记录=记录#内存记录
    def get(自身,键):#读记录
        自身._宿主._断言可读()#关闭后拒绝
        return 自身._记录.get(键)#从内存取
    def entries(自身):#快照条目
        自身._宿主._断言可读()#关闭后拒绝
        return list(自身._记录.items())#拷贝后迭代
    def keys(自身):#快照键
        自身._宿主._断言可读()#关闭后拒绝
        return list(自身._记录.keys())#拷贝后迭代
    @property
    def size(自身):#记录数
        自身._宿主._断言可读()#关闭后拒绝
        return len(自身._记录)#dict 大小
    async def put(自身,键,值):#耐久写入
        async def 作业():#一次 put
            await 自身._宿主._单元.putRecord(自身._表名,键,值)#先耐久
            自身._记录[键]=值#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':自身._表名,'key':键,'operation':'put','value':值})#发事件
        await 自身._宿主._入队(作业)#上写链
    async def delete(自身,键):#耐久删除
        async def 作业():#一次 delete
            if 键 not in 自身._记录:#链槽上已不存在
                return False#无写无事件
            await 自身._宿主._单元.deleteRecord(自身._表名,键)#先耐久
            del 自身._记录[键]#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':自身._表名,'key':键,'operation':'deleted'})#发删除事件
            return True#确实删了
        return await 自身._宿主._入队(作业)#上写链
    async def update(自身,键,函数):#原子读改写
        async def 作业():#一次 update
            if 键 not in 自身._记录:#缺失键
                raise 域错误('missing-key',f"domain '{自身._宿主.name}' table '{自身._表名}' has no record '{键}' to update")#missing-key
            下一条=函数(自身._记录[键])#纯变换
            await 自身._宿主._单元.putRecord(自身._表名,键,下一条)#先耐久
            自身._记录[键]=下一条#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':自身._表名,'key':键,'operation':'put','value':下一条})#发事件
            return 下一条#返回新记录
        return await 自身._宿主._入队(作业)#上写链

class 域全局:#全局句柄
    """域全局单例的句柄。"""
    def __init__(自身,宿主):#构造全局句柄
        自身._宿主=宿主#域宿主
    def get(自身):#读全局
        自身._宿主._断言可读()#关闭后拒绝
        return 自身._宿主._全局值#返回内存值
    async def set(自身,值):#写全局
        async def 作业():#一次全局写
            await 自身._宿主._单元.setGlobal(值)#先耐久
            自身._宿主._全局值=值#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':'','key':'','operation':'put','value':值})#发事件
        await 自身._宿主._入队(作业)#上写链

class 域实现:#域实现
    """`Domain` 接口背后的唯一域实现。"""
    def __init__(自身,上下文对象,spec,单元,记录,全局值,关闭钩子):#构造已打开域
        自身.name=spec['name']#记下域名
        自身._上下文=上下文对象#发出变更的上下文
        自身._单元=单元#后端单元
        自身._全局值=全局值#全局初值
        自身._关闭钩子=关闭钩子#关闭钩子
        自身._链=asyncio.Future()#写链尾
        自身._链.set_result(None)#初始已决议
        自身._正在拆除=False#正在拆除
        自身._已关闭=False#已完全关闭
        自身._拆除=None#关闭承诺
        自身._表={}#表句柄
        for 表名,表记录 in 记录.items():#每张表
            自身._表[表名]=键值表(自身,表名,表记录)#构造表句柄
        if spec.get('global') is not None:#有全局槽
            setattr(自身,'global',域全局(自身))#全局句柄；避开 global 关键字赋值
        else:#无全局
            setattr(自身,'global',None)#无全局句柄
    def table(自身,名称):#取表句柄
        表=自身._表.get(名称)#查表
        if 表 is None:#未声明
            raise Exception(f"domain '{自身.name}' declares no table '{名称}'")#调用方错误
        return 表#返回句柄
    async def close(自身):#关闭域
        if 自身._拆除 is None:#首次关闭
            自身._拆除=asyncio.ensure_future(自身._执行关闭())#共享拆除
        await 自身._拆除#等拆除完成
    async def _执行关闭(自身):#实际关闭
        自身._正在拆除=True#拒绝新写
        await 自身._链#排空写链
        await 自身._单元.close()#关后端单元
        自身._已关闭=True#标记完全关闭
        自身._关闭钩子()#腾出域名
    def _发变更(自身,变更):#发出域变更
        try:#派发
            自身._上下文.emit('domain/changed',变更)#发出事件
        except Exception as 错误:#监听器同步抛错
            自身._上下文.logger.warn(f"domain '{自身.name}': domain/changed listener failed: {错误}")#记警告
    async def _入队(自身,作业):#入队写任务
        if 自身._正在拆除:#正在或已经拆除
            raise 域错误('closed',f"domain '{自身.name}' is closed")#拒绝新写
        前=自身._链#当前链尾
        async def _串联():#等前序再跑
            await 前#等前序
            return await 作业()#跑本作业
        结果=asyncio.ensure_future(_串联())#本作业承诺
        自身._链=asyncio.ensure_future(结果)#更新链尾
        return await 结果#等本作业
    def _断言可读(自身):#断言可读
        if 自身._已关闭:#完全关闭
            raise 域错误('closed',f"domain '{自身.name}' is closed")#拒绝读
