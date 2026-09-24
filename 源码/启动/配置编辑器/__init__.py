import os
import yaml
from ...依赖.cordis import 服务,纤程状态,纤程解析配置
from ...依赖.工具 import 克隆,深入比较
from ...依赖.include import 插件列表读取器,插件列表写出器
from ...依赖.loader import 是否表达式节点,表达式键
from ...启动.app启动 import 组合条目,加载配置目录,读配置档补丁,协调配置档补丁
from ...工具.原子写入 import 带文件锁,原子写文件

__all__=['包名','名称','依赖','默认','配置编辑器']

包名='@deepseek-ai/dsh-boot-config-editor'
名称='config-editor'
依赖=['加载器','profileContext']

class 配置编辑错误(Exception):
    """配置编辑失败。"""

def 展平(行列表):
    """展开嵌套 Include 组。行是 dict。"""
    结果=[]
    for 行 in 行列表:
        结果.append(行)
        if 行.get('group') and isinstance(行.get('config'),list):
            结果.extend(展平(行['config']))
    return 结果

class 配置编辑器(服务):
    """配置档拥有的插件配置编辑。"""
    def __init__(自身,拥有上下文):
        """登记 configEditor。"""
        super().__init__(拥有上下文,'configEditor')
        自身._拥有=拥有上下文

    @property
    def documentPath(自身):
        """本服务编辑的配置档补丁路径。"""
        return 自身._拥有.profileContext['patchPath']

    def 条目(自身):
        """带唯一补丁 id 的活动条目。"""
        候选=[]
        for 插件配置对象 in 自身._拥有.加载器.列出插件配置():
            拥有=插件配置对象.父组.所属树.所属上下文.纤程.插件配置
            if 拥有 is None or 拥有.选项.get('id')!='include':
                continue
            候选.append(插件配置对象)
        计数={}
        for 项 in 候选:
            标识=项.选项['id']
            计数[标识]=计数.get(标识,0)+1
        return [项 for 项 in 候选 if 计数[项.选项['id']]==1]

    def 配置面(自身):
        """活动条目的继承层与显式覆盖。"""
        配置档=自身._拥有.profileContext
        已加载=加载配置目录('dsh',配置档['dir'],配置档['installAnchor'])
        结果=[]
        for 插件配置对象 in 自身.条目():
            覆盖={}
            for 行 in reversed(已加载['patches']):
                if 行.get('id')==插件配置对象.选项['id'] and 'config' in 行:
                    覆盖=克隆(行['config'])
                    break
            结果.append({
                'entry':插件配置对象,
                'inherited':自身._继承(插件配置对象,已加载),
                'override':覆盖,
            })
        return 结果

    def _继承(自身,插件配置对象,已加载):
        """去掉本 id 的 config 后组合得到的继承值。"""
        补丁=[]
        for 行 in 已加载['patches']:
            if 行.get('id')!=插件配置对象.选项['id'] or 'insert' in 行:
                补丁.append(行)
                continue
            其余=dict(行)
            其余.pop('config',None)
            补丁.append(其余)
        层表=[层['patches'] for 层 in 已加载['layers']]
        层表.append(补丁)
        命中=None
        for 行 in 展平(组合条目(层表)):
            if 行.get('id')==插件配置对象.选项['id']:
                命中=行
                break
        return 克隆(命中['config'] if 命中 is not None and 'config' in 命中 else {})

    def 编辑(自身,插件配置对象,变更):
        """校验、落盘并协调下一份配置。"""
        def 跑():
            """持锁编辑。"""
            路径=自身.documentPath
            配置档=自身._拥有.profileContext
            def 锁内():
                """单次写事务。"""
                if 插件配置对象 not in 自身.条目() or 插件配置对象.纤程 is None:
                    raise 配置编辑错误('配置条目已不可用')
                先前补丁=读配置档补丁('dsh',配置档)
                协调配置档补丁(自身._拥有.根,先前补丁,'dsh')
                if 插件配置对象 not in 自身.条目():
                    raise 配置编辑错误('重载期间配置条目已更换')
                当前=克隆(插件配置对象.选项['config'] if 'config' in 插件配置对象.选项 else {})
                继承=自身._继承(插件配置对象,加载配置目录('dsh',配置档['dir'],配置档['installAnchor']))
                下一份=变更(当前,继承)
                纤程=插件配置对象.纤程
                if 纤程.状态!=纤程状态.已激活:
                    raise 配置编辑错误('配置插件已不再活动')
                def 原样(*位置参数):
                    """瀑布内建：原样交出下一份。"""
                    return 下一份
                已解析=纤程.所属上下文.链式拦截(纤程,'internal/config',下一份,原样)
                纤程解析配置(纤程.运行时,已解析)
                try:
                    文件=open(路径,'r',encoding='utf-8')
                    try:
                        先前=文件.read()
                    finally:
                        文件.close()
                except FileNotFoundError:
                    先前='[]\n'
                文档=yaml.load(先前,Loader=插件列表读取器)
                if 文档 is None:
                    文档=[]
                if not isinstance(文档,list):
                    raise 配置编辑错误('配置档补丁必须是 YAML 序列')
                序号=-1
                for 下标 in range(len(文档)-1,-1,-1):
                    项=文档[下标]
                    if not isinstance(项,dict):
                        continue
                    if 项.get('id')!=插件配置对象.选项['id'] or 'insert' in 项:
                        continue
                    if 'name' in 项 and 项.get('name')!=插件配置对象.选项.get('name'):
                        continue
                    序号=下标
                    break
                if 深入比较(下一份,继承):
                    下标=len(文档)-1
                    while 下标>=0:
                        行=文档[下标]
                        if isinstance(行,dict) and 行.get('id')==插件配置对象.选项['id'] and 'insert' not in 行:
                            行.pop('config',None)
                            仅身份=('id' in 行)+('name' in 行)
                            if len(行)==仅身份:
                                文档.pop(下标)
                        下标-=1
                elif 序号<0:
                    文档.append({
                        'id':插件配置对象.选项['id'],
                        'name':插件配置对象.选项.get('name'),
                        'config':下一份,
                    })
                else:
                    文档[序号]['config']=下一份
                写出=yaml.dump(文档,Dumper=插件列表写出器,allow_unicode=True,sort_keys=False)
                已加载=加载配置目录('dsh',配置档['dir'],配置档['installAnchor'])
                读入=yaml.load(写出,Loader=插件列表读取器)
                if 读入 is None:
                    读入=[]
                补丁=读配置档补丁('dsh',配置档,{**已加载,'patches':读入})
                生效=None
                for 行 in 展平(组合条目([补丁])):
                    if 行.get('id')==插件配置对象.选项['id']:
                        生效=行
                        break
                生效配置=生效['config'] if 生效 is not None and 'config' in 生效 else {}
                if not 深入比较(生效配置,下一份):
                    raise 配置编辑错误('配置 "'+str(插件配置对象.选项['id'])+'" 被主目录补丁或命令行覆盖层覆盖')
                原子写文件(路径,写出,{'mode':0o600})
                try:
                    协调配置档补丁(自身._拥有.根,补丁,'dsh',[插件配置对象.选项['id']])
                except Exception as 错误:
                    原子写文件(路径,先前,{'mode':0o600})
                    协调配置档补丁(自身._拥有.根,先前补丁,'dsh')
                    raise 错误
            return 带文件锁(os.path.join(配置档['dir'],'package.json'),锁内)
        热更新服务=自身._拥有.获取服务('hmr',False)
        if 热更新服务 is None:
            跑()
        else:
            热更新服务.独占执行(跑)

默认=配置编辑器
name=名称
inject=依赖
default=默认
配置编辑器.inject=依赖
