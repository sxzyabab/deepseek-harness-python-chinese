"""经子进程能力做 git 工作树快照、树差异与忽略检查。"""
import os,re,shutil,tempfile#路径、正则、拷贝与临时目录
from ...工具.超时 import 截止,取超时,已中止#超时与中止
from .行数统计 import 解析行数统计#numstat解析
from .路径 import 规范路径,是否位于内,转斜杠路径#路径工具
__all__=[#仅中文公开名
    'git运行器','定位版本库工作区','快照树','树团块','团块文本','差异树','链接路径集','忽略路径集',
]#公开面结束

#常量
终止宽限毫秒=2000#子进程终止宽限
标准误尾字节=16*1024#诊断用stderr尾
非仓库模式=re.compile(r'not a git repository',re.I|re.ASCII)#rev-parse非仓库

class 版本库错误(Exception):#本包git异常
    """git 命令失败或输出越界。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 是否不存在错误(错误):#是否ENOENT
    """文件系统错误是否表示路径不存在。"""
    if isinstance(错误,FileNotFoundError):#专用
        return True#缺失
    return isinstance(错误,OSError) and 错误.errno==2#ENOENT

class git运行器:#已解析可执行上的带限额运行器
    """对已解析 git 可执行文件跑命令：净化环境、超时、有界输出。"""
    def __init__(自身,子进程,可执行,限额):#记下能力与限额
        """绑定子进程能力、可执行路径与限额。"""
        自身.子进程=子进程#subprocess服务
        自身.可执行=可执行#git路径
        自身.限额=限额#timeoutMs/outputMaxBytes

    def 运行(自身,参数表,选项):#跑完一条git
        """同步跑 `git <参数表>` 至结束；超时、中止或无法派生时抛错。"""
        截止对象=截止(选项['signal'],自身.限额['timeoutMs'],'GIT_TIMEOUT')#融合超时
        try:#跑完再释放
            环境={'GIT_CONFIG_COUNT':'0','GIT_TERMINAL_PROMPT':'0','GIT_OPTIONAL_LOCKS':'0','LC_ALL':'C'}#净化基
            if 'env' in 选项 and 选项['env'] is not None:#额外环境
                环境.update(选项['env'])#叠上
            标准入='ignore'#默认忽略stdin
            if 'stdin' in 选项 and 选项['stdin'] is not None:#有stdin数据
                标准入={'data':选项['stdin']}#批数据
            最大字节=选项['maxBytes'] if 'maxBytes' in 选项 and 选项['maxBytes'] is not None else 自身.限额['outputMaxBytes']#输出帽
            句柄=自身.子进程.启动({#派生
                'argv':[自身.可执行]+list(参数表),#argv
                'cwd':选项['cwd'],#工作目录
                'stdio':{#三路
                    'stdin':标准入,#stdin
                    'stdout':{'maxBytes':最大字节},#有界stdout
                    'stderr':{'maxBytes':标准误尾字节},#有界stderr
                },#stdio结束
                'graceMs':终止宽限毫秒,#宽限
                'signal':截止对象.信号,#取消
                'env':环境,#环境
            })#启动结束
            try:#等结局
                结局=句柄.等待结局()#同步等待
            except Exception:#派生级失败
                if 已中止(截止对象.信号):#已中止
                    if 取超时(截止对象.信号,'GIT_TIMEOUT') is not None:#超时
                        raise 版本库错误('git '+' '.join(参数表)+' timed out after '+str(自身.限额['timeoutMs'])+'ms')#超时文案
                    raise 版本库错误('git '+' '.join(参数表)+' was aborted')#中止文案
                raise#其他
            if 已中止(截止对象.信号):#结束后再查
                if 取超时(截止对象.信号,'GIT_TIMEOUT') is not None:#超时
                    raise 版本库错误('git '+' '.join(参数表)+' timed out after '+str(自身.限额['timeoutMs'])+'ms')#超时
                raise 版本库错误('git '+' '.join(参数表)+' was aborted')#中止
            收集=句柄.collected if 句柄.collected is not None else {}#收集读取器
            if 'stdout' in 收集:#有stdout
                读出=收集['stdout'].自偏移读取(0)#从头读
                标准出文本=读出['text']#文本
                截断=读出['lossy']#是否丢头
            else:#无
                标准出文本=''#空
                截断=False#未截断
            if 'stderr' in 收集:#有stderr
                标准误文本=收集['stderr'].自偏移读取(0)['text']#文本
            else:#无
                标准误文本=''#空
            return {'exitCode':结局['exitCode'],'stdout':标准出文本,'stderr':标准误文本,'truncated':截断}#结果
        finally:#清定时器
            截止对象.释放()#释放

def 须成功(结果,说明):#非零即抛
    """非零退出则带 stderr 抛错；否则原样返回。"""
    if 结果['exitCode']!=0:#失败
        raise 版本库错误(说明+' failed: '+结果['stderr'].strip())#诊断
    return 结果#成功

def 定位版本库工作区(git,工作目录,草稿工厂,信号):#定位仓库并备草稿
    """定位包围工作目录的仓库并准备私有对象目录；不在仓库内返回 None。"""
    找到=git.运行(['rev-parse','--show-toplevel','--absolute-git-dir','--git-path','objects'],{'cwd':工作目录,'signal':信号})#定位
    if 找到['exitCode']==128 and 非仓库模式.search(找到['stderr']) is not None:#普通目录
        return None#无仓库
    行表=[os.path.normpath(os.path.join(工作目录,行) if not os.path.isabs(行) else 行) for 行 in 须成功(找到,'git rev-parse')['stdout'].rstrip('\n').split('\n')]#三行路径
    根=行表[0]#toplevel
    git目录=行表[1]#absolute-git-dir
    仓库对象=行表[2]#objects路径
    目录=规范路径(草稿工厂())#私有草稿根
    对象目录=os.path.join(目录,'objects')#私有objects
    os.makedirs(对象目录,exist_ok=True)#创建
    排除表=[转斜杠路径(os.path.relpath(目录,根))] if 是否位于内(根,目录) else []#工作树内则排除
    环境={'GIT_OBJECT_DIRECTORY':对象目录,'GIT_ALTERNATE_OBJECT_DIRECTORIES':仓库对象}#读写分流
    return {'root':根,'gitDir':git目录,'scratch':目录,'env':环境,'excludes':排除表}#工作区

def 快照树(git,工作区,信号):#写完整工作树为tree
    """经私有 index 把工作树（含未跟踪、不含忽略）写成 tree；仓库自身不变。"""
    草稿=tempfile.mkdtemp(prefix='index-',dir=工作区['scratch'])#临时index目录
    try:#写完清理
        索引=os.path.join(草稿,'index')#私有index
        try:#从仓库index种子
            shutil.copyfile(os.path.join(工作区['gitDir'],'index'),索引)#拷贝
        except OSError as 错误:#可能尚无index
            if not 是否不存在错误(错误):#非缺失
                raise 错误#上抛
        环境=dict(工作区['env'])#拷贝环境
        环境['GIT_INDEX_FILE']=索引#指向私有index
        路径规格=[] if len(工作区['excludes'])==0 else ['--','.']+[(':(exclude)'+路径) for 路径 in 工作区['excludes']]#排除规格
        已加=git.运行(['add','--all','--ignore-errors']+路径规格,{'cwd':工作区['root'],'env':环境,'signal':信号})#加入
        if 已加['exitCode']!=1:#非跳过不可读
            须成功(已加,'git add in '+工作区['root'])#须成功
        return 须成功(git.运行(['write-tree'],{'cwd':工作区['root'],'env':环境,'signal':信号}),'git write-tree')['stdout'].strip()#tree id
    finally:#删草稿index
        shutil.rmtree(草稿,ignore_errors=True)#强制删

def 树团块(git,工作区,树,路径,信号):#树上某路径的blob
    """快照树在路径上的 blob；无或非 blob 返回 None。"""
    结果=须成功(git.运行(['ls-tree','-z','-l',树,'--',路径],{#字面路径规格
        'cwd':工作区['root'],'env':{**工作区['env'],'GIT_LITERAL_PATHSPECS':'1'},'signal':信号,
    }),'git ls-tree')#须成功
    条目=结果['stdout'].split('\0')[0]#首条
    匹配=re.match(r'^\d+ (\S+) ([0-9a-f]+) +(\d+)\t',条目)#mode type oid size
    if 匹配 is None or 匹配.group(1)!='blob':#非blob
        return None#无
    return {'oid':匹配.group(2),'size':int(匹配.group(3))}#团块

def 团块文本(git,工作区,对象号,最大字节,信号):#读blob文本
    """读出已确认未超限的 blob 文本（UTF-8）。"""
    结果=须成功(git.运行(['cat-file','blob',对象号],{'cwd':工作区['root'],'env':工作区['env'],'maxBytes':最大字节,'signal':信号}),'git cat-file')#读
    if 结果['truncated']:#仍截断
        raise 版本库错误('blob '+对象号+' exceeds '+str(最大字节)+' bytes')#越界
    return 结果['stdout']#文本

def 差异树(git,工作区,之前,之后,信号):#两树numstat
    """两棵快照树之间的逐文件行数；同 id 返回空表。"""
    if 之前==之后:#无变化
        return []#空
    结果=须成功(git.运行(['diff-tree','-r','-M','-z','--numstat',之前,之后],{#带重命名
        'cwd':工作区['root'],'env':工作区['env'],'signal':信号,
    }),'git diff-tree')#须成功
    if 结果['truncated']:#输出帽不够
        raise 版本库错误('git diff-tree output exceeded the configured cap')#放弃
    return 解析行数统计(结果['stdout'])#条目表

def 链接路径集(git,工作区,信号):#gitlink路径
    """index 中记为 gitlink 的嵌套仓/submodule 路径集。"""
    结果=须成功(git.运行(['ls-files','-z','--stage'],{'cwd':工作区['root'],'env':工作区['env'],'signal':信号}),'git ls-files')#stage
    链接=set()#路径集
    for 条目 in 结果['stdout'].split('\0'):#逐条
        if 条目.startswith('160000 '):#gitlink模式
            链接.add(条目[条目.find('\t')+1:])#路径
    return 链接#集合

def 忽略路径集(git,工作区,路径表,信号):#被忽略的子集
    """路径表中被仓库忽略的成员；已跟踪文件不会报出。"""
    if len(路径表)==0:#空
        return set()#空集
    结果=git.运行(['check-ignore','-z','--stdin'],{#stdin喂路径
        'cwd':工作区['root'],'env':工作区['env'],'stdin':'\0'.join(路径表)+'\0','signal':信号,
    })#检查
    if 结果['exitCode']==1:#无一忽略
        return set()#空集
    return set(路径 for 路径 in 须成功(结果,'git check-ignore')['stdout'].split('\0') if 路径!='')#忽略集
