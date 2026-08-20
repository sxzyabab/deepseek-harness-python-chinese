"""面向模型的整文件写入。它从单策略槽取得可选意图，不经 stat 调用 ctx.fs.writeText，然后记录结果版本；没有策略表示无条件原子创建或覆盖。对齐上游 tool-fs/src/write.ts。"""
from tools import 定义工具#导入工具定义
from .差异 import 计算块差异,从元数据取差异#导入hunk diff计算与meta收窄
from .错误 import 补救文件系统错误#导入模型边界错误补救
from .会话工作目录 import 会话解析选项#导入会话cwd解析选项
from .辅助 import 取字段,试取,解开#字段读取与承诺展开

写提示文本=(#把 write 定位为整文件创建/覆盖的稳定系统提示词指引（字面量不翻译）
    'Use the write tool to create files or completely replace file contents. Existing files are overwritten, so read an existing file first (the default fs-observation-policy requires it) and prefer edit for targeted changes.'#整文件创建/覆盖：先读后写，定向改优先edit
)#写提示文本结束
def 解析写参数(参数):#校验写工具参数
    """校验 schema DSL 表达不了的值约束：只要非空白 file_path——空 content 合法。"""
    if len(取字段(参数,'file_path').strip())==0:#路径不得为空
        raise Exception('file_path must be a non-empty string')#路径不得为空
    return {'路径':取字段(参数,'file_path'),'内容':取字段(参数,'content')}#转为内部字段

def 格式化写输出(展示路径,结果):#格式化写结果确认信封
    """把写入结果格式化成一块面向模型的文本体。确认信封不含文件内容。"""
    动词='Created' if 取字段(结果,'operation')=='create' else 'Updated'#按操作选择动词
    return '<path>'+展示路径+'</path>\n<type>file</type>\n<content>\n'+动词+' file\n</content>'#确认信封

def 应用写工具(上下文,沙箱):#注册 write 工具
    """注册 write 工具及其系统提示词指引。"""
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:write',#段落名
        'order':101,#排序
        'text':写提示文本,#指引模型先读再用write
    })#系统提示词结束
    参数表={#参数schema
        'file_path':{'type':'string','required':True,'description':'Path to write, resolved by the filesystem backend.'},#写入路径
        'content':{'type':'string','required':True,'description':'Full UTF-8 text content to write.'},#完整内容
    }#基础参数
    if len(沙箱.升级模式)>0:#隔离后端才展开升级字段
        参数表.update(沙箱.模式字段())#升级字段
    def 渲染(参数,值):#模型可见确认信封
        """模型可见确认信封。"""
        return [{'type':'text','text':格式化写输出(取字段(值,'path'),值)}]#确认信封
    def 呈现元数据(参数,值):#结果展示用的 diff meta
        """结果展示用的 diff meta。"""
        if 取字段(值,'before') is None:#没有before则无hunk
            差异列表=[]#空diff列表
        else:#有基准文本
            差异列表=[{'path':项['path'],'oldText':项['oldText'],'newText':项['newText']} for 项 in 计算块差异(取字段(参数,'file_path'),取字段(值,'before'),取字段(值,'after'))]#只保留展示字段
        return {'diffs':差异列表}#diff meta
    def 无条件意图():#裸默认无条件写入
        """裸默认无条件写入。"""
        return None#无条件
    def 执行(参数,执行上下文):#执行写入
        """执行写入。"""
        输入=解析写参数(参数)#校验参数
        沙箱政策=解开(沙箱.解析政策('write',参数,执行上下文))#解析沙箱策略
        目标=解开(上下文.fs.解析(输入['路径'],会话解析选项(执行上下文,输入['路径'],试取(沙箱政策,'workspaceRoot'))))#解析稳定目标
        意图=解开(上下文.waterfall('fs/write-intent',目标,执行上下文,无条件意图))#取写意图
        try:#调用提供方写入
            结局=解开(上下文.fs.写文本(目标,输入['内容'],意图,试取(执行上下文,'signal'),沙箱政策))#原子写入
        except Exception as 错误:#写入失败
            raise 补救文件系统错误(沙箱.映射错误(错误,沙箱政策))#映射并补救后抛出
        上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(结局,'version')},执行上下文)#记录观察
        return {#返回结构化结果
            'path':取字段(目标,'displayPath'),#展示路径
            'operation':取字段(结局,'operation'),#创建或更新
            'before':试取(结局,'before'),#写入前文本
            'after':取字段(结局,'after'),#写入后文本
        }#结果结束
    def 呈现调用(参数):#调用时 diff 卡片
        """调用时 diff 卡片。拿不到先前文件内容，因此 oldText 为 None 也表示覆盖。"""
        return {#卡片
            'card':'diff',#diff卡片
            'title':'Write '+取字段(参数,'file_path'),#标题
            'diffs':[{'path':取字段(参数,'file_path'),'oldText':None,'newText':取字段(参数,'content')}],#整文件作为新文本
            'locations':[{'path':取字段(参数,'file_path')}],#位置
        }#卡片结束
    def 呈现结果(参数,结果):#结果时 diff 卡片
        """结果时 diff 卡片。错误结果不展示。畸形则回退到调用参数。"""
        if 取字段(结果,'isError'):#错误结果
            return None#不展示diff
        差异列表=从元数据取差异(试取(结果,'meta'))#从meta收窄hunk
        if 差异列表 is None:#畸形
            差异列表=[{'path':取字段(参数,'file_path'),'oldText':None,'newText':取字段(参数,'content')}]#回退到调用参数
        return {'card':'diff','title':'Write '+取字段(参数,'file_path'),'diffs':差异列表}#结果diff卡片
    上下文.tools.登记(定义工具({#注册write工具
        'name':'write',#工具名
        'description':'Create or fully replace a UTF-8 text file.',#工具描述
        'parameters':参数表,#参数schema
        'output':{#结构化输出
            'schema':{#输出schema
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'path':{'type':'string','required':True},#已解析路径
                    'operation':{'type':'string','required':True,'enum':['create','update']},#创建或更新
                    'before':{#写入前文本
                        'required':True,#必填
                        'oneOf':[#字符串或null
                            {'type':'string'},#有基准文本
                            {'type':'null'},#无基准
                        ],#oneOf结束
                    },#before结束
                    'after':{'type':'string','required':True},#写入后文本
                },#properties结束
            },#schema结束
            'render':渲染,#模型可见确认信封
            'presentationMeta':呈现元数据,#结果展示用的diff meta
        },#output结束
        'execute':执行,#执行写入
        'presentCall':呈现调用,#调用时diff卡片
        'presentResult':呈现结果,#结果时diff卡片
    }))#register结束
