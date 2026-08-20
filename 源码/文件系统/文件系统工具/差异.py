"""写与编辑的结果时上下文 diff 展示。存储返回 before/after 文本；此面向模型的层为每个已应用 hunk 推导一张三行上下文卡片。对齐上游 tool-fs/src/diff.ts。"""
import difflib#标准库行差异（对齐上游 structuredPatch 的 hunk 分组）
from .辅助 import 试取#可选字段

差异上下文=3#每个已应用 hunk 两侧展示的上下文行数

def 计算块差异(路径,之前,之后):#按hunk计算上下文diff
    """在 before 与 after 之间为每个 hunk 计算一个文件差异，各自携带已应用变更加上差异上下文行。纯插入使用 oldText 为 None，仅属于补丁的无换行标记被省略，分散的替换保持为独立 hunk。文本相同时为空列表。"""
    旧行=之前.splitlines()#旧侧行
    新行=之后.splitlines()#新侧行
    匹配=difflib.SequenceMatcher(a=旧行,b=新行,autojunk=False)#按行求差异
    差异列表=[]#收集每个hunk的FileDiff
    for 组 in 匹配.get_grouped_opcodes(差异上下文):#按上下文分组成hunk
        旧侧=[]#旧侧行
        新侧=[]#新侧行
        for 标记,旧起,旧止,新起,新止 in 组:#逐段分类
            if 标记=='equal':#未变上下文
                旧侧.extend(旧行[旧起:旧止])#旧侧
                新侧.extend(新行[新起:新止])#新侧
            elif 标记=='replace':#替换
                旧侧.extend(旧行[旧起:旧止])#旧侧
                新侧.extend(新行[新起:新止])#新侧
            elif 标记=='delete':#删除
                旧侧.extend(旧行[旧起:旧止])#只进旧侧
            elif 标记=='insert':#插入
                新侧.extend(新行[新起:新止])#只进新侧
        差异列表.append({#一张 FileDiff
            'path':路径,#盖到产出 diff 上的路径
            'oldText':'\n'.join(旧侧) if len(旧侧)>0 else None,#纯插入时 oldText 为 None
            'newText':'\n'.join(新侧),#新侧文本
        })#hunk结束
    return 差异列表#按文件顺序返回

def 是否文件差异(值):#收窄为文件差异
    """value 是否为合法文件差异（从不透明 meta 做防御性收窄）。"""
    if not isinstance(值,dict):#必须是普通对象
        return False#不是对象
    路径=试取(值,'path')#路径
    旧文本=试取(值,'oldText')#旧文本
    新文本=试取(值,'newText')#新文本
    return isinstance(路径,str) and (旧文本 is None or isinstance(旧文本,str)) and isinstance(新文本,str)#字段类型

def 从元数据取差异(元数据):#从结果meta收窄出diff列表
    """把不透明的现场或回放结果元数据收窄为非空文件 diff。畸形元数据返回 None，以便展示回退，而不是在回放时抛错。"""
    if not isinstance(元数据,dict):#必须是普通对象
        return None#畸形
    差异列表=试取(元数据,'diffs')#取出diffs字段
    if (not isinstance(差异列表,list)) or len(差异列表)==0:#必须是非空数组
        return None#畸形
    for 项 in 差异列表:#逐项
        if not 是否文件差异(项):#有非法项
            return None#畸形
    return 差异列表#已校验列表
