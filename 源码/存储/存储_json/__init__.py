"""JSON 存储后端：在配置根下以原子整文件重写发布人类可读文档。

对齐上游 `@deepseek-ai/dsh-storage-json`。在存储枢纽上注册为后端 `json`。
"""
import os#路径
from ...依赖.schemastery import 字符串字段,字典字段#配置
from ..存储.错误 import 存储错误#存储错误
from ..存储.后端 import 单元名正则,存储后端,键值面#后端词汇
from ..存储 import 存储后端服务键#生命周期键
from .单单元 import 打开单单元#single 布局
from .按记录单元 import 打开按记录单元#per-record 布局

名称='storage-json'#Cordis 插件名
注入=['storage']#依赖 storage 枢纽
配置模式=字典字段({'root':字符串字段()})#必填根目录
配置=配置模式#中文配置

def 校验描述符(描述符):#校验单元与表名
    """校验单元与表名。"""
    if 单元名正则.fullmatch(描述符.name) is None:#单元名非法
        raise 存储错误('malformed-medium',"invalid unit name '"+描述符.name+"'")#拒绝
    for 表 in 描述符.tables:#每张表
        if 单元名正则.fullmatch(表) is None:#表名非法
            raise 存储错误('malformed-medium',"invalid table name '"+表+"' in unit '"+描述符.name+"'")#拒绝

class 键值面实现(键值面):#JSON 后端 KV 面
    """JSON 后端 KV 面。"""
    def __init__(自身,后端):#绑定后端
        """绑定后端。"""
        自身._后端=后端#宿主后端

    def open(自身,描述符):#打开单元
        """打开单元。"""
        return 自身._后端._打开(描述符)#委托

class Json存储后端(存储后端):#JSON 存储后端
    """拥有文件树根并服务 `kv` 面。"""
    def __init__(自身,根):#记下根目录
        """记下根目录。"""
        super().__init__()#初始化后端
        自身._根=根#根路径
        自身.kv=键值面实现(自身)#KV 面
        自身._已打开={}#已打开单元
        自身._已关=False#关闭标志

    def _释放槽(自身,名称):#关闭回调
        """从已打开表摘掉单元。"""
        自身._已打开.pop(名称,None)#释放槽

    def _打开(自身,描述符):#实际打开
        """实际打开。"""
        if 自身._已关:#已关
            raise 存储错误('closed','json backend is closed')#拒绝
        校验描述符(描述符)#校验名
        if 描述符.name in 自身._已打开:#双开
            raise 存储错误('malformed-medium',"unit '"+描述符.name+"' is already open; a unit has exactly one live handle")#调用方错误
        os.makedirs(自身._根,mode=0o700,exist_ok=True)#确保根目录
        def 关闭回调():#释放槽
            """释放已打开槽。"""
            自身._释放槽(描述符.name)#释放
        if 描述符.layout=='per-record':#per-record
            单元=打开按记录单元(描述符,自身._根,关闭回调)#打开目录树
        else:#single 默认
            单元=打开单单元(描述符,自身._根,关闭回调)#打开整文件
        if 自身._已关:#打开途中后端关了
            单元.close()#关掉刚打开的
            raise 存储错误('closed','json backend is closed')#拒绝
        自身._已打开[描述符.name]=单元#登记
        return 单元#返回

    def close(自身):#关闭后端
        """关闭后端与全部已打开单元。"""
        if not 自身._已关:#首次
            自身._已关=True#标记
        for 单元 in list(自身._已打开.values()):#关每个单元
            单元.close()#关闭

def 应用(上下文对象,配置值):#注册 json 后端
    """在存储枢纽上注册 `json` 后端。"""
    后端=Json存储后端(配置值['root'])#构造后端
    def 副作用():#注册 effect
        """挂到枢纽，拆除时注销并关后端。"""
        注销=上下文对象.storage.backend.register('json',后端)#挂到枢纽
        def 拆除():#插件拆除
            """先注销再关后端。"""
            注销()#先注销
            后端.close()#再关后端
        return 拆除#disposer
    上下文对象.副作用(副作用)#登记
    上下文对象.提供服务(存储后端服务键('json'),后端)#提供生命周期服务
    return None#无额外返回

__all__=['Json存储后端','名称','注入','配置','配置模式','应用']#仅中文公开名
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置模式#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
