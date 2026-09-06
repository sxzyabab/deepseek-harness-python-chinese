"""预设的展示元数据：选择器显示的名称与描述。

对齐上游 `agent-presets/src/metadata.ts`。公开面仅中文名。
"""
import os#路径拼接
import yaml#外部依赖胶水（PyYAML）

__all__=['元数据文件','读预设元数据','渲染预设元数据']#仅中文公开名

元数据文件='preset.yml'#元数据文件名

def 文本(值):
    """非空已修剪字符串；其他一律 None。"""
    if not isinstance(值,str):#非字符串
        return None#不要
    修剪=值.strip()#去掉首尾空白
    return None if 修剪=='' else 修剪#空串当缺席

def 读预设元数据(目录):
    """读一个预设目录的展示元数据。缺席、无法解析、形状不对都是空元数据。"""
    路径=os.path.join(目录,元数据文件)#preset.yml
    try:#元数据文件可选
        文件=open(路径,'r',encoding='utf-8')#打开
        try:#读
            原文=文件.read()#原文
        finally:#关
            文件.close()#关闭
    except OSError:#缺席是常见情况
        return {}#空元数据
    try:#YAML 必须能解析
        解析=yaml.safe_load(原文)#解析
    except yaml.YAMLError:#畸形展示文本
        return {}#空元数据
    if not isinstance(解析,dict):#非对象
        return {}#空
    名称=文本(解析['name'] if 'name' in 解析 else None)#收窄名称
    描述=文本(解析['description'] if 'description' in 解析 else None)#收窄描述
    排序=解析['order'] if 'order' in 解析 else None#排序
    if not isinstance(排序,(int,float)) or isinstance(排序,bool):#非数字，先排除 bool
        排序=None#缺席
    elif 排序!=排序 or abs(排序)==float('inf'):#非有限
        排序=None#缺席
    结果={}#只展开已有字段
    if 名称 is not None:#有名称
        结果['name']=名称#带上
    if 描述 is not None:#有描述
        结果['description']=描述#带上
    if 排序 is not None:#有排序
        结果['order']=排序#带上
    return 结果#元数据

def 渲染预设元数据(元数据):
    """把展示元数据渲染成文件内容；没有可存内容时为 None。元数据是 dict。"""
    名称=文本(元数据['name'] if 'name' in 元数据 else None)#收窄名称
    描述=文本(元数据['description'] if 'description' in 元数据 else None)#收窄描述
    排序=元数据['order'] if 'order' in 元数据 else None#排序
    if 名称 is None and 描述 is None and 排序 is None:#全空
        return None#不写文件
    文档={}#文档
    if 名称 is not None:#有名称
        文档['name']=名称#带上
    if 描述 is not None:#有描述
        文档['description']=描述#带上
    if 排序 is not None:#有排序
        文档['order']=排序#带上
    return yaml.safe_dump(文档,allow_unicode=True,sort_keys=False,width=10**9)#不折行
