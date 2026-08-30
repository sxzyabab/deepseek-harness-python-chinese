"""智能体预设的文件系统发现。

对齐上游 `agent-presets/src/discovery.ts`。公开面仅中文名。
"""
import os,math,yaml
from ...依赖 import include#外部依赖胶水（PyYAML 与 include）
#条目列表读取器=include.条目列表读取器#加载器 YAML 方言（含 !!js）
from ...工具.工作区路径 import 展开家目录路径#展开 ~
from .元数据 import 读预设元数据#读展示元数据
from .预设 import 预设标识规则#id 文法

__all__=['组合文件','用户预设目录','扫描根','发现预设']#仅中文公开名

组合文件='agent.cordis.yml'#组合文件名
用户预设目录='.agent-presets'#用户预设目录名

def 条目列表问题(行们,处=''):#条目列表形状问题
    """`rows` 为何不能当条目列表，能当时为 None。"""
    if not isinstance(行们,list):#必须是列表
        return 'the composition must be a top-level list of plugin rows' if 处=='' else 'group '+处+' must hold a list of plugin rows'#措辞
    for 下标,行 in enumerate(行们):#逐行
        标签='row '+str(下标+1) if 处=='' else 处+' row '+str(下标+1)#标签
        if not isinstance(行,dict) or 行 is None:#行必须是映射
            return 标签+' is not a plugin row (expected a map with a "name")'#不是插件行
        名=行.get('name')#插件名
        if not isinstance(名,str) or 名=='':#必须有非空 name
            return 标签+' names no plugin (a "name" string is required)'#未点名
        if 行.get('group') is True:#组行递归
            嵌套=条目列表问题(行.get('config'),标签)#检查嵌套
            if 嵌套 is not None:#有问题
                return 嵌套#上抛
    return None#形状成立

def 组合问题(路径):#组合文件健康问题
    """`path` 处的组合为何不能挂载；看起来可加载时为 None。"""
    try:#读组合文件
        文件=open(路径,'r',encoding='utf-8')#打开
        try:#读
            内容=文件.read()#原文
        finally:#关
            文件.close()#关闭
    except OSError:#读失败
        return 'the composition file '+组合文件+' cannot be read'#读不出
    try:#按加载器方言解析
        行们=yaml.load(内容,Loader=条目列表读取器)#含 !!js
    except Exception as 错误:#解析失败
        全文=str(错误)#消息
        首行=全文.split('\n',1)[0]#只取第一行
        return 'the composition is not valid YAML: '+首行#非法 YAML
    return 条目列表问题(行们)#再查形状

def 是文件(路径):#是否为普通文件
    """`path` 是否命名一个已存在的普通文件。"""
    try:#stat
        return os.path.isfile(路径)#是普通文件
    except OSError:#任何失败
        return False#不是

def 扫描根(根):#扫描一个预设根
    """扫描一个根下的预设目录。缺席的根产出零预设。"""
    目录=os.path.abspath(展开家目录路径(根['path'] if isinstance(根,dict) else 根.path))#展开并绝对
    信任=根['trust'] if isinstance(根,dict) else 根.trust#信任
    try:#列根目录
        子们=os.listdir(目录)#列出
    except FileNotFoundError:#根不存在
        return []#空
    except OSError as 错误:#其他错误
        raise Exception('agent-presets: cannot read preset root '+目录+': '+str(错误)) from 错误#上抛
    发现=[]#本根发现的预设
    for 名 in 子们:#每个子条目
        子路径=os.path.join(目录,名)#子路径
        if not os.path.isdir(子路径) or 预设标识规则.fullmatch(名) is None:#非目录或非法 id
            continue#跳过
        组合路径=os.path.join(子路径,组合文件)#组合文件
        if 是文件(组合路径):#存在则查健康
            损坏=组合问题(组合路径)#原因或 None
        else:#缺失仍占 id
            损坏='the composition file '+组合文件+' is missing — the directory still occupies the id; delete it or restore the file'#缺失
        元数据=读预设元数据(子路径)#展示元数据
        行={'id':名,'trust':信任,'path':组合路径}#名册行
        行.update(元数据)#展示字段
        if 损坏 is not None:#损坏才带原因
            行['broken']=损坏#原因
        发现.append(行)#收下
    def 排序键(项):#按 order 再按 id
        """排序键。"""
        序=项.get('order')#排序
        if 序 is None:#未声明
            序=math.inf#排最后
        return (序,项['id'])#再按 id
    发现.sort(key=排序键)#排序
    return 发现#本根预设

def 发现预设(根们):#扫描全部根
    """按优先序扫描每个根；更早的根在重复 id 上胜出。"""
    按标识={}#按 id 去重
    for 根 in 根们:#按优先序
        for 预设 in 扫描根(根):#该根的预设
            if 预设['id'] in 按标识:#更早的根已胜出
                continue#跳过
            按标识[预设['id']]=预设#认领
    return list(按标识.values())#去重后的名册
