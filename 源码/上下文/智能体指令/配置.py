"""工作区指令发现与渲染的配置归一化。"""
import json,os#序列化身份与相对路径
from ...依赖 import schemastery#外部依赖胶水
模式=schemastery.模式#导入配置校验
from ..工作区路径 import 解析主目录#导入harness家目录解析

__all__=['配置','解析配置','工作区基线身份','默认项目根标记','默认指令文件候选','默认本地指令文件候选','默认单源字节']#公开面

默认项目根标记=('.git',)#默认项目根标记
默认指令文件候选=('AGENTS.md','CLAUDE.md')#默认同目录基线候选
默认本地指令文件候选=('AGENTS.local.md','CLAUDE.local.md')#默认同目录本地覆盖候选
默认单源字节=1048576#单文件默认UTF-8字节上限
保留路径段=set(('','.','..'))#禁止作为候选文件名的路径段

配置=模式.对象({#Config的Schemastery校验
    'dshHome':模式.字符串(),#家目录字符串
    'projectRootMarkers':模式.数组(模式.字符串()).默认(list(默认项目根标记)),#根标记默认.git
    'maxBytes':模式.数字().必填(),#渲染预算必填
    'maxSourceBytes':模式.数字().默认(默认单源字节),#单源默认上限
    'instructionFileCandidates':模式.数组(模式.字符串()).默认(list(默认指令文件候选)),#基线候选默认
    'localInstructionFileCandidates':模式.数组(模式.字符串()).默认(list(默认本地指令文件候选)),#本地覆盖默认
})#Config校验结束
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 工作区基线身份(配置值,工作目录,项目根):#计算工作区基线身份
    """标识一份基线的发现、优先级与预算语义。返回供恢复时兼容检查的稳定序列化身份。"""
    return json.dumps({#序列化发现与预算字段
        'projectRoot':os.path.relpath(项目根,工作目录).replace('\\','/'),#相对cwd的项目根
        'projectRootMarkers':配置值['projectRootMarkers'],#根标记
        'maxBytes':配置值['maxBytes'],#渲染预算
        'maxSourceBytes':配置值['maxSourceBytes'],#单源上限
        'instructionFileCandidates':配置值['instructionFileCandidates'],#基线候选
        'localInstructionFileCandidates':配置值['localInstructionFileCandidates'],#本地覆盖候选
    },ensure_ascii=False,separators=(',',':'))#紧凑JSON身份

def 解析指令文件候选(候选们,回退):#过滤合法同目录候选名
    """过滤空段、.、..以及含路径分隔符的名字。"""
    源=list(回退) if 候选们 is None else 候选们#缺省用回退列表
    return [名 for 名 in 源 if 名 not in 保留路径段 and ('\\' not in 名) and ('/' not in 名)]#去掉非法名

def 解析发现配置(配置值):#解析发现配置
    """解析渲染指令内容之前所用的配置子集。返回归一化的家目录、根标记与指令候选。"""
    根标记=取字段(配置值,'projectRootMarkers')#可选根标记
    return {#组装发现字段
        'dshHome':解析主目录(取字段(配置值,'dshHome')),#解析harness家目录
        'projectRootMarkers':list(默认项目根标记) if 根标记 is None else 根标记,#根标记缺省.git
        'instructionFileCandidates':解析指令文件候选(取字段(配置值,'instructionFileCandidates'),默认指令文件候选),#过滤基线候选
        'localInstructionFileCandidates':解析指令文件候选(取字段(配置值,'localInstructionFileCandidates'),默认本地指令文件候选),#过滤本地覆盖
    }#返回发现配置

def 解析配置(配置值):#解析完整运行时配置
    """解析默认值、harness 家目录以及合法的同目录候选。返回归一化运行时配置。"""
    发现=解析发现配置(配置值)#展开发现子集
    发现['maxBytes']=取字段(配置值,'maxBytes')#渲染预算
    单源=取字段(配置值,'maxSourceBytes')#可选单源
    发现['maxSourceBytes']=默认单源字节 if 单源 is None else 单源#单源上限缺省用默认
    return 发现#完整运行时配置
