"""批准当前配置档工作区设置里 pnpm 待决的依赖脚本。"""
import os
import yaml
from ...工具.原子写入 import 原子写文件
from .失败 import 装载失败

__all__=['读待决构建','批准构建']

待决占位='set this to true or false'#pnpm 11 待决标量

def 节点含锚点或别名(节点):
    """allowBuilds 子树是否含 YAML 锚点或别名。"""
    if 节点 is None:
        return False
    if getattr(节点,'anchor',None):
        return True
    if isinstance(节点,yaml.nodes.AliasNode):
        return True
    if isinstance(节点,yaml.nodes.CollectionNode):
        for 项 in 节点.value:
            if isinstance(项,tuple):
                for 子 in 项:
                    if 节点含锚点或别名(子):
                        return True
            elif 节点含锚点或别名(项):
                return True
    return False

def 读策略(目录):
    """读出 pnpm-workspace.yaml 的文档与待决包名；锚点/别名拒绝。"""
    路径=os.path.join(目录,'pnpm-workspace.yaml')
    try:
        文件=open(路径,'r',encoding='utf-8')
        try:
            文本=文件.read()
        finally:
            文件.close()
    except FileNotFoundError:
        文本='{}\n'
    except OSError as 错误:
        if getattr(错误,'errno',None)!=2:
            raise
        文本='{}\n'
    try:
        根=yaml.compose(文本)
    except yaml.YAMLError as 错误:
        raise 错误
    if 根 is None:
        根=yaml.compose('{}\n')
    if not isinstance(根,yaml.nodes.MappingNode):
        raise Exception('pnpm-workspace.yaml 必须是 YAML 映射')
    构建节点=None
    for 键节点,值节点 in 根.value:
        if isinstance(键节点,yaml.nodes.ScalarNode) and 键节点.value=='allowBuilds':
            构建节点=值节点
            break
    if 构建节点 is not None and not isinstance(构建节点,yaml.nodes.MappingNode):
        raise Exception('allowBuilds 必须是 YAML 映射')
    if 节点含锚点或别名(构建节点):
        raise Exception('allowBuilds 不得含 YAML 锚点或别名')
    try:
        文档=yaml.safe_load(文本)
    except yaml.YAMLError as 错误:
        raise 错误
    if 文档 is None:
        文档={}
    if not isinstance(文档,dict):
        raise Exception('pnpm-workspace.yaml 必须是 YAML 映射')
    构建=文档.get('allowBuilds')
    if 构建 is not None and not isinstance(构建,dict):
        raise Exception('allowBuilds 必须是 YAML 映射')
    待决=[]
    if isinstance(构建,dict):
        for 键,值 in 构建.items():
            if isinstance(键,str) and '*' not in 键 and '?' not in 键 and 值==待决占位:
                待决.append(键)
    return {'document':文档,'pending':待决,'path':路径,'text':文本}

def 读待决构建(目录):
    """读出 pnpm 11 留下的未决定包名；通配规则排除。"""
    return 读策略(目录)['pending']

def 批准构建(目录,名称列表):
    """持久化批准且不跑脚本；调用方持有配置档清单锁。名称须仍在待决列表。"""
    策略=读策略(目录)
    待决=策略['pending']
    for 名称 in 名称列表:
        if 名称 not in 待决:
            raise 装载失败('stale-approval')
    if len(名称列表)==0:
        return
    文档=策略['document']
    if 'allowBuilds' not in 文档 or not isinstance(文档.get('allowBuilds'),dict):
        文档['allowBuilds']={}
    for 名称 in 名称列表:
        文档['allowBuilds'][名称]=True
    写出=yaml.safe_dump(文档,allow_unicode=True,sort_keys=False)
    原子写文件(策略['path'],写出,{'mode':0o600})
