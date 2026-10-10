'面向模型的整文件写入'
from ...内核.工具 import 定义工具#导入工具定义
from .差异 import 计算块差异,从元数据取差异,从元数据取路径#导入hunk diff计算与meta收窄
from .异常 import 补救文件系统错误,工具文件系统错误#导入模型边界错误补救与本包异常
from .会话工作目录 import 会话解析选项#导入会话cwd解析选项

写提示文本前缀='Read an existing file before overwriting it with write (the default fs-observation-policy requires it)'#先读后覆盖
def 解析写参数(参数):#校验写工具参数
    '校验 schema DSL 表达不了的值约束：只要非空白 file_path——空 content 合法'
    if len(参数['file_path'].strip())==0:#路径不得为空
        raise 工具文件系统错误('file_path must be a non-empty string')#路径不得为空
    return {'路径':参数['file_path'],'内容':参数['content']}#转为内部字段

def 格式化写输出(展示路径,结果):#格式化写结果确认信封
    """把写入结果格式化成一块面向模型的文本体。
    确认信封不含文件内容
    """
    动词='Created' if 结果['operation']=='create' else 'Updated'#按操作选择动词
    return '<path>'+展示路径+'</path>\n<type>file</type>\n<content>\n'+动词+' file\n</content>'#确认信封

def 应用写工具(上下文,沙箱):#注册 write 工具
    '注册 write 工具及其系统提示词指引'
    def 段落文本(上下文元):#按作用域
        '本作用域无 write 则空；有 edit 时补定向修改指引'
        作用域=上下文元['scope'] if 'scope' in 上下文元 else None#作用域
        if 上下文.tools.获取('write',作用域) is None:#看不见
            return ''#空
        文=写提示文本前缀#前半
        if 上下文.tools.获取('edit',作用域) is not None:#有edit
            文+=' and prefer edit for targeted changes'#补定向
        return 文+'.'#收尾
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:write',#段落名
        'order':上下文.systemPrompt.获取段落顺序('TOOL_WRITE'),#中央段落顺序
        'text':段落文本,#动态指引
    })#系统提示词结束
    参数表={#参数schema
        'file_path':{'type':'string','required':True,'description':'Path to write, resolved by the filesystem backend. Provide `file_path` before `content` in the arguments.'},#写入路径，参数里先写路径
        'content':{'type':'string','required':True,'description':'Full UTF-8 text content to write.'},#完整内容
    }#基础参数
    if len(沙箱.升级模式)>0:#隔离后端才展开升级字段
        参数表.update(沙箱.模式字段())#升级字段
    def 渲染(参数,值):#模型可见确认信封
        '模型可见确认信封'
        return [{'type':'text','text':格式化写输出(值['path'],值)}]#确认信封
    def 呈现元数据(参数,值):#结果呈现用的 diff meta
        '结果呈现用的 diff meta'
        if 'before' not in 值 or 值['before'] is None:#没有before则无hunk
            差异列表=[]#空diff列表
        else:#有基准文本
            差异列表=[{'path':项['path'],'oldText':项['oldText'],'newText':项['newText']} for 项 in 计算块差异(值['path'],值['before'],值['after'])]#只保留展示字段
        return {'operation':值['operation'],'path':值['path'],'diffs':差异列表}#含操作与路径的diff meta
    def 无条件意图():#裸默认无条件写入
        '裸默认无条件写入'
        return None#无条件
    def 执行(参数,执行上下文):#执行写入
        '执行写入'
        输入=解析写参数(参数)#校验参数
        沙箱政策=沙箱.解析政策('write',参数,执行上下文)#解析沙箱策略
        目标=上下文.fs.解析(输入['路径'],会话解析选项(上下文,执行上下文))#按当前目录解析稳定目标
        意图=上下文.链式拦截('fs/write-intent',目标,执行上下文,无条件意图)#取写意图
        try:#调用提供方写入
            结局=上下文.fs.写文本(目标,输入['内容'],意图,执行上下文['signal'] if 'signal' in 执行上下文 else None,沙箱政策)#原子写入
        except Exception as 错误:#写入失败
            补救后=补救文件系统错误(沙箱.映射错误(错误,沙箱政策),目标['displayPath'])#映射并补救
            if 补救后 is 错误:#原错误
                raise#原样
            raise 补救后#换成面向模型的诊断
        结果={键:值 for 键,值 in 结局.items() if 键!='version'}#结果不含版本
        上下文.广播('fs/observed',目标,{'kind':'present','version':结局['version']},执行上下文)#记录观察
        返回={'path':上下文.fs.进程路径(目标)}#执行世界中的规范路径
        返回.update(结果)#其余结果字段；若自带 path 则覆盖
        return 返回#结构化结果
    def 呈现调用(参数):#调用时 diff 卡片
        """调用时 diff 卡片。
        拿不到先前文件内容，因此 oldText 为 None 也表示覆盖
        """
        return {#卡片
            'card':'diff',#diff卡片
            'title':'Write '+参数['file_path'],#标题
            'diffs':[{'path':参数['file_path'],'oldText':None,'newText':参数['content']}],#整文件作为新文本
            'locations':[{'path':参数['file_path']}],#位置
        }#卡片结束
    def 呈现结果(参数,结果):#结果时 diff 卡片
        """结果时 diff 卡片。
        错误结果不展示。
        畸形则回退到调用参数
        """
        if 'isError' in 结果 and 结果['isError']:#错误结果
            return None#不展示diff
        元数据=结果['meta'] if 'meta' in 结果 else None#持久元数据
        差异列表=从元数据取差异(元数据)#从meta收窄hunk
        if 差异列表 is None:#创建、未改或畸形
            记下的路径=从元数据取路径(元数据)#记下的路径
            差异列表=[{'path':参数['file_path'] if 记下的路径 is None else 记下的路径,'oldText':None,'newText':参数['content']}]#回退
        return {'card':'diff','title':'Write '+参数['file_path'],'diffs':差异列表}#结果diff卡片
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
            'presentationMeta':呈现元数据,#结果呈现用的diff meta
        },#output结束
        'execute':执行,#执行写入
        'presentCall':呈现调用,#调用时diff卡片
        'presentResult':呈现结果,#结果时diff卡片
    }))#register结束
