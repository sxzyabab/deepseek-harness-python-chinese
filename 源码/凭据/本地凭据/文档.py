"""凭证 YAML 文档的解析、渲染与仅所有者权限检查。

versioned `refs` + `records` 布局（DOCUMENT_VERSION=1）。
公开面仅中文名。

注释往返：上游用 `yaml` 包的 CST/`parseDocument` 保注释编辑；本包 `pyproject.toml` 仅依赖
`pyyaml>=6`、未引入 `ruamel.yaml`，故保持 PyYAML `safe_load`/`safe_dump`——编辑以结构正确为先，
不保留手写注释与未触碰条目的版式。若日后显式加入 `ruamel.yaml`，可将渲染改为 round-trip。
"""
import os,errno,io,copy#路径、错误码、文本流与深拷贝
import yaml#PyYAML
from ..凭据 import 凭证引用,解析凭证键#引用与记录键
from ...工具.主目录路径 import 规范化监视路径#监视路径规范化

凭证文件名='.credentials.yaml'#harness 主目录内凭证文档的基名
文档版本=1#本构建读写的布局版本
组其他人位=0o077#所有者以外的权限位
字符串流=io.StringIO#内存序列化

__all__=[#仅中文公开名
    '凭证文件名','文档版本','补错误码','是否缺席','断言无空字节',
    '解析凭证文档','渲染扁平迁移','渲染引用','渲染记录',
    '读文档文本','断言仅所有者','同json值',
]#公开面结束


def 补错误码(错误):
    """给逃出的 OSError 补上 Node 风格 `code`。"""
    if isinstance(错误,OSError) and getattr(错误,'code',None) is None:#尚无 code
        表={
            errno.ENOENT:'ENOENT',
            errno.ENOTDIR:'ENOTDIR',
            errno.EISDIR:'EISDIR',
            errno.EACCES:'EACCES',
            errno.EPERM:'EPERM',
        }#常见映射
        错误.code=表.get(错误.errno) or errno.errorcode.get(错误.errno) or 'EIO'#写入
    return 错误#原错误


def 是否缺席(错误):
    """判定缺席错误。"""
    if getattr(错误,'code',None)=='ENOENT':#已带码
        return True#缺席
    return isinstance(错误,OSError) and 错误.errno==errno.ENOENT#按 errno


def 断言无空字节(文件名):
    """空字节在到达操作系统之前拒绝。"""
    if '\0' in 文件名:#含空字节
        错误=ValueError("The argument 'path' must be a string or Uint8Array without null bytes. Received "+repr(文件名))#对齐 Node
        错误.code='ERR_INVALID_ARG_VALUE'#码
        raise 错误#抛


def 描述yaml错误(错误):
    """描述一次 YAML 解析失败，且不引用源文。"""
    标记=getattr(错误,'problem_mark',None)#行列
    if 标记 is None:#无
        位置=''#空
    else:
        位置=' at line '+str(标记.line+1)+', column '+str(标记.column+1)#1 起算
    码=getattr(错误,'code',None) or type(错误).__name__#码
    return str(码)+位置#诊断


def 解析凭证文档(文本,文件名):
    """解析 versioned 凭证文档为 {refs, records}。空文档是空存储。"""
    try:
        根=yaml.safe_load(文本)#解析
    except yaml.YAMLError as 错误:
        raise Exception('credentials-local: invalid document at '+文件名+': '+描述yaml错误(错误))#诊断
    if 根 is None:#空
        return {'refs':{},'records':{}}#空存储
    if not isinstance(根,dict) or isinstance(根,list):#非映射
        raise TypeError('credentials-local: '+文件名+' must be a mapping')#拒绝
    键列表=list(根.keys())#顶层键
    if len(键列表)==0:#空映射
        return {'refs':{},'records':{}}#空存储
    if 'version' not in 根:#预发布扁平
        raise Exception(
            'credentials-local: '+文件名+' uses the pre-release flat layout. Add `version: '+str(文档版本)+'`'
            +' and nest the existing '+str(len(键列表))+' '
            +('entry' if len(键列表)==1 else 'entries')+' under `refs:`.'
            +' No values need to change.'
        )#指引迁移
    if 根['version']!=文档版本:#版本不符
        raise Exception(
            'credentials-local: '+文件名+' declares version '+repr(根['version'])+';'
            +' this build reads version '+str(文档版本)
        )#拒绝
    for 键 in 键列表:#未知顶层
        if 键 not in ('version','refs','records'):#越界
            raise Exception('credentials-local: unknown top-level key "'+str(键)+'" in '+文件名)#拒绝
    return {
        'refs':_解析引用节(根.get('refs'),文件名),
        'records':_解析记录节(根.get('records'),文件名),
    }#两节


def 渲染扁平迁移(文本):
    """识别预发布扁平布局并渲染 version-1；否则 None。"""
    try:
        根=yaml.safe_load(文本)#解析
    except yaml.YAMLError:
        return None#非目标
    if not isinstance(根,dict) or len(根)==0:#非非空映射
        return None#拒
    for 行 in 文本.split('\n'):#指令
        if 行.startswith('%') or 行.startswith('---') or 行.startswith('...'):#指令
            return None#拒
    for 键,值 in 根.items():#逐对
        文字键=键 if isinstance(键,str) else str(键)#键
        if 文字键=='version':#已版本化
            return None#拒
        try:
            凭证引用(文字键)#POSIX
        except TypeError:
            return None#拒
        if not isinstance(值,str) or len(值)==0:#值非法
            return None#拒
    体='\n'.join(('' if 行=='' else '  '+行) for 行 in 文本.split('\n'))#缩进
    结果='version: '+str(文档版本)+'\nrefs:\n'+体#拼
    if not 结果.endswith('\n'):#换行
        结果=结果+'\n'#补
    return 结果#迁移文本


def _节为映射(节,名,文件名):
    """节为普通映射；缺席与 null 都表示空。"""
    if 节 is None:#缺席
        return {}#空
    if not isinstance(节,dict) or isinstance(节,list):#非映射
        raise TypeError('credentials-local: "'+名+'" in '+文件名+' must be a mapping')#拒绝
    return 节#收窄


def _解析引用节(节,文件名):
    """接纳 refs。"""
    条目={}#结果
    for 键,值 in _节为映射(节,'refs',文件名).items():#逐项
        文字键=键 if isinstance(键,str) else str(键)#键
        凭证引用(文字键)#校验
        if not isinstance(值,str):#类型
            raise TypeError('credentials-local: the value for "'+文字键+'" in '+文件名+' must be a string')#拒绝
        if len(值)==0:#空
            raise Exception('credentials-local: the value for "'+文字键+'" in '+文件名+' is empty; remove the key instead')#拒绝
        条目[文字键]=值#收下
    return 条目#表


def _解析记录节(节,文件名):
    """接纳 records。"""
    条目={}#结果
    for 键,值 in _节为映射(节,'records',文件名).items():#逐项
        文字键=键 if isinstance(键,str) else str(键)#键
        解析凭证键(文字键)#校验
        条目[文字键]=_解析记录(文字键,值,文件名)#记录
    return 条目#表


def _解析记录(键,值,文件名):
    """接纳一条记录。"""
    if not isinstance(值,dict) or isinstance(值,list):#非映射
        raise TypeError('credentials-local: record "'+键+'" in '+文件名+' must be a mapping')#拒绝
    种类=值.get('kind')#种类
    if 种类=='api-key':#api
        _断言字段(键,值,('kind','key','env'),文件名)#词表
        密钥=值.get('key')#密钥
        if 密钥 is not None and (not isinstance(密钥,str) or len(密钥)==0):#非法
            raise TypeError('credentials-local: record "'+键+'" in '+文件名+' has a non-string or empty key')#拒绝
        环境=_解析记录环境(键,值.get('env'),文件名)#环境
        记录={'kind':'api-key'}#基
        if 密钥 is not None:#有密钥
            记录['key']=密钥#写
        if 环境 is not None:#有环境
            记录['env']=环境#写
        return 记录#返回
    if 种类=='grant':#授权
        _断言字段(键,值,('kind','payload'),文件名)#词表
        if 'payload' not in 值:#缺
            raise Exception('credentials-local: record "'+键+'" in '+文件名+' has no payload')#拒绝
        断言json值('record "'+键+'" payload in '+文件名,值['payload'],set())#JSON
        return {'kind':'grant','payload':值['payload']}#返回
    if 种类 is None:#缺
        raise Exception('credentials-local: record "'+键+'" in '+文件名+' has no kind')#拒绝
    raise Exception('credentials-local: record "'+键+'" in '+文件名+' has unknown kind '+repr(种类))#未知


def _断言字段(键,字段,允许,文件名):
    """拒绝未知字段。"""
    for 名 in 字段.keys():#逐字段
        if 名 not in 允许:#越界
            raise Exception('credentials-local: record "'+键+'" in '+文件名+' has unknown field "'+str(名)+'"')#拒绝


def _解析记录环境(键,环境,文件名):
    """api-key 的 env 映射。"""
    if 环境 is None:#缺席
        return None#无
    if not isinstance(环境,dict) or isinstance(环境,list):#非映射
        raise TypeError('credentials-local: record "'+键+'" in '+文件名+' has a non-mapping env')#拒绝
    解析={}#结果
    for 名,值 in 环境.items():#逐项
        文字名=名 if isinstance(名,str) else str(名)#名
        凭证引用(文字名)#校验
        if not isinstance(值,str) or len(值)==0:#非法
            raise TypeError('credentials-local: record "'+键+'" env "'+文字名+'" in '+文件名+' must be a non-empty string')#拒绝
        解析[文字名]=值#写
    return 解析#表


def 断言可存api密钥(键,记录):
    """写前拒绝读路径不会接纳的 api-key。"""
    if 'key' in 记录 and 记录['key'] is not None and len(记录['key'])==0:#空密钥
        raise TypeError('credentials-local: record "'+键+'" has an empty key; omit the field instead')#拒绝
    for 名,值 in (记录.get('env') or {}).items():#环境
        凭证引用(名)#名
        if len(值)==0:#空
            raise TypeError('credentials-local: record "'+键+'" env "'+名+'" must be a non-empty string')#拒绝


def 断言json值(何处,值,已见):
    """拒绝无法 JSON 往返的载荷。"""
    if 值 is None or isinstance(值,(str,bool)):#标量
        return#OK
    if isinstance(值,int) and not isinstance(值,bool):#整数
        return#OK
    if isinstance(值,float):#浮点
        if 值==值 and 值 not in (float('inf'),float('-inf')):#有限
            return#OK
        raise TypeError('credentials-local: '+何处+' holds a non-finite number')#非有限
    if isinstance(值,(dict,list)):#容器
        身份=id(值)#身份
        if 身份 in 已见:#环
            raise TypeError('credentials-local: '+何处+' is cyclic')#环
        已见.add(身份)#入途
        if isinstance(值,dict):#映射
            if type(值) is not dict:#非普通
                raise TypeError('credentials-local: '+何处+' holds a value JSON cannot represent')#拒
            for 嵌 in 值.values():#递归
                断言json值(何处,嵌,已见)#检
        else:#列表
            for 嵌 in 值:#递归
                断言json值(何处,嵌,已见)#检
        已见.discard(身份)#离途
        return#OK
    raise TypeError('credentials-local: '+何处+' holds a value JSON cannot represent')#不可表示


def _可编辑根(文本):
    """从缓存文本建可编辑根；盖版本戳。"""
    if 文本 is None:#缺席
        根={'version':文档版本}#新
    else:
        根=yaml.safe_load(文本) or {}#再解析
        if not isinstance(根,dict):#非映射
            根={}#空
        根['version']=文档版本#盖戳
    return 根#根


def _序列化(根):
    """序列化根映射。"""
    if 根.keys()=={'version'} or (len(根)==1 and 'version' in 根 and 'refs' not in 根 and 'records' not in 根):#仅版本
        # 空存储：保留 version 以便下一启动走 versioned 路径；无 refs/records 节
        pass#保持
    # 清理空节
    if 'refs' in 根 and (根['refs'] is None or 根['refs']=={}):#空 refs
        del 根['refs']#删
    if 'records' in 根 and (根['records'] is None or 根['records']=={}):#空 records
        del 根['records']#删
    文本=yaml.safe_dump(根,allow_unicode=True,default_flow_style=False,sort_keys=False)#序列化
    if not 文本.endswith('\n'):#换行
        文本=文本+'\n'#补
    return 文本#文本


def 渲染引用(文本,引用,值):
    """设置或删除一条引用。"""
    根=_可编辑根(文本)#根
    if 'refs' not in 根 or not isinstance(根.get('refs'),dict):#无节
        根['refs']={}#建
    if 值 is None:#删除
        根['refs'].pop(引用,None)#删
    else:
        根['refs'][引用]=值#写
    return _序列化(根)#文本


def 渲染记录(文本,键,记录):
    """写入或删除一条记录。"""
    根=_可编辑根(文本)#根
    if 'records' not in 根 or not isinstance(根.get('records'),dict):#无节
        根['records']={}#建
    if 记录 is None:#删除
        根['records'].pop(键,None)#删
    else:
        根['records'][键]=copy.deepcopy(记录)#整份替换
    return _序列化(根)#文本


def 读文档文本(文件名):
    """按 utf8 读文档。"""
    断言无空字节(文件名)#空字节
    try:
        with open(文件名,'r',encoding='utf-8',newline='') as 文件:#打开
            return 文件.read()#全文
    except OSError as 错误:
        raise 补错误码(错误)#补码


def 断言仅所有者(文件名):
    """拒绝其他 OS 用户也能读的凭证文档。"""
    断言无空字节(文件名)#空字节
    try:
        模式=os.stat(文件名).st_mode#mode
    except OSError as 错误:
        补错误码(错误)#补
        if not 是否缺席(错误):#非缺席
            raise 错误#抛
        规范化监视路径(文件名)#规范化
        return#缺席通过
    if os.name=='nt':#Windows
        return#跳过
    越权=模式&组其他人位#越权位
    if 越权==0:#通过
        return#过
    八进制=format(模式&0o777,'o')#八进制
    raise Exception('credentials-local: '+文件名+' is readable beyond its owner (mode '+八进制+'); run "chmod 600 '+文件名+'" before starting again')#拒绝


def 同json值(左,右):
    """两个已接纳 JSON 值的结构相等。"""
    if 左 is 右:#同一
        return True#等
    if type(左)!=type(右):#类型
        return False#不等
    if isinstance(左,list):#列表
        if len(左)!=len(右):#长
            return False#不等
        return all(同json值(a,b) for a,b in zip(左,右))#逐项
    if isinstance(左,dict):#映射
        if set(左.keys())!=set(右.keys()):#键
            return False#不等
        return all(同json值(左[k],右[k]) for k in 左)#递归
    return 左==右#标量


# 兼容旧名
渲染文档=渲染引用#旧调用方
