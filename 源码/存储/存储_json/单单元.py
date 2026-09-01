"""一个已打开的 `single` 布局 JSON 单元。"""
import asyncio#在途发布跟踪
from ..存储.错误 import 存储错误#存储错误
from .格式 import 单元状态,序列化,解析#格式
from .原子 import 原子写#原子写
__all__=['打开单单元']#仅中文公开名

class _单单元:#single 布局实现
    def __init__(自身,描述符,路径,状态,关闭回调):#构造
        自身._描述符=描述符#描述符
        自身._路径=路径#文件路径
        自身._状态=状态#权威内存
        自身._关闭回调=关闭回调#释放槽
        自身._已关=False#关闭旗标
        自身._在途=set()#在途发布
    async def loadAll(自身):#读全快照
        自身._断言打开()#已关拒绝
        表={}#投影
        for 表名,记录 in 自身._状态.tables.items():#每张表
            表[表名]=dict(记录)#转 dict
        return {'tables':表,'global':自身._状态.全局值}#快照
    async def putRecord(自身,表,键,值):#写入记录
        自身._断言打开()#已关拒绝
        记录=自身._取表(表)#表记录
        曾有键=键 in 记录#写入前是否有键
        先前=记录.get(键)#先前值
        记录[键]=值#先改内存
        try:#发布
            await 自身._发布()#原子写盘
        except BaseException as 错误:#发布失败
            if 曾有键:#恢复
                记录[键]=先前#写回旧值
            else:#删掉新键
                记录.pop(键,None)#回滚
            raise 错误#再抛
    async def deleteRecord(自身,表,键):#删除记录
        自身._断言打开()#已关拒绝
        记录=自身._取表(表)#表记录
        if 键 not in 记录:#缺失键
            return#幂等
        先前=记录[键]#先前值
        del 记录[键]#先改内存
        try:#发布
            await 自身._发布()#原子写盘
        except BaseException as 错误:#发布失败
            记录[键]=先前#回滚
            raise 错误#再抛
    async def setGlobal(自身,值):#写全局
        自身._断言打开()#已关拒绝
        if not 自身._描述符.hasGlobal:#未声明全局
            raise Exception(f"unit '{自身._描述符.name}' does not declare a global slot")#调用方错误
        先前=自身._状态.全局值#先前全局
        自身._状态.全局值=值#先改内存
        try:#发布
            await 自身._发布()#原子写盘
        except BaseException as 错误:#发布失败
            自身._状态.全局值=先前#回滚
            raise 错误#再抛
    async def close(自身):#关闭单元
        if 自身._已关:#重复关闭
            await asyncio.gather(*[asyncio.ensure_future(自身._等(写)) for 写 in list(自身._在途)],return_exceptions=True)#排空
            return#结束
        自身._已关=True#标记关闭
        await asyncio.gather(*[asyncio.ensure_future(自身._等(写)) for 写 in list(自身._在途)],return_exceptions=True)#排空
        自身._关闭回调()#释放槽
    def _断言打开(自身):#打开守卫
        if 自身._已关:#已关
            raise 存储错误('closed',f"unit '{自身._描述符.name}' is closed")#拒绝
    def _取表(自身,表):#取声明表
        记录=自身._状态.tables.get(表)#查表
        if 记录 is None:#未声明
            raise Exception(f"unit '{自身._描述符.name}' does not declare table '{表}'")#调用方错误
        return 记录#表记录
    async def _发布(自身):#原子发布整文件
        写=asyncio.ensure_future(asyncio.to_thread(原子写,自身._路径,序列化(自身._描述符.name,自身._状态)))#后台写盘
        自身._在途.add(写)#跟踪
        try:#等写完成
            await 写#等结果
        finally:#无论成败摘掉
            自身._在途.discard(写)#摘掉
    async def _等(自身,任务):#等可等待对象
        try:#等
            await 任务#等完成
        except Exception:#跟踪分支吞错
            pass#吞掉

async def 打开单单元(描述符,根目录,关闭回调):#打开 single 单元
    """打开或惰性创建 `<root>/<name>.json`。"""
    import os#路径
    路径=os.path.join(根目录,f'{描述符.name}.json')#单元文件
    文本=None#文件文本
    try:#读已有
        with open(路径,'r',encoding='utf-8') as 文件:#打开读
            文本=文件.read()#读全文
    except FileNotFoundError:#缺失文件
        pass#空单元
    except OSError as 错误:#其它 IO 错
        raise 错误#原样抛
    if 文本 is None:#无文件
        状态=单元状态(描述符.version,None,{表: {} for 表 in 描述符.tables})#空状态
    else:#有文件
        状态=解析(文本,描述符)#解析
    return _单单元(描述符,路径,状态,关闭回调)#返回单元
