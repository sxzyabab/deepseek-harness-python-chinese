"""一个已打开的 `single` 布局 JSON 单元。"""
import os#路径
from ..存储.错误 import 存储错误#存储错误
from .格式 import 单元状态,序列化,解析#格式
from .原子 import 原子写#原子写
__all__=['打开单单元']#仅中文公开名

class 单单元:#single 布局实现
    """整文件 JSON 单元。"""
    def __init__(自身,描述符,路径,状态,关闭回调):#构造
        """记下描述符、路径、内存状态与关闭回调。"""
        自身._描述符=描述符#描述符
        自身._路径=路径#文件路径
        自身._状态=状态#权威内存
        自身._关闭回调=关闭回调#释放槽
        自身._已关=False#关闭标志

    def loadAll(自身):#读全快照
        """读全快照。"""
        自身._断言打开()#已关拒绝
        表={}#投影
        for 表名,记录 in 自身._状态.tables.items():#每张表
            表[表名]=dict(记录)#转 dict
        return {'tables':表,'global':自身._状态.全局值}#快照

    def putRecord(自身,表,键,值):#写入记录
        """写入记录并原子发布。"""
        自身._断言打开()#已关拒绝
        记录=自身._取表(表)#表记录
        曾有键=键 in 记录#写入前是否有键
        先前=记录[键] if 曾有键 else None#先前值
        记录[键]=值#先改内存
        try:#发布
            自身._发布()#原子写盘
        except BaseException as 错误:#发布失败
            if 曾有键:#恢复
                记录[键]=先前#写回旧值
            else:#删掉新键
                记录.pop(键,None)#回滚
            raise 错误#再抛

    def deleteRecord(自身,表,键):#删除记录
        """删除记录并原子发布。"""
        自身._断言打开()#已关拒绝
        记录=自身._取表(表)#表记录
        if 键 not in 记录:#缺失键
            return#幂等
        先前=记录[键]#先前值
        del 记录[键]#先改内存
        try:#发布
            自身._发布()#原子写盘
        except BaseException as 错误:#发布失败
            记录[键]=先前#回滚
            raise 错误#再抛

    def setGlobal(自身,值):#写全局
        """写全局并原子发布。"""
        自身._断言打开()#已关拒绝
        if not 自身._描述符.hasGlobal:#未声明全局
            raise 存储错误('malformed-medium',"unit '"+自身._描述符.name+"' does not declare a global slot")#调用方错误
        先前=自身._状态.全局值#先前全局
        自身._状态.全局值=值#先改内存
        try:#发布
            自身._发布()#原子写盘
        except BaseException as 错误:#发布失败
            自身._状态.全局值=先前#回滚
            raise 错误#再抛

    def close(自身):#关闭单元
        """关闭单元；重复关闭为空操作。"""
        if 自身._已关:#重复关闭
            return
        自身._已关=True#标记关闭
        自身._关闭回调()#释放槽

    def _断言打开(自身):#打开守卫
        """已关则拒绝。"""
        if 自身._已关:#已关
            raise 存储错误('closed',"unit '"+自身._描述符.name+"' is closed")#拒绝

    def _取表(自身,表):#取声明表
        """取声明表。"""
        if 表 not in 自身._状态.tables:#未声明
            raise 存储错误('malformed-medium',"unit '"+自身._描述符.name+"' does not declare table '"+表+"'")#调用方错误
        return 自身._状态.tables[表]#表记录

    def _发布(自身):#原子发布整文件
        """原子写盘。"""
        原子写(自身._路径,序列化(自身._描述符.name,自身._状态))#同步写盘

def 打开单单元(描述符,根目录,关闭回调):#打开 single 单元
    """打开或惰性创建 `<root>/<name>.json`。"""
    路径=os.path.join(根目录,描述符.name+'.json')#单元文件
    文本=None#文件文本
    try:#读已有
        with open(路径,'r',encoding='utf-8') as 文件:#打开读
            文本=文件.read()#读全文
    except FileNotFoundError:#缺失文件
        pass#空单元
    if 文本 is None:#无文件
        状态=单元状态(描述符.version,None,{表:{} for 表 in 描述符.tables})#空状态
    else:#有文件
        状态=解析(文本,描述符)#解析
    return 单单元(描述符,路径,状态,关闭回调)#返回单元
