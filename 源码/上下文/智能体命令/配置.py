'工作区指令发现与渲染的配置归一化'
import os#智能体根目录解析
from ...基础设施.通用工具 import 紧凑json编码,相对正斜杠路径
from ...工具.主目录路径 import 展开家目录路径,解析主目录#导入家目录展开与 harness 根解析

def 已中止(信号):
    '信号按 Event 定死。无信号视为未中止'
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 已置位
from ...依赖.schemastery import 字符串字段,数字字段,整数字段,列表字段
from .异常 import 智能体命令错误

__all__=['配置','解析配置','工作区基线身份','默认项目根标记','默认指令文件候选','默认本地指令文件候选','默认单源字节','智能体命令错误','已中止','若已中止则抛出']#公开面

默认项目根标记=('.git',)#默认项目根标记
默认指令文件候选=('AGENTS.md','CLAUDE.md')#默认同目录基线候选
默认本地指令文件候选=('AGENTS.local.md','CLAUDE.local.md')#默认同目录本地覆盖候选
默认单源字节=1048576#单文件默认UTF-8字节上限
保留路径段=set(('','.','..'))#禁止作为候选文件名的路径段

配置={#Config的Schemastery校验；行配置不能改写进程家目录
    'projectRootMarkers':列表字段(字符串字段(),默认值=list(默认项目根标记)),#根标记默认.git
    'maxBytes':数字字段(可空=False),#渲染预算必填
    'maxSourceBytes':整数字段(最小=1,默认值=默认单源字节),#单源默认上限，正整数
    'instructionFileCandidates':列表字段(字符串字段(),默认值=list(默认指令文件候选)),#基线候选默认
    'localInstructionFileCandidates':列表字段(字符串字段(),默认值=list(默认本地指令文件候选)),#本地覆盖默认
}#Config校验结束

def 若已中止则抛出(信号):
    '已中止则抛出承载原因的异常'
    if not 已中止(信号):#无信号或仍活着
        return#仍活着
    if 信号.原因 is not None:#有承载异常
        raise 信号.原因#抛出
    raise 智能体命令错误('aborted')#默认中止

def 工作区基线身份(配置值,工作目录,项目根):#计算工作区基线身份
    '标识一份基线的发现、优先级与预算语义。返回供恢复时兼容检查的稳定序列化身份'
    return 紧凑json编码({#序列化发现与预算字段
        'projectRoot':相对正斜杠路径(项目根,工作目录),#相对cwd的项目根
        'projectRootMarkers':配置值['projectRootMarkers'],#根标记
        'maxBytes':配置值['maxBytes'],#渲染预算
        'maxSourceBytes':配置值['maxSourceBytes'],#单源上限
        'instructionFileCandidates':配置值['instructionFileCandidates'],#基线候选
        'localInstructionFileCandidates':配置值['localInstructionFileCandidates'],#本地覆盖候选
    })#紧凑JSON身份

def 解析指令文件候选(候选列表,回退):#过滤合法同目录候选名
    '过滤空段、.、..以及含路径分隔符的名字'
    源=list(回退) if 候选列表 is None else 候选列表#缺省用回退列表
    return [名 for 名 in 源 if 名 not in 保留路径段 and ('\\' not in 名) and ('/' not in 名)]#去掉非法名

def 解析智能体主目录(已配置=None):#解析共享智能体配置根
    '显式路径优先，其次非空白 DSH_AGENTS_HOME，否则 ~/.agents'
    来自环境=os.environ.get('DSH_AGENTS_HOME')#读取覆盖
    if 已配置 is not None:#显式配置优先
        选中=已配置#显式路径
    elif 来自环境 is not None and len(str(来自环境).strip())>0:#非空白环境变量
        选中=来自环境#环境覆盖
    else:#都没有
        选中=os.path.join(os.path.expanduser('~'),'.agents')#默认~/.agents
    return os.path.abspath(展开家目录路径(选中))#展开波浪号并规范化

def 智能体主目录展示(已解析主目录):#共享根的面向模型标签
    '默认根标为 ~/.agents，其余标为 $DSH_AGENTS_HOME'
    默认=os.path.abspath(os.path.join(os.path.expanduser('~'),'.agents'))#默认绝对根
    return '~/.agents' if 已解析主目录==默认 else '$DSH_AGENTS_HOME'#不返回机器路径

def 解析发现配置(配置值):#解析发现配置
    '解析渲染指令内容之前所用的配置子集。返回归一化的家目录、根标记与指令候选'
    根标记=配置值['projectRootMarkers'] if 'projectRootMarkers' in 配置值 else None#可选根标记
    return {#组装发现字段
        'dshHome':解析主目录(配置值['dshHome'] if 'dshHome' in 配置值 else None),#已解析则沿用，否则进程根
        'agentsHome':解析智能体主目录(配置值['agentsHome'] if 'agentsHome' in 配置值 else None),#共享智能体根
        'projectRootMarkers':list(默认项目根标记) if 根标记 is None else 根标记,#根标记缺省.git
        'instructionFileCandidates':解析指令文件候选(配置值['instructionFileCandidates'] if 'instructionFileCandidates' in 配置值 else None,默认指令文件候选),#过滤基线候选
        'localInstructionFileCandidates':解析指令文件候选(配置值['localInstructionFileCandidates'] if 'localInstructionFileCandidates' in 配置值 else None,默认本地指令文件候选),#过滤本地覆盖
    }#返回发现配置

def 解析配置(配置值):#解析完整运行时配置
    '解析默认值、进程家目录以及合法的同目录候选。行里未声明的字段不能改写进程家目录'
    发现入={}#只转发发现控件，不转发家目录
    if 'projectRootMarkers' in 配置值 and 配置值['projectRootMarkers'] is not None:#声明了根标记
        发现入['projectRootMarkers']=配置值['projectRootMarkers']#转发
    if 'instructionFileCandidates' in 配置值 and 配置值['instructionFileCandidates'] is not None:#声明了基线候选
        发现入['instructionFileCandidates']=配置值['instructionFileCandidates']#转发
    if 'localInstructionFileCandidates' in 配置值 and 配置值['localInstructionFileCandidates'] is not None:#声明了本地覆盖
        发现入['localInstructionFileCandidates']=配置值['localInstructionFileCandidates']#转发
    发现=解析发现配置(发现入)#家目录走进程解析
    发现['maxBytes']=配置值['maxBytes']#渲染预算
    单源=配置值['maxSourceBytes'] if 'maxSourceBytes' in 配置值 else None#可选单源
    发现['maxSourceBytes']=默认单源字节 if 单源 is None else 单源#单源上限缺省用默认
    return 发现#完整运行时配置
