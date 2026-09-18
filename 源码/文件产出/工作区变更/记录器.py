"""每会话轮次记录器：快照、文件工具捕获、轮末差异，及释放前保留的记录。"""
import os,shutil,tempfile,threading#路径、删树、临时目录与串行锁
from ...工具.超时 import 中止控制器,已中止,合成信号#中止原语
from .捕获 import 捕获文件,变更路径,相同捕获#整文件捕获
from .对比 import 对比文本#逐行对比
from .版本库 import (
    团块文本,#读blob
    差异树,#两树numstat
    链接路径集,#gitlink
    忽略路径集,#check-ignore
    定位版本库工作区,#定位仓库
    快照树,#写tree
    树团块,#ls-tree
)#版本库操作
from .路径 import (
    规范路径,#canonical
    展示路径自,#display
    持久路径自,#path
    是否位于内,#inside
    是否临时路径,#temp
    临时根列表,#temp roots
    转斜杠路径,#posix
)#路径工具
__all__=['轮次记录器']#仅中文公开名

#常量
超限哨兵=object()#快照侧超限标记

class 记录器错误(Exception):#本模块异常
    """轮次记录失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 新鲜状态(轮次):#新一轮累积状态
    """构造一轮的空累积状态。"""
    return {'turn':轮次,'baseline':None,'captures':{},'lastToolResultSeq':-1,'attemptedAfterSeq':-1,'recordedAfterSeq':-1}#空状态

def 是否二进制捕获(捕获):#捕获侧是否二进制
    """捕获侧是否持有二进制内容。"""
    return 捕获['kind']=='file' and 捕获['binary']#文件且含NUL

def 变更文件(路径集,仓库根,绝对路径,计数):#构造摘要文件项
    """由路径集与行数构造一条工作区变更文件 dict。"""
    文件={'path':持久路径自(绝对路径,路径集['cwd']),'display':展示路径自(绝对路径,路径集['cwd'],仓库根,路径集['home']),'added':计数['added'],'deleted':计数['deleted']}#必填
    if 计数['binary']:#二进制
        文件['binary']=True#标记
    if 'oversized' in 计数 and 计数['oversized'] is True:#超限
        文件['oversized']=True#标记
    return 文件#条目

def 展示键(项):#排序键
    """已列项按 display 排序的键。"""
    return 项['file']['display']#展示路径

class 轮次记录器:#单会话串行记录
    """串行化一轮的快照、捕获、记录与按需对比；临时目录随释放删除。"""
    def __init__(自身,会话,工作目录,环境):#绑会话与环境
        """保存会话、工作目录与共享环境。"""
        自身.会话=会话#Session
        自身.工作目录=工作目录#cwd
        自身.环境=环境#RecorderEnvironment dict
        自身.链锁=threading.Lock()#串行锁
        自身.状态=新鲜状态(0)#占位状态
        自身.路径集=None#首次轮次解析
        自身.仓库=None#已定位仓库
        自身.草稿=None#临时目录路径
        自身.记录表={}#seq -> 记录
        自身.寿命=中止控制器()#插件/会话寿命

    def 开始(自身,轮次):#打开一轮并拍基线
        """打开一轮并同步拍基线快照。"""
        状态=新鲜状态(轮次)#本轮状态
        自身.状态=状态#切换
        def 任务(信号):#基线任务
            """拍基线。"""
            自身.拍基线(状态,信号)#执行
        自身.入队(任务)#串行拍基线

    def 拍基线(自身,状态,信号):#基线快照体
        """解析路径、定位仓库并写起始 tree。"""
        try:#失败则标记failed
            if 自身.路径集 is None:#首次
                自身.路径集={'cwd':os.path.realpath(自身.工作目录),'home':规范路径(os.path.expanduser('~')),'temporaryRoots':临时根列表()}#规范路径集
            仓库=自身.定位(自身.路径集['cwd'],信号)#定位
            if 仓库 is None:#无仓库或无git
                return#仅靠捕获
            树=快照树(仓库['git'],仓库['workspace'],信号)#起始tree
            状态['baseline']={'git':仓库['git'],'workspace':仓库['workspace'],'tree':树}#基线
        except Exception as 错误:#快照失败
            状态['baseline']='failed'#不得当无仓库
            raise 错误#交入队警告

    def 捕获(自身,名称,参数):#工具执行前捕获
        """在文件工具变更前捕获路径；每轮每路径只捕第一次。"""
        路径=变更路径(名称,参数)#模型侧路径
        if 路径 is None:#非变更工具
            return#空操作
        状态=自身.状态#当前轮
        def 任务(信号):#捕获体
            """解析绝对路径并写入首次捕获。"""
            路径集=自身.路径集#须已由开始解析
            if 路径集 is None:#尚未开始
                return#空操作
            绝对=规范路径(os.path.abspath(os.path.join(路径集['cwd'],路径)))#规范绝对
            if 绝对 in 状态['captures']:#已捕
                return#跳过
            捕获=捕获文件(绝对,os.path.join(自身.草稿目录(),'captures'),自身.环境['maxFileBytes'])#读入
            if 捕获 is not None:#可读或缺失
                状态['captures'][绝对]=捕获#记下
        自身.入队(任务)#串行

    def 观察(自身,事件):#记下tool/result
        """记住本轮 tool/result 的序号。"""
        状态=自身.状态#当前
        if 事件['data']['turn']==状态['turn']:#同轮
            状态['lastToolResultSeq']=事件['seq']#更新

    def 停止中(自身,轮次):#轮内记录
        """在 turn 结束前提交记录。"""
        状态=自身.状态#当前
        if 轮次!=状态['turn']:#轮次不符
            return#空操作
        def 任务(信号):#记录体
            """写本轮记录。"""
            自身.记录(状态,信号)#执行
        自身.入队(任务)#串行记录

    def 结束(自身,轮次):#turn/end后再记
        """若最后工具结果之后尚未尝试过记录，则再记一次。"""
        状态=自身.状态#当前
        if 轮次!=状态['turn'] or 状态['attemptedAfterSeq']>=状态['lastToolResultSeq']:#无需
            return#空操作
        def 任务(信号):#记录体
            """再记本轮。"""
            自身.记录(状态,信号)#执行
        自身.入队(任务)#再记

    def 已结算(自身):#等到队列空
        """同步入队下空操作即表示此前工作已完成。"""
        def 空任务(信号):#排空
            """空操作。"""
            return None#无事
        自身.入队(空任务)#排空点

    def 摘要(自身,序号):#按事件序号取摘要
        """返回该 workspace/changes 序号宣告的摘要，未知则 None。"""
        记录=自身.记录表[序号] if 序号 in 自身.记录表 else None#查找
        return None if 记录 is None else 记录['summary']#摘要

    def 差异(自身,序号,下标,信号):#按需对比一文件
        """对比摘要中下标文件两侧；未知序号/下标或已释放返回 None。"""
        记录=自身.记录表[序号] if 序号 in 自身.记录表 else None#记录
        if 记录 is None:#无
            return None#未知
        文件表=记录['summary']['files']#所列
        来源表=记录['sources']#对齐来源
        if 下标<0 or 下标>=len(文件表) or 下标>=len(来源表):#越界
            return None#无
        文件=文件表[下标]#条目
        来源=来源表[下标]#来源
        路径=文件['path']#path
        展示=文件['display']#display
        if 'refusal' in 来源:#拒绝对比
            return {'kind':来源['refusal'],'path':路径,'display':展示}#binary/oversized
        合成=自身.寿命.信号 if 信号 is None else 合成信号(信号,自身.寿命.信号)#寿命与调用方
        try:#读两侧
            之前=自身.读侧(来源['before'],合成)#起始侧
            之后=自身.读侧(来源['after'],合成)#结束侧
            if 之前 is 超限哨兵 or 之后 is 超限哨兵:#快照超限
                return {'kind':'oversized','path':路径,'display':展示}#超限
            对比=对比文本(之前,之后,自身.环境['diffTimeoutMs'])#逐行
            return {'kind':'text','path':路径,'display':展示,'before':之前 is not None,'after':之后 is not None,'hunks':对比['hunks'],'coarse':对比['coarse']}#文本差
        except Exception as 错误:#读失败
            if 已中止(自身.寿命.信号):#已释放
                return None#会话没了
            raise 错误#上抛

    def 释放(自身):#中止并删临时目录
        """中止排队、清空记录并删除临时目录。"""
        自身.寿命.中止()#中止
        自身.记录表.clear()#忘掉摘要
        with 自身.链锁:#等串行结束
            pass#锁空即闲
        if 自身.草稿 is not None:#有临时目录
            shutil.rmtree(自身.草稿,ignore_errors=True)#强制删

    def 入队(自身,任务):#串行执行
        """在寿命未中止时串行跑任务；失败则警告。"""
        with 自身.链锁:#互斥
            if 已中止(自身.寿命.信号):#已释放
                return#空操作
            try:#跑任务
                任务(自身.寿命.信号)#同步
            except Exception as 错误:#失败
                自身.未释放则警告(错误)#记警告

    def 未释放则警告(自身,错误):#释放后静默
        """释放后的失败视为取消，保持静默。"""
        if not 已中止(自身.寿命.信号):#仍活
            自身.环境['warn']('workspace-changes: '+str(错误))#警告

    def 草稿目录(自身):#会话临时目录
        """惰性创建本会话临时目录。"""
        if 自身.草稿 is None:#首次
            自身.草稿=tempfile.mkdtemp(prefix='dsh-workspace-changes-',dir=自身.环境['tempRoot'])#创建
        return 自身.草稿#路径

    def 定位(自身,工作目录,信号):#定位仓库一次
        """定位包围工作目录的仓库；无则返回 None 并允许下轮重试。"""
        if 自身.仓库 is not None:#已找到
            return 自身.仓库#复用
        git=自身.环境['git']#运行器或None；由插件同步解析后传入
        if git is None:#无git
            return None#无
        工作区=定位版本库工作区(git,工作目录,自身.草稿目录,信号)#定位
        if 工作区 is None:#不在仓内
            return None#无
        自身.仓库={'git':git,'workspace':工作区}#钉住
        return 自身.仓库#仓库

    def 读侧(自身,来源,信号):#读一侧文本
        """读一侧文本；缺失为 None；快照超限为超限哨兵。"""
        种类=来源['kind']#来源种类
        if 种类=='absent':#缺失
            return None#无文件
        if 种类=='file':#副本
            with open(来源['file'],'r',encoding='utf-8') as 读入:#读文本
                return 读入.read()#全文
        if 种类=='snapshot':#快照树
            仓库=来源['repository']#git+workspace
            团块=树团块(仓库['git'],仓库['workspace'],来源['tree'],来源['path'],信号)#定位blob
            if 团块 is None:#无
                return None#缺失
            if 团块['size']>自身.环境['maxFileBytes']:#超限
                return 超限哨兵#哨兵
            return 团块文本(仓库['git'],仓库['workspace'],团块['oid'],自身.环境['maxFileBytes'],信号)#文本
        raise 记录器错误('unknown content source kind')#契约外

    def 记录(自身,状态,信号):#汇总并追加事件
        """汇总本轮变更、追加 workspace/changes 并保存记录。"""
        路径集=自身.路径集#须已有
        基线=状态['baseline']#基线
        if 路径集 is None or 基线=='failed' or 状态['lastToolResultSeq']<0:#不可记
            return#放弃
        状态['attemptedAfterSeq']=状态['lastToolResultSeq']#记下尝试点
        根=基线['workspace']['root'] if 基线 is not None else 路径集['cwd']#仓库根或工作目录
        已列={}#绝对路径 -> 已列项
        快照=None#可选snapshot字段
        if 基线 is not None:#有快照
            之后树=快照树(基线['git'],基线['workspace'],信号)#结束tree
            快照={'before':基线['tree'],'after':之后树}#两端
            仓库={'git':基线['git'],'workspace':基线['workspace']}#仓库句柄
            for 条目 in 差异树(基线['git'],基线['workspace'],基线['tree'],之后树,信号):#逐文件
                绝对=os.path.abspath(os.path.join(根,条目['path']))#绝对
                if 条目['binary']:#二进制
                    来源={'refusal':'binary'}#拒绝
                else:#文本两侧来自快照
                    旧路径=条目['oldPath'] if 'oldPath' in 条目 else 条目['path']#重命名前
                    来源={#两侧
                        'before':{'kind':'snapshot','repository':仓库,'tree':基线['tree'],'path':旧路径},#起始
                        'after':{'kind':'snapshot','repository':仓库,'tree':之后树,'path':条目['path']},#结束
                    }#来源结束
                已列[绝对]={'file':变更文件(路径集,根,绝对,条目),'sources':来源}#列入
        已捕=[绝对 for 绝对 in 状态['captures'] if 绝对 not in 已列]#快照未覆盖
        仓内=[绝对 for 绝对 in 已捕 if 是否位于内(根,绝对)]#工作树内
        if 基线 is not None and len(仓内)>0:#有gitlink要滤
            链接集=链接路径集(基线['git'],基线['workspace'],信号)#gitlink
            过滤后=[]#过滤结果
            for 绝对 in 仓内:#逐路径
                落在链接=False#是否gitlink内
                for 链接 in 链接集:#逐链接
                    if 是否位于内(os.path.abspath(os.path.join(根,链接)),绝对):#在链接下
                        落在链接=True#命中
                        break#停
                if not 落在链接:#非嵌套仓
                    过滤后.append(绝对)#保留
            仓内=过滤后#替换
        if 基线 is None:#无快照则仓内全算未覆盖
            未覆盖仓内=set(转斜杠路径(os.path.relpath(绝对,根)) for 绝对 in 仓内)#全收
        else:#有快照则只有忽略的算未覆盖
            未覆盖仓内=忽略路径集(基线['git'],基线['workspace'],[转斜杠路径(os.path.relpath(绝对,根)) for 绝对 in 仓内],信号)#忽略集
        for 绝对 in 已捕:#逐捕获路径
            if 是否位于内(根,绝对):#仓内
                未覆盖=转斜杠路径(os.path.relpath(绝对,根)) in 未覆盖仓内#是否忽略
            else:#仓外
                未覆盖=not 是否临时路径(绝对,路径集['temporaryRoots'])#非临时才算
            if not 未覆盖:#快照已覆盖或临时
                continue#跳过
            之前=状态['captures'][绝对]#起始捕获
            之后=捕获文件(绝对,os.path.join(自身.草稿目录(),'captures'),自身.环境['maxFileBytes'])#结束捕获
            if 之后 is None or 相同捕获(之前,之后):#无变化或不可比
                continue#跳过
            已列[绝对]=自身.已对比项(路径集,根,绝对,之前,之后)#列入
        排序表=sorted(已列.values(),key=展示键)#display序
        if len(排序表)==0 and 状态['recordedAfterSeq']<0:#从未记过且空
            return#不发空事件
        事件=自身.会话.追加('workspace/changes',{'turn':状态['turn']})#宣告
        保留=排序表[0:自身.环境['maxFiles']]#截断列表
        摘要={'turn':状态['turn'],'cwd':自身.工作目录,'files':[项['file'] for 项 in 保留],'total':len(排序表),'added':sum(项['file']['added'] for 项 in 排序表),'deleted':sum(项['file']['deleted'] for 项 in 排序表)}#摘要
        if 快照 is not None:#有快照id
            摘要['snapshot']=快照#带上
        自身.记录表[事件['seq']]={'summary':摘要,'sources':[项['sources'] for 项 in 保留]}#按序号存
        状态['recordedAfterSeq']=事件['seq']#记下

    def 已对比项(自身,路径集,仓库根,绝对路径,之前,之后):#捕获对列入
        """由捕获对生成列表项：超限/二进制拒绝对比，否则带行数。"""
        def 列出(计数,来源):#组装
            """组装已列项。"""
            return {'file':变更文件(路径集,仓库根,绝对路径,计数),'sources':来源}#项
        if 之前['kind']=='oversized' or 之后['kind']=='oversized':#超限
            return 列出({'added':0,'deleted':0,'binary':False,'oversized':True},{'refusal':'oversized'})#拒绝
        if 是否二进制捕获(之前) or 是否二进制捕获(之后):#二进制
            return 列出({'added':0,'deleted':0,'binary':True},{'refusal':'binary'})#拒绝
        def 侧文本(侧):#读捕获文本
            """捕获侧转文本或 None。"""
            if 侧['kind']!='file':#缺失
                return None#无
            with open(侧['file'],'r',encoding='utf-8') as 读入:#读
                return 读入.read()#全文
        对比=对比文本(侧文本(之前),侧文本(之后),自身.环境['diffTimeoutMs'])#行数
        return 列出({'added':对比['added'],'deleted':对比['deleted'],'binary':False},{'before':之前,'after':之后})#文本对
