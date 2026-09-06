"""工作区指令发现与渲染的配置归一化。"""
import json,os#序列化身份与相对路径
from ...依赖.schemastery import 字符串字段,数字字段,列表字段#配置字段
from ...工具.工作区路径 import 解析主目录#导入harness家目录解析

__all__=['配置','解析配置','工作区基线身份','默认项目根标记','默认指令文件候选','默认本地指令文件候选','默认单源字节','智能体命令错误','已中止','若已中止则抛出']#公开面

默认项目根标记=('.git',)#默认项目根标记
默认指令文件候选=('AGENTS.md','CLAUDE.md')#默认同目录基线候选
默认本地指令文件候选=('AGENTS.local.md','CLAUDE.local.md')#默认同目录本地覆盖候选
默认单源字节=1048576#单文件默认UTF-8字节上限
保留路径段=set(('','.','..'))#禁止作为候选文件名的路径段

配置={#Config的Schemastery校验
    'dshHome':字符串字段(),#家目录字符串
    'projectRootMarkers':列表字段(字符串字段(),默认值=list(默认项目根标记)),#根标记默认.git
    'maxBytes':数字字段(可空=False),#渲染预算必填
    'maxSourceBytes':数字字段(默认值=默认单源字节),#单源默认上限
    'instructionFileCandidates':列表字段(字符串字段(),默认值=list(默认指令文件候选)),#基线候选默认
    'localInstructionFileCandidates':列表字段(字符串字段(),默认值=list(默认本地指令文件候选)),#本地覆盖默认
}#Config校验结束

class 智能体命令错误(Exception):
    """工作区指令包的异常基类。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出承载原因的异常。"""
    if 信号 is None:#无信号
        return#无信号
    if not 信号._事件.is_set():#仍活着
        return#仍活着
    if 信号._异常 is not None:#有承载异常
        raise 信号._异常#抛出
    raise 智能体命令错误('aborted')#默认中止

def 工作区基线身份(配置值,工作目录,项目根):#计算工作区基线身份
    """标识一份基线的发现、优先级与预算语义。返回供恢复时兼容检查的稳定序列化身份。"""
    return json.dumps({#序列化发现与预算字段
        'projectRoot':os.path.relpath(项目根,工作目录).replace('\\','/'),#相对cwd的项目根
        'projectRootMarkers':配置值['projectRootMarkers'],#根标记
        'maxBytes':配置值['maxBytes'],#渲染预算
        'maxSourceBytes':配置值['maxSourceBytes'],#单源上限
        'instructionFileCandidates':配置值['instructionFileCandidates'],#基线候选
        'localInstructionFileCandidates':配置值['localInstructionFileCandidates'],#本地覆盖候选
    },ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑JSON身份

def 解析指令文件候选(候选列表,回退):#过滤合法同目录候选名
    """过滤空段、.、..以及含路径分隔符的名字。"""
    源=list(回退) if 候选列表 is None else 候选列表#缺省用回退列表
    return [名 for 名 in 源 if 名 not in 保留路径段 and ('\\' not in 名) and ('/' not in 名)]#去掉非法名

def 解析发现配置(配置值):#解析发现配置
    """解析渲染指令内容之前所用的配置子集。返回归一化的家目录、根标记与指令候选。"""
    根标记=配置值['projectRootMarkers'] if 'projectRootMarkers' in 配置值 else None#可选根标记
    return {#组装发现字段
        'dshHome':解析主目录(配置值['dshHome'] if 'dshHome' in 配置值 else None),#解析harness家目录
        'projectRootMarkers':list(默认项目根标记) if 根标记 is None else 根标记,#根标记缺省.git
        'instructionFileCandidates':解析指令文件候选(配置值['instructionFileCandidates'] if 'instructionFileCandidates' in 配置值 else None,默认指令文件候选),#过滤基线候选
        'localInstructionFileCandidates':解析指令文件候选(配置值['localInstructionFileCandidates'] if 'localInstructionFileCandidates' in 配置值 else None,默认本地指令文件候选),#过滤本地覆盖
    }#返回发现配置

def 解析配置(配置值):#解析完整运行时配置
    """解析默认值、harness 家目录以及合法的同目录候选。返回归一化运行时配置。"""
    发现=解析发现配置(配置值)#展开发现子集
    发现['maxBytes']=配置值['maxBytes']#渲染预算
    单源=配置值['maxSourceBytes'] if 'maxSourceBytes' in 配置值 else None#可选单源
    发现['maxSourceBytes']=默认单源字节 if 单源 is None else 单源#单源上限缺省用默认
    return 发现#完整运行时配置
