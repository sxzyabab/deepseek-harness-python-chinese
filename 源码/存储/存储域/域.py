"""一个已打开域的运行时：权威内存状态、单条写链与变更事件发射。"""
import threading#写链互斥
from .错误 import 域错误#域错误
__all__=['域实现','键值表','域全局']#仅中文公开名

class 键值表:#表句柄
    """一张已声明表的句柄。"""
    def __init__(自身,宿主,表名,记录):#构造表句柄
        """记下宿主、表名与内存记录。"""
        自身._宿主=宿主#域宿主
        自身._表名=表名#表名
        自身._记录=记录#内存记录

    def get(自身,键):#读记录
        """读记录。"""
        自身._宿主._断言可读()#关闭后拒绝
        return 自身._记录[键] if 键 in 自身._记录 else None#从内存取

    def entries(自身):#快照条目
        """快照条目。"""
        自身._宿主._断言可读()#关闭后拒绝
        return list(自身._记录.items())#拷贝后迭代

    def keys(自身):#快照键
        """快照键。"""
        自身._宿主._断言可读()#关闭后拒绝
        return list(自身._记录.keys())#拷贝后迭代

    @property#只读属性
    def size(自身):#记录数
        """记录数。"""
        自身._宿主._断言可读()#关闭后拒绝
        return len(自身._记录)#dict 大小

    def put(自身,键,值):#耐久写入
        """耐久写入。"""
        def 作业():#一次 put
            """一次 put。"""
            自身._宿主._单元.putRecord(自身._表名,键,值)#先耐久
            自身._记录[键]=值#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':自身._表名,'key':键,'operation':'put','value':值})#发事件
        自身._宿主._入队(作业)#上写链

    def delete(自身,键):#耐久删除
        """耐久删除。"""
        def 作业():#一次 delete
            """一次 delete。"""
            if 键 not in 自身._记录:#链槽上已不存在
                return False#无写无事件
            自身._宿主._单元.deleteRecord(自身._表名,键)#先耐久
            del 自身._记录[键]#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':自身._表名,'key':键,'operation':'deleted'})#发删除事件
            return True#确实删了
        return 自身._宿主._入队(作业)#上写链

    def update(自身,键,函数):#原子读改写
        """原子读改写。"""
        def 作业():#一次 update
            """一次 update。"""
            if 键 not in 自身._记录:#缺失键
                raise 域错误('missing-key',"domain '"+自身._宿主.name+"' table '"+自身._表名+"' has no record '"+键+"' to update")#missing-key
            下一条=函数(自身._记录[键])#纯变换
            if 下一条 is 自身._记录[键]:#调用方用同一对象表示无变更
                return 下一条#不写盘、不发事件
            自身._宿主._单元.putRecord(自身._表名,键,下一条)#先耐久
            自身._记录[键]=下一条#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':自身._表名,'key':键,'operation':'put','value':下一条})#发事件
            return 下一条#返回新记录
        return 自身._宿主._入队(作业)#上写链

class 域全局:#全局句柄
    """域全局单例的句柄。"""
    def __init__(自身,宿主):#构造全局句柄
        """记下宿主。"""
        自身._宿主=宿主#域宿主

    def get(自身):#读全局
        """读全局。"""
        自身._宿主._断言可读()#关闭后拒绝
        return 自身._宿主._全局值#返回内存值

    def set(自身,值):#写全局
        """写全局。"""
        def 作业():#一次全局写
            """一次全局写。"""
            自身._宿主._单元.setGlobal(值)#先耐久
            自身._宿主._全局值=值#再改内存
            自身._宿主._发变更({'domain':自身._宿主.name,'table':'','key':'','operation':'put','value':值})#发事件
        自身._宿主._入队(作业)#上写链

class 域实现:#域实现
    """`Domain` 接口背后的唯一域实现。"""
    def __init__(自身,上下文,spec,单元,记录,全局值,关闭钩子):#构造已打开域
        """记下上下文、spec、单元、内存表与关闭钩子。spec 是 dict。"""
        自身.name=spec['name']#记下域名
        自身._上下文=上下文#发出变更的上下文
        自身._单元=单元#后端单元
        自身._全局值=全局值#全局初值
        自身._关闭钩子=关闭钩子#关闭钩子
        自身._写锁=threading.Lock()#写链互斥
        自身._正在拆除=False#正在拆除
        自身._已关闭=False#已完全关闭
        自身._表={}#表句柄
        for 表名,表记录 in 记录.items():#每张表
            自身._表[表名]=键值表(自身,表名,表记录)#构造表句柄
        if 'global' in spec and spec['global'] is not None:#有全局槽
            setattr(自身,'global',域全局(自身))#全局句柄；避开 global 关键字赋值
        else:#无全局
            setattr(自身,'global',None)#无全局句柄

    def table(自身,名称):#取表句柄
        """取表句柄。"""
        if 名称 not in 自身._表:#未声明
            raise 域错误('malformed-medium',"domain '"+自身.name+"' declares no table '"+名称+"'")#调用方错误
        return 自身._表[名称]#返回句柄

    def close(自身):#关闭域
        """关闭域；重复关闭为空操作。"""
        with 自身._写锁:#与写入互斥
            if 自身._已关闭:#已关
                return
            自身._正在拆除=True#拒绝新写
            自身._单元.close()#关后端单元
            自身._已关闭=True#标记完全关闭
            自身._关闭钩子()#腾出域名

    def _发变更(自身,变更):#发出域变更
        """发出域变更。"""
        try:#派发
            自身._上下文.广播('domain/changed',变更)#发出事件
        except BaseException as 错误:#监听器同步抛错
            自身._上下文.日志.警告("domain '"+自身.name+"': domain/changed listener failed: "+str(错误))#记警告

    def _入队(自身,作业):#入队写任务
        """串行执行一次写作业。"""
        with 自身._写锁:#单条写链
            if 自身._正在拆除:#正在或已经拆除
                raise 域错误('closed',"domain '"+自身.name+"' is closed")#拒绝新写
            return 作业()#跑本作业

    def _断言可读(自身):#断言可读
        """完全关闭后拒绝读。"""
        if 自身._已关闭:#完全关闭
            raise 域错误('closed',"domain '"+自身.name+"' is closed")#拒绝读
