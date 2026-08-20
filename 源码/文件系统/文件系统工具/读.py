"""面向模型的 UTF-8 读取。它做一次提供方 stat 以取得类型、路由与观察版本，对流式大文件或大小未知的文件做流式读取，渲染有界窗口，然后发出观察。对齐上游 tool-fs/src/read.ts。"""
import re#读信封正文提取
from tools import 定义工具#导入工具定义
from .读渲染 import 构建窗口,格式化读输出,路径语言,从元数据取读窗口#导入读窗口与展示
from .读目标 import 解析普通读目标#导入普通文件目标解析
from .辅助 import 取字段,试取,解开,是否整数,是否有限数#字段读取与数字判定

读行数上限=2000#默认读行数上限
流最小大小=10*1024*1024#默认10MiB起流式读取
读信封正文=re.compile(r'^<path>[^\n]*</path>\n<type>file</type>\n<content>\n([\s\S]*)\n</content>$')#抽出信封内正文
读提示文本=(#把 read 定位为带行号检视的稳定系统提示词指引（字面量不翻译）
    'Use the read tool — not shell commands like cat — to inspect text files. Results include line numbers. Use offset and limit to continue reading large files.'#用read而不是cat，带行号与分页
)#读提示文本结束
def 解析正整数(值,名):#解析正整数参数
    """把工具参数收成正整数。非有限数、非整数或小于 1 时抛错；消息键名保持上游英文，供模型与测试对照。"""
    if (not 是否有限数(值)) or (not 是否整数(值)) or 值<1:#非有限、非整数或小于1
        raise Exception(名+' must be a positive integer')#参数非法
    return 值#合法正整数

def 解析读参数(参数,最大行数):#校验读工具参数
    """校验 schema DSL 表达不了的值约束。offset 缺省为 1，limit 缺省为 maxLimit。"""
    if len(取字段(参数,'file_path').strip())==0:#路径不得为空
        raise Exception('file_path must be a non-empty string')#路径不得为空
    偏移=1 if 试取(参数,'offset') is None else 解析正整数(取字段(参数,'offset'),'offset')#缺省从第1行
    行数=最大行数 if 试取(参数,'limit') is None else 解析正整数(取字段(参数,'limit'),'limit')#缺省用部署上限
    if 行数>最大行数:#不得超过部署上限
        raise Exception('limit must be less than or equal to '+str(最大行数))#不得超过部署上限
    return {'路径':取字段(参数,'file_path'),'偏移':偏移,'行数':行数}#内部输入

def 应用读工具(上下文,上限):#注册 read 工具
    """注册 read 工具及其系统提示词指引。"""
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:read',#段落名
        'order':100,#排序
        'text':读提示文本,#指引用read而不是cat
    })#系统提示词结束
    def 渲染(参数,值):#渲染模型可见信封
        """渲染模型可见信封。"""
        输入=解析读参数(参数,上限['行数'])#还原请求窗口
        窗口行=取字段(值,'lines')#窗口行
        if len(窗口行)>0:#有窗口行
            末行=窗口行[-1]['number']#窗口末行
        else:#空窗口
            末行=max(0,取字段(值,'offset')-1)#offset前一行
        因字节截断=len(窗口行)<输入['行数'] and 末行<取字段(值,'totalLines')#行未满且未到EOF则是字节截断
        结果={'offset':取字段(值,'offset'),'lines':窗口行,'totalLines':取字段(值,'totalLines')}#窗口结果
        if 因字节截断:#字节截断
            结果['truncatedByBytes']=True#标记
        return [{'type':'text','text':格式化读输出(取字段(值,'path'),结果)}]#单个文本块
    def 呈现元数据(参数,值):#结果展示用的 read meta
        """结果展示用的 read meta。"""
        语言=路径语言(取字段(值,'path'))#按扩展名推导高亮语言
        元数据={#meta载荷
            'path':取字段(值,'path'),#路径
            'offset':取字段(值,'offset'),#起始行
            'lines':[{'number':行['number'],'text':行['text']} for 行 in 取字段(值,'lines')],#行窗口
            'totalLines':取字段(值,'totalLines'),#总行数
        }#meta结束
        if 语言 is not None:#有语言提示
            元数据['lang']=语言#带上
        return 元数据#meta
    def 执行(参数,执行上下文):#执行读取
        """执行读取。"""
        输入=解析读参数(参数,上限['行数'])#校验参数
        已解析=解开(解析普通读目标(上下文,执行上下文,输入['路径']))#解析普通文件目标
        目标=已解析['target']#目标
        信息=已解析['info']#stat结果
        大小=试取(信息,'size')#文件大小
        if 大小 is None or 大小>=上限['流最小大小']:#未知大小或达到阈值
            块们=解开(上下文.fs.流文本(目标,试取(执行上下文,'signal')))#流式块
        else:#小文件
            块们=[解开(上下文.fs.读文本(目标,试取(执行上下文,'signal')))]#整文件作为单块
        窗口=构建窗口(#构建有界行窗口
            块们,#文本块
            {'offset':输入['偏移'],'limit':输入['行数'],'maxLineLength':上限['最大行长'],'maxBytes':上限['最大字节']},#窗口上限
            取字段(目标,'displayPath'),#错误消息用的展示路径
        )#构建窗口结束
        结局={#结构化读结果
            'path':取字段(目标,'displayPath'),#展示路径
            'offset':输入['偏移'],#起始行
            'lines':窗口['lines'],#窗口行
            'totalLines':窗口['totalLines'],#总行数
        }#结局结束
        上下文.emit('fs/observed',目标,{'kind':'present','version':取字段(信息,'version')},执行上下文)#记录观察
        return 结局#返回结构化结果
    def 呈现结果(参数,结果):#结果时 read 卡片
        """结果时 read 卡片。畸形或缺失 meta 降为 None。"""
        if 取字段(结果,'isError'):#错误结果
            return None#不展示read卡片
        元数据=从元数据取读窗口(试取(结果,'meta'))#从meta收窄窗口
        if 元数据 is None:#畸形
            return None#通用回退
        内容=取字段(结果,'content')#内容块
        唯一=内容[0] if len(内容)==1 else None#唯一内容块
        文本=取字段(唯一,'text') if 试取(唯一,'type')=='text' else None#必须是文本块
        if 文本 is None:#没有文本
            return None#回退
        匹配=读信封正文.match(文本)#抽出信封内正文
        if 匹配 is None:#不是read信封
            return None#回退
        卡片={#read卡片
            'card':'read',#read卡片
            'path':元数据['path'],#路径
            'offset':元数据['offset'],#起始行
            'lines':元数据['lines'],#行窗口
            'totalLines':元数据['totalLines'],#总行数
            'content':[{'type':'text','text':匹配.group(1)}],#剥信封后的正文
        }#卡片结束
        if 试取(元数据,'lang') is not None:#有语言提示
            卡片['lang']=元数据['lang']#带上
        return 卡片#卡片
    def 呈现调用(参数):#调用时通用卡片
        """调用时通用卡片。窗口反映原始参数。"""
        偏移=试取(参数,'offset')#起始行
        行数=试取(参数,'limit')#行数上限
        if 行数 is not None and 行数>0:#给出了正limit
            起点=1 if 偏移 is None else 偏移#缺省从第1行
            窗口=' ('+str(起点)+' - '+str(起点+行数-1)+')'#显示起止行
        elif 偏移 is not None:#只有offset
            窗口=' (from line '+str(偏移)+')'#显示从某行起
        else:#无窗口参数
            窗口=''#裸标题
        return {#卡片
            'card':'generic',#通用卡片
            'title':'Read '+取字段(参数,'file_path')+窗口,#标题含窗口
            'kind':'read',#读种类图标
            'locations':[{'path':取字段(参数,'file_path'),'line':1 if 偏移 is None else 偏移}],#跟随到起始行
        }#卡片结束
    def 并发安全(参数):#读并发安全
        """读并发安全。"""
        return True#读并发安全
    上下文.tools.登记(定义工具({#注册read工具
        'name':'read',#工具名
        'description':'Read a UTF-8 text file and return line-numbered content.',#工具描述
        'parameters':{#参数schema
            'file_path':{'type':'string','required':True,'description':'Path to read, resolved by the filesystem backend.'},#读取路径
            'offset':{'type':'number','description':'1-based first line to return. Defaults to 1.'},#起始行
            'limit':{'type':'number','description':'Maximum number of lines to return. Defaults to '+str(上限['行数'])+'.'},#行数上限
        },#parameters结束
        'output':{#结构化输出
            'schema':{#输出schema
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'path':{'type':'string','required':True},#已解析路径
                    'offset':{'type':'integer','required':True},#起始行
                    'lines':{#窗口行
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#每行
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#行字段
                                'number':{'type':'integer','required':True},#行号
                                'text':{'type':'string','required':True},#行文本
                            },#properties结束
                        },#items结束
                    },#lines结束
                    'totalLines':{'type':'integer','required':True},#文件总行数
                },#properties结束
            },#schema结束
            'render':渲染,#渲染模型可见信封
            'presentationMeta':呈现元数据,#结果展示用的read meta
        },#output结束
        'isConcurrencySafe':并发安全,#读并发安全
        'execute':执行,#执行读取
        'presentResult':呈现结果,#结果时read卡片
        'presentCall':呈现调用,#调用时通用卡片
    }))#register结束
