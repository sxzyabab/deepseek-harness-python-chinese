"""收集历史发现事实，不递归预备相关当代代。"""
import os#路径与stat
from ..会话格式 import 会话格式不支持迁移错误#不支持迁移
from ..会话格式目录 import 会话格式目录,既往会话格式目录#当代与既往目录
from ..会话格式_v3到v4 import 历史子名录源#历史子名录源
from .格式 import 解析代次日志文件名#解析代次名
from .代次 import 代次源变更错误,物理身份,读解码jsonl源#代次身份与解码

def 准备名录事实(父标识,源列表,压缩,信号=None):#准备名录事实
    """经既有历史编解码器收集每个相关子的自身描述符。"""
    事实列表=[]#事实
    失败列表=[]#子本地失败
    见证列表=[]#物理见证
    for 源 in 源列表:#逐子
        _若已中止(信号)#取消
        版本=解析代次日志文件名(os.path.basename(源['path']),压缩)#代次版本
        if 版本 is None:#非规范名
            raise 会话格式不支持迁移错误(#不识别
                f"unrecognized historical child generation {os.path.basename(源['path'])}",#仅文件名
            )#错误
        见证={'path':源['path'],'identity':物理身份(os.stat(源['path']))}#见证
        见证列表.append(见证)#记下
        不可用={'childId':源['header']['id'],'childCreatedAt':源['header']['createdAt'],
            'descriptorCount':0,'descriptor':None}#不可用紧缩
        try:#解码历史源
            已恢复=读解码jsonl源(源['path'],版本,压缩,{#格式适配
                'createRestore':lambda 头,源版本=版本: (#按代次选目录
                    既往会话格式目录 if 源版本<=3 else 会话格式目录#v0–v3走既往
                ).创建恢复(头,{'recovery':'recoverable','validation':'current'}),#恢复
            },信号)#解码
        except BaseException as 错误:#读失败
            _若已中止(信号)#优先取消
            失败列表.append({'path':os.path.basename(源['path']),'error':错误})#失败
            事实列表.append(不可用)#不可用事实
            continue#下一子
        见证['identity']=已恢复['identity']#更新见证
        头=已恢复['artifact']['header']#已恢复头
        源头=源['header']#目录头
        if (头['id']!=源头['id'] or 头['createdAt']!=源头['createdAt']
            or 头.get('parentSession')!=父标识 or 头.get('origin')!='subagent'
            or any(头.get(键)!=源头.get(键) for 键 in ('cwd','isSeeded','delegationDepth','agentPreset'))):#身份漂移
            raise 代次源变更错误(os.path.basename(源['path']))#源已变
        try:#紧缩描述符
            事实=历史子名录源(已恢复['artifact'])#历史子名录源
        except BaseException as 错误:#描述符失败
            失败列表.append({'path':os.path.basename(源['path']),'error':错误})#失败
            事实列表.append(不可用)#不可用
            continue#下一子
        事实列表.append(事实)#不回写源路径
    def 校验():#发布前再核物理修订
        """每个已检视子仍持捕获时的物理修订。"""
        for 见证 in 见证列表:#逐见证
            当前=物理身份(os.stat(见证['path']))#当前stat
            身份=见证['identity']#捕获身份
            if (当前['dev']!=身份['dev'] or 当前['ino']!=身份['ino']
                or 当前['size']!=身份['size'] or 当前['mtimeNs']!=身份['mtimeNs']
                or 当前['ctimeNs']!=身份['ctimeNs']):#修订变
                raise 代次源变更错误(os.path.basename(见证['path']))#源已变
    return {'facts':事实列表,'failures':失败列表,'validate':校验}#已准备

def _若已中止(信号):#取消检查
    """已中止则抛出。"""
    if 信号 is None:#无信号
        return#无事
    if 信号.is_set():#已中止
        raise InterruptedError('session migration preparation aborted')#包装
