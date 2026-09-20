"""JSONL 会话持久化后端的磁盘格式辅助。"""
import json,os,re#JSON、路径与正则
from ...内核.会话 import 会话格式版本#本构建格式版本
from ..会话格式 import (#从会话格式导入
    会话格式日志文件名,#格式日志文件名
    解析会话格式日志文件名,#解析格式名
    会话格式不支持迁移错误,#不支持迁移
)#格式工具
from ..会话格式目录 import 会话格式目录#会话格式目录
from ..会话持久化 import 会话格式不支持错误,会话格式版本拒绝文案#持久化错误
from ...内核.会话.json值 import 冻结树#深冻结已存事件图

默认压缩='zstd'#默认 zstd
头必填=('type','version','id','createdAt','isSeeded','delegationDepth')#头行必填键
头可选=('cwd','parentSession','origin','agentPreset')#头行可选键
头键=frozenset([*头必填,*头可选])#头行全部合法键
安全码元=re.compile(r'^[A-Za-z0-9._-]\Z',re.ASCII)#路径安全码元

def 压缩后缀(压缩):#压缩后缀
    """zstd 为 `.zstd`，明文为空。"""
    return '.zstd' if 压缩=='zstd' else ''#压缩后缀

def 日志后缀(压缩):#产物后缀
    """返回一种物理编码对应的产物后缀。"""
    return '.jsonl'+压缩后缀(压缩)#前缀.jsonl再加压缩后缀

def 代次日志文件名(版本,压缩):#代次日志文件名
    """返回一代不可变会话格式的规范文件名。"""
    return 会话格式日志文件名(版本)+压缩后缀(压缩)#格式名加压缩后缀

def 解析代次日志文件名(文件名,压缩):#解析代次日志文件名
    """按所选物理编码解析一代规范文件名。"""
    后缀=压缩后缀(压缩)#期望后缀
    if not 文件名.endswith(后缀):#后缀不符
        return None#非规范
    return 解析会话格式日志文件名(文件名[:len(文件名)-len(后缀)])#去掉后缀再解析

def 断言无已退役头字段(值):#断言无已退役头字段
    """拒绝永不出现在已发布会话头中的策略字段。"""
    if not isinstance(值,dict):#非对象
        return#直接返回
    if 'sandboxMode' in 值 or 'approvalPolicy' in 值:#含退役策略字段
        raise Error('session header uses retired policy baseline fields')#拒绝退役字段

class Error(Exception):#格式辅助错误
    """JSONL 格式辅助抛出的 Error 风格异常。"""

def 头转头行(头,继承事件数=None):#头转头行
    """从会话头构造头行对象。"""
    if 头.get('isSeeded') and 继承事件数 is None:#播种头缺继承计数
        raise Error('seeded session header requires an inherited event count')#播种头必须带继承计数
    切点=0 if 继承事件数 is None else 继承事件数#继承切点
    if not 头.get('isSeeded') and 切点!=0:#未播种头却非零切点
        raise Error('unseeded session header inherited event count must be 0')#未播种头切点必须为0
    return 会话格式目录.编码当代头({#经目录编码当代头
        **头,#展开会话头
        'delegationDepth':头['delegationDepth'] if 'delegationDepth' in 头 else 0,#委托深度缺省为0
    },切点)#切点传入

def 是否头行(值):#是否为头行
    """类型守卫：解析后的首行是形态完备的会话头。"""
    if not isinstance(值,dict):#须为普通对象
        return False#否
    for 键 in 头必填:#必填键齐全
        if 键 not in 值:#缺键
            return False#否
    for 键 in 值.keys():#无额外键
        if 键 not in 头键:#额外
            return False#否
    if 值.get('type')!='session':#类型
        return False#否
    if not isinstance(值.get('version'),(int,float)) or isinstance(值.get('version'),bool):#version
        return False#否
    if not isinstance(值.get('id'),str):#id
        return False#否
    创建=值.get('createdAt')#createdAt
    if not isinstance(创建,int) or isinstance(创建,bool) or 创建<0:#非法
        return False#否
    深度=值.get('delegationDepth')#delegationDepth
    if not isinstance(深度,int) or isinstance(深度,bool) or 深度<0:#非法
        return False#否
    cwd=值.get('cwd')#cwd
    if cwd is not None and (not isinstance(cwd,str) or not os.path.isabs(cwd)):#cwd非法
        return False#否
    父=值.get('parentSession')#parentSession
    if 父 is not None and not isinstance(父,str):#非法
        return False#否
    if not isinstance(值.get('isSeeded'),bool):#isSeeded
        return False#否
    来源=值.get('origin')#origin
    if 来源 is not None and 来源!='subagent':#非法
        return False#否
    预设=值.get('agentPreset')#agentPreset
    if 预设 is not None and not isinstance(预设,str):#非法
        return False#否
    return True#形态完备

def 编码路径分量(原始):#编码路径分量
    """把任意字符串编码为单个安全路径分量。"""
    if len(原始)==0:#空串
        raise Error('cannot encode an empty path segment')#拒绝空串
    if 原始=='.':#单独点
        return '~002E'#转义
    if 原始=='..':#双点
        return '~002E~002E'#转义
    输出=''#输出缓冲
    for 码元 in 原始:#逐码元
        if 码元!='~' and 安全码元.match(码元):#安全且非波浪号
            输出+=码元#原样追加
        else:#需转义
            输出+='~'+format(ord(码元),'04X')#波浪号加四位十六进制
    return 输出#返回编码结果

def 项目键(工作目录):#项目目录键
    """为项目路径构造可读目录键。"""
    if len(工作目录)==0:#空路径
        raise Error('cannot encode an empty project path')#拒绝空路径
    可读=''#可读缓冲
    分隔连续=False#是否处于分隔符连续段
    for 码元 in 工作目录:#逐码元
        if 码元 in ('/','\\',':'):#路径或盘符分隔符
            if not 分隔连续:#连续段只写一个-
                可读+='-'#写-
            分隔连续=True#标记连续段
        elif 码元!='~' and 安全码元.match(码元):#安全码元
            可读+=码元#原样追加
            分隔连续=False#结束连续段
        else:#需转义
            可读+='~'+format(ord(码元),'04X')#转义
            分隔连续=False#结束连续段
    段=可读.lstrip('-') or 'root'#去掉前导连字符，空则用root
    return '--'+段[:251]+'--'#两侧双连字符并截断

def 项目目录(根,工作目录=None):#项目目录路径
    """配置根下人类可导航的项目目录。"""
    if 工作目录 is None:#无cwd
        return os.path.join(根,'_no-cwd')#落到_no-cwd
    return os.path.join(根,项目键(工作目录))#有cwd则拼项目键

def 会话目录(根,工作目录,标识):#会话目录路径
    """单会话拥有的目录。"""
    return os.path.join(项目目录(根,工作目录),编码路径分量(str(标识)))#项目目录下拼编码后的id

def 代次日志路径(根,工作目录,标识,版本,压缩):#代次日志路径
    """构造一代不可变会话格式路径。"""
    return os.path.join(会话目录(根,工作目录,标识),代次日志文件名(版本,压缩))#会话目录下拼代次文件名

def 日志路径(根,头,压缩=None):#当前代次日志路径
    """构造会话当前代次的追加目标路径；亦接受仅含 id 的定位头。"""
    if 压缩 is None:#缺压缩
        压缩=默认压缩#默认
    工作目录=头.get('cwd') if isinstance(头,dict) else None#可选cwd
    标识=头['id'] if isinstance(头,dict) else 头#id
    return 代次日志路径(根,工作目录,标识,会话格式版本,压缩)#用本构建格式版本

def 事件行(事件):#单事件行
    """把一条当代事件序列化为一条无尾随换行的 JSONL 记录。"""
    return json.dumps(会话格式目录.编码当代事件(事件),ensure_ascii=False,separators=(',',':'),allow_nan=False)#经目录编码后序列化

def 事件行文本(事件列表):#事件行文本
    """把一批事件序列化为 JSONL 行（无尾随换行）。"""
    return '\n'.join(事件行(事件) for 事件 in 事件列表)#逐条编码后用换行连接

def 编码段(事件列表,打包块=False):#编码事件为 JSONL 文本
    """把事件列表编成 JSONL 文本；每行 UTF-8 语义由调用方再 encode。

    `打包块` 为历史遗留参数：追踪已删除 chunk-rows，当代写入始终逐事件原样编码，忽略该开关。
    """
    文本=事件行文本(事件列表)#编码（不打包）
    return 文本+('\n' if len(文本)>0 else '')#末行换行

def 拒绝外来格式版本(已解析):#拒绝外来格式版本
    """拒绝本构建不读取的格式版本。"""
    版本=已解析.get('version') if isinstance(已解析,dict) else None#版本
    标识=已解析.get('id') if isinstance(已解析,dict) else None#id
    if not isinstance(版本,(int,float)) or isinstance(版本,bool) or 版本==会话格式版本:#缺版本或本版本
        return#放过
    raise 会话格式不支持错误(#抛格式不支持
        会话格式版本拒绝文案(标识 if isinstance(标识,str) else str(标识),版本),#带拒绝文案
    )#抛错结束

def 头行转元数据(行):#头行转存储元数据
    """把一条当前物理头译成逻辑元数据。"""
    元={#逻辑会话头
        'version':会话格式版本,#本构建的格式版本
        'id':行['id'],#会话id
        'createdAt':行['createdAt'],#创建时刻
        'isSeeded':行['isSeeded'],#是否已播种
        'delegationDepth':行['delegationDepth'],#委托深度
    }#meta基
    if 'cwd' in 行:#有cwd
        元['cwd']=行['cwd']#带上
    if 'parentSession' in 行:#有父会话
        元['parentSession']=行['parentSession']#带上
    if 'origin' in 行:#有来源
        元['origin']=行['origin']#带上
    if 'agentPreset' in 行:#有预设
        元['agentPreset']=行['agentPreset']#带上
    return {'meta':元,'inheritedEventCount':0}#物理头不再携带切点，先置0

def 扫描日志(文本或字节,恢复='recoverable'):#扫描整份日志
    """把完整或撕裂的 JSONL 缓冲解析为保留的事件前缀。"""
    if isinstance(文本或字节,str):#文本
        缓冲=文本或字节.encode('utf-8')#转字节
    else:#字节
        缓冲=文本或字节#原样
    换行=缓冲.find(b'\n')#首行换行位置
    if 换行<0:#无换行
        raise Error('empty or header-less session log')#无头
    头记录=缓冲[:换行+1]#头记录
    其余=缓冲[换行+1:]#其余字节
    try:#解析头JSON
        已解析=json.loads(头记录[:-1].decode('utf-8'))#去掉换行再解析
    except json.JSONDecodeError:
        raise Error('corrupt session log: header line is not valid JSON')#头行非合法JSON
    if not isinstance(已解析,dict):#须为普通对象
        raise Error('corrupt session log: first line is not a JSON object')#首行非对象
    拒绝外来格式版本(已解析)#先拒绝外来版本
    断言无已退役头字段(已解析)#再拒绝退役字段
    if not 是否头行(已解析):#形态不完备
        raise Error('corrupt session log: first line is not a session header')#首行非会话头
    try:#创建恢复器
        恢复器=会话格式目录.创建恢复(已解析,{'recovery':恢复,'validation':'transformed'})#经目录创建
    except (会话格式不支持迁移错误,会话格式不支持错误,TypeError,KeyError,ValueError,AttributeError):
        raise Error('corrupt session log: first line is not a session header')#归类为非会话头
    元=头行转元数据(已解析)['meta']#逻辑头
    已提交=len(头记录)#已提交到头末
    行号=0#事件行号
    延迟错误=None#延迟错误
    偏移=0#其余内偏移
    while 偏移<=len(其余):#按行
        下一=其余.find(b'\n',偏移)#找换行
        if 下一<0:#无完整行
            break#撕裂尾忽略
        行=其余[偏移:下一]#本行
        偏移=下一+1#推进
        行号+=1#行号递增
        行末=len(头记录)+偏移#全局已提交末
        try:#解析行
            已解码=json.loads(行.decode('utf-8'))#解析
        except (json.JSONDecodeError,UnicodeDecodeError):
            问题=Error(f'corrupt session log: unparsable committed event at line {行号}')#构造错误
            if 恢复=='strict':#严格
                raise 问题#立即抛
            if 延迟错误 is None:#可恢复
                延迟错误=问题#记录
            continue#本行放弃
        try:#经恢复器解码
            if 延迟错误 is not None:#已有延迟错误
                if isinstance(已解码,dict) and 已解码.get('type')=='turn/end':#遇回合结束
                    raise 延迟错误#抛出
                continue#否则继续吞行
            恢复器.decodeRow(已解码)#解码行
        except 会话格式不支持迁移错误 as 错误:#不支持
            raise 会话格式不支持错误(str(错误))#映射
        except Error:#已是格式错误
            raise#原样
        except (TypeError,KeyError,ValueError,AttributeError) as 错误:
            问题=Error(f'corrupt session log: invalid committed event at line {行号}: {错误}')#构造
            if 恢复=='strict':#严格
                raise 问题#立即抛
            延迟错误=问题#可恢复记录
            if isinstance(已解码,dict) and 已解码.get('type')=='turn/end':#本行含回合结束
                raise 问题#立即抛
            continue#否则延迟
        已提交=行末#推进已提交字节
    产物=恢复器.finish()#完成恢复器
    事件列表=list(产物['events'])#事件前缀
    for 事件 in 事件列表:#建立不可变共享
        冻结树(事件)#深冻结单事件
    return {#扫描结果
        'meta':元,#会话头
        'inheritedEventCount':产物['inheritedEventCount'],#继承切点
        'events':事件列表,#事件前缀
        'eventState':'shared-frozen',#共享冻结状态
        'committedBytes':已提交,#已提交字节
    }#结果结束

#兼容旧公开名
编码段兼容=编码段#别名

__all__=[#公开面
    '默认压缩','日志后缀','代次日志文件名','解析代次日志文件名',
    '断言无已退役头字段','头转头行','编码路径分量','项目键',
    '项目目录','会话目录','代次日志路径','日志路径',
    '事件行','事件行文本','编码段','扫描日志',
]#公开面结束
