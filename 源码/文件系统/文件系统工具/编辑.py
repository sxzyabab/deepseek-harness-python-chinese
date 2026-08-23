"""面向模型的字面量编辑，默认要求唯一匹配。它从单意图槽取得可选守卫，不经单独 stat 调用 ctx.fs.editText，然后记录观察到的版本；没有策略表示无条件原子编辑。对齐上游 tool-fs/src/edit.ts。"""
from ...内核.工具 import 定义工具#导入工具定义
from .差异 import 计算块差异,从元数据取差异#导入hunk diff计算与meta收窄
from .错误 import 补救文件系统错误#导入模型边界错误补救
from .会话工作目录 import 会话解析选项#导入会话cwd解析选项
from .辅助 import 取字段,试取,解开#字段读取与承诺展开

编辑提示文本=(#把 edit 定位为定向字面量替换的稳定系统提示词指引（字面量不翻译）
    'Use the edit tool for targeted changes to existing UTF-8 text files. It replaces literal old_string with new_string; by default old_string must appear exactly once. If old_string appears multiple times, provide a more specific old_string or set replace_all to true. Read the file first (the default fs-observation-policy requires it), unless you just created or edited it in this session.'#定向替换：默认唯一匹配，先读后edit
)#编辑提示文本结束
def 解析编辑参数(参数):#校验编辑工具参数
    """校验 schema DSL 表达不了的值约束：非空白 file_path、非空 old_string，以及 old_string 与 new_string 必须不同。replace_all 缺省为 False。"""
    if len(取字段(参数,'file_path').strip())==0:#路径不得为空
        raise Exception('file_path must be a non-empty string')#路径不得为空
    if len(取字段(参数,'old_string'))==0:#旧字面量不得为空
        raise Exception('old_string must be a non-empty string')#旧字面量不得为空
    if 取字段(参数,'old_string')==取字段(参数,'new_string'):#新旧必须不同
        raise Exception('old_string and new_string must differ')#新旧必须不同
    替换全部=试取(参数,'replace_all')#是否替换全部
    if 替换全部 is None:#缺省
        替换全部=False#缺省不替换全部
    return {#转为内部输入
        '路径':取字段(参数,'file_path'),#路径
        '旧字面量':取字段(参数,'old_string'),#旧字面量
        '新字面量':取字段(参数,'new_string'),#新字面量
        '替换全部':替换全部,#是否替换全部
    }#输入结束

def 格式化编辑输出(展示路径,替换全部):#格式化编辑成功消息
    """把编辑成功格式化为 Claude 风格的面向模型消息。"""
    if 替换全部:#是否全部替换
        return 'The file '+展示路径+' has been updated. All occurrences were successfully replaced.'#全部替换确认
    return 'The file '+展示路径+' has been updated successfully.'#单次替换确认

def 应用编辑工具(上下文,沙箱):#注册 edit 工具
    """注册 edit 工具及其系统提示词指引。"""
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:edit',#段落名
        'order':102,#排序
        'text':编辑提示文本,#指引模型先读再edit
    })#系统提示词结束
    参数表={#参数schema
        'file_path':{'type':'string','required':True,'description':'Path to edit, resolved by the filesystem backend.'},#编辑路径
        'old_string':{'type':'string','required':True,'description':'Literal text to replace. Must match exactly.'},#待替换字面量
        'new_string':{'type':'string','required':True,'description':'Literal replacement text. Use an empty string to delete the match.'},#替换字面量
        'replace_all':{'type':'boolean','description':'Replace all matches. Defaults to false; when false, old_string must appear exactly once.'},#是否全部替换
    }#基础参数
    if len(沙箱.升级模式)>0:#隔离后端才展开升级字段
        参数表.update(沙箱.模式字段())#升级字段
    def 渲染(参数,值):#模型可见确认句
        """模型可见确认句。"""
        替换全部=试取(参数,'replace_all')#是否全部替换
        if 替换全部 is None:#缺省
            替换全部=False#缺省否
        return [{'type':'text','text':格式化编辑输出(取字段(值,'path'),替换全部)}]#确认句
    def 呈现元数据(参数,值):#结果展示用的 diff meta
        """结果展示用的 diff meta。"""
        差异列表=[{'path':项['path'],'oldText':项['oldText'],'newText':项['newText']} for 项 in 计算块差异(取字段(参数,'file_path'),取字段(值,'before'),取字段(值,'after'))]#只保留展示字段
        return {'diffs':差异列表}#diff meta
    def 无条件意图():#裸默认无条件编辑
        """裸默认无条件编辑。"""
        return None#无条件
    def 执行(参数,执行上下文):#执行编辑
        """执行编辑。"""
        输入=解析编辑参数(参数)#校验参数
        沙箱政策=解开(沙箱.解析政策('edit',参数,执行上下文))#解析沙箱策略
        目标=解开(上下文.fs.解析(输入['路径'],会话解析选项(执行上下文,输入['路径'],试取(沙箱政策,'workspaceRoot'))))#解析稳定目标
        try:#取意图并调用提供方编辑
            意图=解开(上下文.waterfall('fs/edit-intent',目标,执行上下文,无条件意图))#取编辑意图
            结局=解开(上下文.fs.编辑文本(#原子编辑
                目标,#目标
                {'oldString':输入['旧字面量'],'newString':输入['新字面量'],'replaceAll':输入['替换全部']},#字面量替换请求
                意图,#版本守卫或None
                试取(执行上下文,'signal'),#取消信号
                沙箱政策,#每调用沙箱策略
            ))#编辑文本结束
        except Exception as 错误:#意图或编辑失败
            raise 补救文件系统错误(沙箱.映射错误(错误,沙箱政策))#映射并补救后抛出
        上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(结局,'version')},执行上下文)#记录观察
        return {#返回结构化结果
            'path':取字段(目标,'displayPath'),#展示路径
            'before':取字段(结局,'before'),#编辑前文本
            'after':取字段(结局,'after'),#编辑后文本
        }#结果结束
    def 呈现调用(参数):#调用时 diff 卡片
        """调用时 diff 卡片。空 old_string 映射为 None。"""
        旧字面量=取字段(参数,'old_string')#待替换字面量
        return {#卡片
            'card':'diff',#diff卡片
            'title':'Edit '+取字段(参数,'file_path'),#标题
            'diffs':[{'path':取字段(参数,'file_path'),'oldText':旧字面量 if 旧字面量 else None,'newText':取字段(参数,'new_string')}],#字面量替换片段
            'locations':[{'path':取字段(参数,'file_path')}],#位置
        }#卡片结束
    def 呈现结果(参数,结果):#结果时 diff 卡片
        """已应用元数据替换调用时片段；错误或畸形回放元数据使用通用结果渲染。"""
        if 取字段(结果,'isError'):#错误结果
            return None#不展示diff
        差异列表=从元数据取差异(试取(结果,'meta'))#从meta收窄hunk
        if 差异列表 is None:#畸形
            return None#交给通用渲染
        return {'card':'diff','title':'Edit '+取字段(参数,'file_path'),'diffs':差异列表}#结果diff卡片
    上下文.tools.登记(定义工具({#注册edit工具
        'name':'edit',#工具名
        'description':'Edit an existing UTF-8 text file by replacing literal text.',#工具描述
        'parameters':参数表,#参数schema
        'output':{#结构化输出
            'schema':{#输出schema
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'path':{'type':'string','required':True},#已解析路径
                    'before':{'type':'string','required':True},#编辑前文本
                    'after':{'type':'string','required':True},#编辑后文本
                },#properties结束
            },#schema结束
            'render':渲染,#模型可见确认句
            'presentationMeta':呈现元数据,#结果展示用的diff meta
        },#output结束
        'execute':执行,#执行编辑
        'presentCall':呈现调用,#调用时diff卡片
        'presentResult':呈现结果,#结果时diff卡片
    }))#register结束
