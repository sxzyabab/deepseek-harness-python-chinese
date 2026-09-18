"""批准当前配置档工作区设置里 pnpm 待决的依赖脚本。"""
import os#路径
import yaml#工作区 YAML
from ...工具.原子写入 import 原子写文件#原子写回
from .失败 import 装载失败#过期批准

__all__=['读待决构建','批准构建']#仅中文公开名

待决占位='set this to true or false'#pnpm 11 待决标量

def 节点含锚点或别名(节点):
    """allowBuilds 子树是否含 YAML 锚点或别名。"""
    if 节点 is None:#空
        return False#无
    if getattr(节点,'anchor',None):#有锚点名
        return True#拒绝
    if isinstance(节点,yaml.nodes.AliasNode):#别名
        return True#拒绝
    if isinstance(节点,yaml.nodes.CollectionNode):#序列或映射
        for 项 in 节点.value:#子项
            if isinstance(项,tuple):#映射键值
                for 子 in 项:#键与值
                    if 节点含锚点或别名(子):#递归
                        return True#命中
            elif 节点含锚点或别名(项):#序列元素
                return True#命中
    return False#干净

def 读策略(目录):
    """读出 pnpm-workspace.yaml 的文档与待决包名；锚点/别名拒绝。"""
    路径=os.path.join(目录,'pnpm-workspace.yaml')#工作区路径
    try:#读
        文件=open(路径,'r',encoding='utf-8')#打开
        try:#读全文
            文本=文件.read()#原文
        finally:#关
            文件.close()#关闭
    except FileNotFoundError:#缺失
        文本='{}\n'#空映射
    except OSError as 错误:#其它
        if getattr(错误,'errno',None)!=2:#非 ENOENT
            raise#原样
        文本='{}\n'#空映射
    try:#组树
        根=yaml.compose(文本)#节点树
    except yaml.YAMLError as 错误:#畸形
        raise 错误#原样
    if 根 is None:#空文档
        根=yaml.compose('{}\n')#空映射节点
    if not isinstance(根,yaml.nodes.MappingNode):#须为映射
        raise Exception('pnpm-workspace.yaml must be a YAML mapping')#拒绝
    构建节点=None#allowBuilds 节点
    for 键节点,值节点 in 根.value:#逐项
        if isinstance(键节点,yaml.nodes.ScalarNode) and 键节点.value=='allowBuilds':#命中
            构建节点=值节点#记下
            break#停
    if 构建节点 is not None and not isinstance(构建节点,yaml.nodes.MappingNode):#须为映射
        raise Exception('allowBuilds must be a YAML mapping')#拒绝
    if 节点含锚点或别名(构建节点):#锚点或别名
        raise Exception('allowBuilds must not contain YAML anchors or aliases')#拒绝
    try:#解析值
        文档=yaml.safe_load(文本)#安全加载
    except yaml.YAMLError as 错误:#畸形
        raise 错误#原样
    if 文档 is None:#空文档
        文档={}#空映射
    if not isinstance(文档,dict):#须为映射
        raise Exception('pnpm-workspace.yaml must be a YAML mapping')#拒绝
    构建=文档.get('allowBuilds')#允许构建表
    if 构建 is not None and not isinstance(构建,dict):#须为映射
        raise Exception('allowBuilds must be a YAML mapping')#拒绝
    待决=[]#待决名
    if isinstance(构建,dict):#有表
        for 键,值 in 构建.items():#逐项
            if isinstance(键,str) and '*' not in 键 and '?' not in 键 and 值==待决占位:#精确待决
                待决.append(键)#收下
    return {'document':文档,'pending':待决,'path':路径,'text':文本}#策略

def 读待决构建(目录):
    """读出 pnpm 11 留下的未决定包名；通配规则排除。"""
    return 读策略(目录)['pending']#待决名

def 批准构建(目录,名称列表):
    """持久化批准且不跑脚本；调用方持有配置档清单锁。名称须仍在待决列表。"""
    策略=读策略(目录)#当前策略
    待决=策略['pending']#待决
    for 名称 in 名称列表:#逐名
        if 名称 not in 待决:#已不待决
            raise 装载失败('stale-approval')#过期批准
    if len(名称列表)==0:#空批准
        return#无写
    文档=策略['document']#文档
    if 'allowBuilds' not in 文档 or not isinstance(文档.get('allowBuilds'),dict):#无表
        文档['allowBuilds']={}#新建
    for 名称 in 名称列表:#逐名写 true
        文档['allowBuilds'][名称]=True#批准
    写出=yaml.safe_dump(文档,allow_unicode=True,sort_keys=False)#写回文本
    原子写文件(策略['path'],写出,{'mode':0o600})#原子替换
