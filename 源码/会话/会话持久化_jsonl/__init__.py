"""JSONL 会话持久化：代次文件加活写句柄。"""
import hashlib,json,os,secrets,sys#摘要、JSON、路径、临时名、平台
from ...依赖.schemastery import 字典字段,字符串字段,布尔字段,数字字段
from ...内核.会话 import 会话格式版本#当代格式版本
from ..会话格式目录 import 会话格式目录,创建带子项的会话格式目录#格式目录
from .名录迁移 import 准备名录事实#名录事实
from ..会话持久化 import (
    会话持久化,默认预备会话缓存大小,默认写批最大延迟毫秒,
    持久化协调器,持久化错误,若已中止则抛出,
    会话持久化未找到错误,会话已存在错误,
    会话格式不支持错误,会话格式版本拒绝文案,会话持久化损坏错误,
)#基座
from ..会话持久化.存储契约 import 物化创建头,断言已存标识,断言版本,校验已存事件#存储契约
from ..会话持久化.修订 import 会话持久化修订#修订
from .格式 import (#格式工具
    代次日志文件名,解析代次日志文件名,代次日志路径,日志路径,
    会话目录,项目目录,扫描日志,头转头行,事件行文本,默认压缩,断言无已退役头字段,
)#格式
from .租约 import 租约文件名,会话写租约,会话已有写主错误#写租约
from .zstd编解码 import (#zstd
    压缩zstd帧,解压zstd帧,扫描zstd帧,解压zstd前缀,创建zstd帧解码器,
    Error as zstd帧错误,
)#zstd
from .代次 import (#代次
    物理身份,身份串,读稳定jsonl文件,准备jsonl迁移,默认代次格式适配器,
    代次不支持迁移错误,代次源变更错误,同步目录,
)#代次
from .迁移校验 import 进程内校验当代代#进程内校验
from .存储 import jsonl会话句柄,jsonl后端跟踪器#存储句柄
from .win32 import 发布新文件win32#Win32 发布

包名='@deepseek-ai/dsh-session-persistence-jsonl'
名称='session-persistence-jsonl'
依赖=['sessions']#依赖
配置=字典字段(字典结构={
    'root':字符串字段(),#根目录必填
    'packChunks':布尔字段(默认值=False),#历史遗留；当代写入不打包（追踪已删 chunk-rows）
    'compression':字符串字段(默认值='zstd'),#压缩
    'preparedSessionCacheSize':数字字段(默认值=默认预备会话缓存大小),#预备缓存
    'writeBatchMaxDelayMs':数字字段(默认值=默认写批最大延迟毫秒),#写批延迟
})
__all__=[
    '包名','名称','依赖','应用','默认','配置','jsonl会话持久化','租约文件名','会话写租约','会话已有写主错误',
]

def _断言zstd头帧(明文):#校验头帧
    """断言可独立解码的第一帧只含头记录。"""
    if len(明文)==0 or 明文.find(b'\n')!=len(明文)-1:#空或不是恰好一行
        raise 持久化错误('corrupt Zstandard session log: first frame is not exactly one header line')#损坏

class jsonl会话持久化(会话持久化):
    """每会话目录下不可变代文件；create/open 返回可入队活写的句柄。"""
    def __init__(自身,上下文,配置值):#构造
        """按配置登记 JSONL 后端、跟踪器与协调器。"""
        super().__init__(上下文)#基类
        if 'root' not in 配置值 or len(str(配置值['root']).strip())==0:#缺根
            raise 持久化错误('session-persistence-jsonl: root is required')#拒绝
        自身.根=os.path.abspath(str(配置值['root']))#绝对根
        自身.打包块=False#当代写入不打包；配置项仅兼容读取
        自身.压缩=配置值['compression'] if 'compression' in 配置值 else 默认压缩#压缩
        预备缓存=配置值['preparedSessionCacheSize'] if 'preparedSessionCacheSize' in 配置值 else 默认预备会话缓存大小#预备
        写批延迟=配置值['writeBatchMaxDelayMs'] if 'writeBatchMaxDelayMs' in 配置值 else 默认写批最大延迟毫秒#写批
        自身.跟踪器=jsonl后端跟踪器(名称)#活写跟踪器
        自身.代次格式=默认代次格式适配器()#代格式适配器
        自身.协调器=持久化协调器(上下文,自身.造后端(),{#协调器（遗留预备/加载）
            'preparedSessionCacheSize':预备缓存,#预备缓存
            'writeBatchMaxDelayMs':写批延迟,#写批延迟
        })#协调器
        #活写接到句柄：协调器优先查跟踪器写者，避免与写后双写

    @property
    def 支持原样子产物(自身):#是否支持原样子产物
        """JSONL 后端暴露原样子产物。"""
        return True#支持

    def 相反压缩(自身):#相反物理编码
        """返回与当前配置相反的压缩模式。"""
        return 'none' if 自身.压缩=='zstd' else 'zstd'#相反

    def 造后端(自身):#协调器后端适配
        """把代次感知文件 IO 原语交给协调器。"""
        持有=自身#外层
        class 后端:
            """协调器耐久原语（代次路径）。"""
            name=名称#诊断名
            def locate(自身,头):#定位
                """定位当代产物。"""
                选中=持有.查找日志(头['id'])
                if 选中 is None:#缺席
                    return None#无
                return {'kind':'jsonl','path':选中['sourcePath']}#位置
            def loadStored(自身,标识,信号=None):#加载
                """加载已存会话（含撕裂尾元数据）。"""
                return 持有.加载已存日志(标识,信号)#委托
            def readStoredRevision(自身,标识,信号=None):#修订
                """读已存修订指纹。"""
                选中=持有.查找日志(标识,信号)
                if 选中 is None:#无
                    return None#无
                return 会话持久化修订(身份串(物理身份(os.stat(选中['sourcePath']))))#修订
            def loadStoredFrom(自身,标识,起始序号,信号=None):#后缀读
                """从起始序号起读后缀。"""
                已加载=自身.loadStored(标识,信号)#全读
                if 已加载 is None:#缺席
                    return None#无
                return {#后缀
                    'meta':已加载['meta'],#头
                    'inheritedEventCount':已加载['inheritedEventCount'],#继承
                    'events':[事件 for 事件 in 已加载['events'] if 事件['seq']>=起始序号],#后缀
                    'eventState':已加载['eventState'],#状态
                }#返回
            def appendBatch(自身,标识或头,批次,已物化=True,信号=None):#追加
                """追加一批；经持久化批次（代次物化/追加）。"""
                if isinstance(标识或头,dict):#头
                    头=标识或头#头
                    标识=头['id']#id
                else:#id
                    标识=标识或头#id
                    头={'id':标识}#最小头
                状态=持有.协调器.状态表.get(标识)#协调器状态
                继承=0 if 状态 is None else 状态.get('inheritedEventCount',0)#继承
                if 状态 is not None and 'meta' in 状态:#有完整头
                    头=状态['meta']#用记账头
                持有.持久化批次(头,批次,已物化,继承)#写
                return None#无撕裂标记（撕裂在打开时记下）
            def commitRepair(自身,标识,修复,信号=None):#修复
                """截断撕裂尾。"""
                头=标识 if isinstance(标识,dict) else {'id':标识}#头
                偏移=修复 if isinstance(修复,(int,float)) else 修复.get('truncateTo',修复)#偏移
                持有.截断撕裂尾(头,int(偏移))#截断
            def list(自身,信号=None):#列表
                """列出可解析会话头。"""
                return [项['header'] for 项 in 持有.列出产物(信号)]#头列表
            def close(自身):#关闭
                """关闭。"""
                return#无状态
        return 后端()#实例

    # --- SessionPersistence 服务 API ---

    def 创建(自身,头,选项=None):#创建写句柄
        """创建新已存会话并取得写所有权；未物化直至首次追加/刷盘。"""
        信号=选项.get('signal') if 选项 else None#取消
        若已中止则抛出(信号)#取消
        快照=物化创建头(头)#物化头
        继承=选项.get('inheritedEventCount',0) if 选项 else 0#继承
        头转头行(快照,继承 if 快照.get('isSeeded') else None)#校验头行
        若已中止则抛出(信号)#再取消
        if 自身.跟踪器.有挂起(快照['id']) or 自身.查找日志(快照['id'],信号) is not None:#已存在
            raise 会话已存在错误(快照['id'])#拒绝
        若已中止则抛出(信号)#再取消
        自身.跟踪器.登记已创建(快照,继承)#登记挂起
        句柄=自身.跟踪器.收养(jsonl会话句柄(自身,快照['id'],快照,'write',{#收养写句柄
            'cursor':0,#游标
            'materialized':False,#未物化
            'inheritedEventCount':继承,#继承
        }))#句柄
        自身.协调器.登记活写句柄(句柄)#活写接到句柄
        return 句柄#返回

    def 打开(自身,标识,访问,选项=None):#打开句柄
        """打开已存会话；写打开发布历史迁移并取租约。"""
        信号=选项.get('signal') if 选项 else None#取消
        若已中止则抛出(信号)#取消
        挂起=自身.跟踪器.挂起项(标识)#挂起
        if 访问=='read':#只读
            if 挂起 is not None:#未物化挂起
                句柄=自身.跟踪器.收养(jsonl会话句柄(自身,标识,挂起['header'],'read',{#读挂起
                    'cursor':0,'materialized':False,'inheritedEventCount':挂起['inheritedEventCount'],
                }))#收养
                return 句柄#返回
            已存=自身.要求已存日志(标识,信号)#要求已存
            if 已存.get('status')=='prepared':#已准备历史
                状态={'cursor':0,'materialized':True,'inheritedEventCount':已存['inheritedEventCount'],'primed':已存}#预热
            else:#当代
                状态={'cursor':0,'materialized':True,'inheritedEventCount':已存['inheritedEventCount']}#无预热
            return 自身.跟踪器.收养(jsonl会话句柄(自身,标识,已存['meta'],'read',状态))#读句柄
        自身.跟踪器.声明写(标识)#认领写
        租约=None#租约
        try:#写打开
            选中=自身.查找日志(标识,信号)
            if 选中 is None:#未找到
                raise 会话持久化未找到错误(标识)#未找到
            租约=会话写租约.取得(os.path.dirname(选中['currentPath']),标识)#租约
            已准备=自身.要求已存日志(标识,信号)#已存
            若已中止则抛出(信号)#取消
            if 已准备.get('status')=='prepared':#需发布迁移
                已存=自身.发布已存迁移(标识,已准备)#发布
            else:#当代
                已存=已准备#直接用
            若已中止则抛出(信号)#再取消
            句柄=自身.跟踪器.收养(jsonl会话句柄(自身,标识,已存['meta'],'write',{#写句柄
                'cursor':len(已存['events']),#游标
                'materialized':True,#已物化
                'tornTruncateTo':已存.get('tornTruncateTo'),#撕裂截断
                'recoveredTail':已存.get('recoveredTail'),#恢复尾
                'inheritedEventCount':已存['inheritedEventCount'],#继承
                'primed':已存,#预热
            },租约))#带租约
            自身.协调器.登记活写句柄(句柄)#活写接到句柄
            return 句柄#返回
        except BaseException as 错误:
            释错=None#释租失败
            try:#释租
                if 租约 is not None:#有租约
                    租约.释放()#释放
            except BaseException as 原始:
                释错=原始#记下
            自身.跟踪器.释放声明(标识)#释放认领
            if 释错 is not None:#聚合
                raise ExceptionGroup(f'session "{标识}": write open failed and its lock release failed',[错误,释错])#聚合
            raise#抛出

    def 刷盘全部(自身):#服务刷盘
        """刷每个活跃写句柄的活缓冲与未物化头。"""
        return 自身.跟踪器.刷全部()#委托

    def 观察(自身,标识,选项=None):#轻量观察
        """不取所有权观察；不读事件日志。"""
        信号=选项.get('signal') if 选项 else None#信号
        若已中止则抛出(信号)#取消
        挂起=自身.跟踪器.挂起项(标识)#挂起
        if 挂起 is not None:#未物化
            return {'header':挂起['header'],'revision':挂起['revision']}#快照
        选中=自身.查找日志(标识,信号)
        if 选中 is None:#无
            return None#缺席
        头=自身.读代次头(选中,标识,信号)#头
        if 头 is None:#坏
            return None#缺席
        try:#stat
            身份=物理身份(os.stat(选中['sourcePath']))#身份
            若已中止则抛出(信号)#取消
            修订=会话持久化修订(身份串(身份))#修订
            if 选中['sourceVersion']<会话格式版本:#历史
                修订=会话持久化修订(身份串(身份)+':'+自身.历史语料修订(信号))#语料修订
            return {'header':头,'revision':修订,'sizeBytes':身份['size']}#快照
        except FileNotFoundError:#消失
            return None#缺席

    def 列出(自身,选项=None):#列举快照
        """列举已物化产物与本进程挂起会话。"""
        信号=选项.get('signal') if 选项 else None#信号
        快照列表=[]#结果
        已列=set()#已列 id
        挂起=list(自身.跟踪器.挂起条目())#挂起快照
        产物列表=自身.列出产物(信号)#产物
        语料修订=None#历史语料
        for 产物 in 产物列表:#是否需要语料修订
            if 产物.get('sourceVersion',会话格式版本)<会话格式版本:#历史
                语料修订=自身.历史语料修订(信号)#语料
                break#只需一次
        for 产物 in 产物列表:#产物
            若已中止则抛出(信号)#取消
            try:#stat
                身份=物理身份(os.stat(产物['path']))#身份
                已列.add(产物['header']['id'])#记下
                修订=会话持久化修订(身份串(身份))#修订
                if 产物.get('sourceVersion',会话格式版本)<会话格式版本 and 语料修订 is not None:#历史
                    修订=会话持久化修订(身份串(身份)+':'+语料修订)#语料修订
                快照列表.append({'header':产物['header'],'revision':修订,'sizeBytes':身份['size']})#追加
            except FileNotFoundError:#消失
                continue#跳过
        for 标识,条目 in 挂起:#挂起
            if 标识 not in 已列:#未列
                快照列表.append({'header':条目['header'],'revision':条目['revision']})#补上
        return 快照列表#返回

    def 列出快照(自身,信号=None):#列出快照别名
        """列出快照（兼容旧名）。"""
        return 自身.列出({'signal':信号} if 信号 is not None else None)#委托

    # --- JsonlHandleStorage 面 ---

    def 解析当代日志(自身,标识,信号=None):#解析当代路径
        """解析当代代产物路径；历史未发布时为 None。"""
        若已中止则抛出(信号)#取消
        选中=自身.查找日志(标识,信号)
        if 选中 is None:#无
            return None#无
        if 选中['sourceVersion']==会话格式版本:#已是当代
            return 选中['sourcePath']#路径
        if 选中['sourceVersion']<会话格式版本:#历史
            return None#未发布
        raise 会话格式不支持错误(#未来版本
            会话格式版本拒绝文案(标识,选中['sourceVersion'])+f' (raw log: {选中["sourcePath"]})',
            {'kind':'jsonl','path':选中['sourcePath']},
        )#错误

    def 读已存日志(自身,路径,期望标识,信号=None):#读已存日志
        """读取并校验 path 处已存日志。"""
        若已中止则抛出(信号)#取消
        with open(路径,'rb') as 文件:#读
            原始=文件.read()#字节
        解码=自身.解码日志字节(原始,信号)#解码
        断言已存标识(期望标识,解码['meta'])#身份
        断言版本(解码['meta'],{'kind':'jsonl','path':路径})#版本
        校验已存事件(解码['meta'],list(解码['events']),{'kind':'jsonl','path':路径})#事件契约
        return 解码#返回

    def 持久化批次(自身,头,事件列表,已物化,继承事件数):#持久化批次
        """耐久追加一批；首次写入时惰性物化。"""
        if 已物化:#已有文件
            自身.追加行(头,事件列表)#追加
        else:#尚未物化
            自身.物化(头,继承事件数,事件列表)#原子写出
            自身.跟踪器.已物化(头['id'])#清挂起

    def 持久化头(自身,头,继承事件数):#持久化仅头
        """为显式刷过的空会话物化仅头产物。"""
        自身.物化(头,继承事件数,[])#仅头
        自身.跟踪器.已物化(头['id'])#清挂起

    def 截断撕裂尾(自身,头,截到):#截断撕裂尾
        """在首次新追加前耐久截断撕裂物理尾巴。"""
        路径=日志路径(自身.根,头,自身.压缩)#路径
        with open(路径,'r+b') as 文件:#截断
            文件.truncate(截到)#截到
            文件.flush()#刷
            os.fsync(文件.fileno())#同步
        if hasattr(自身.上下文,'日志'):#有日志
            自身.上下文.日志.警告(f'{名称}: session "{头["id"]}" recovered from a torn tail; incomplete tail bytes were discarded')#警告

    def 有挂起会话(自身,标识):#是否挂起
        """本进程是否仍跟踪已创建但未物化会话。"""
        return 自身.跟踪器.有挂起(标识)#委托

    def 释放句柄(自身,句柄,已物化):#释放句柄
        """关闭时释放后端簿记并注销协调器活写。"""
        自身.协调器.注销活写句柄(句柄)#注销活写
        自身.跟踪器.释放(句柄,已物化)#跟踪器

    def 取得写租约(自身,头):#取得写租约
        """为正在物化的会话取得跨进程写锁。"""
        目录=会话目录(自身.根,头.get('cwd'),头['id'])#会话目录
        return 会话写租约.取得(目录,头['id'])#租约

    # --- 代次发现 / 读写 ---

    def 查找日志(自身,标识,信号=None):
        """在根下按会话目录选出权威不可变代。"""
        若已中止则抛出(信号)#取消
        if not os.path.isdir(自身.根):#无根
            return None#无
        for 项目名 in os.listdir(自身.根):#项目
            项目路径=os.path.join(自身.根,项目名)#路径
            if not os.path.isdir(项目路径):#非目录
                continue#跳过
            for 会话名 in os.listdir(项目路径):#会话
                会话路径=os.path.join(项目路径,会话名)#路径
                if not os.path.isdir(会话路径):#非目录
                    continue#跳过
                选中=自身.解析目录内代(会话路径,信号)#解析
                if 选中 is None:#无代
                    continue#跳过
                try:#读头 id
                    头=自身.读代次头行(选中['sourcePath'],信号)#头行
                except (持久化错误,OSError,UnicodeDecodeError,ValueError):
                    continue#跳过
                if 头 is not None and 头.get('id')==标识:#匹配
                    return 选中#返回
        return None#未找到

    def 解析目录内代(自身,目录,信号=None):#解析目录内代
        """在一个会话目录内选出数值最高的规范代。"""
        若已中止则抛出(信号)#取消
        try:#列目录
            名称列表=os.listdir(目录)#名
        except FileNotFoundError:#缺失
            return None#无
        代列表=[]#本编码代
        相反=[]#相反编码
        for 名 in 名称列表:#每项
            版本=解析代次日志文件名(名,自身.压缩)#本编码
            if 版本 is not None:
                代列表.append({'path':os.path.join(目录,名),'version':版本})#记下
                continue#下一项
            if 解析代次日志文件名(名,自身.相反压缩()) is not None:#相反
                相反.append(os.path.join(目录,名))#记下
        if len(相反)>0:#冲突
            raise 持久化错误(f'session directory mixes compression encodings: {相反[0]}')#拒绝
        if len(代列表)==0:#无代
            return None#无
        代列表.sort(key=lambda 项:项['version'],reverse=True)#最高版本
        最新=代列表[0]#最新
        return {#已解析
            'sourcePath':最新['path'],#源
            'sourceVersion':最新['version'],#版本
            'currentPath':os.path.join(目录,代次日志文件名(会话格式目录.当前版本,自身.压缩)),#当代
        }#返回

    def 读代次头行(自身,路径,信号=None):#读头行对象
        """读文件第一条完整头行并解析为对象。"""
        若已中止则抛出(信号)#取消
        import json#JSON
        if 自身.压缩=='zstd':#压缩
            文本=自身.读首帧zstd行(路径,信号)#头行
        else:#明文
            文本=自身.读明文首行(路径,信号)#头行
        if 文本 is None:#无
            return None#无
        return json.loads(文本)#解析

    def 读明文首行(自身,路径,信号=None):#读明文第一行
        """按块读第一条以换行终止的行。"""
        若已中止则抛出(信号)#取消
        with open(路径,'rb') as 文件:#读
            块列表=[]#块
            while True:#直到换行
                若已中止则抛出(信号)#取消
                块=文件.read(8192)#块
                if not 块:#EOF
                    return None#无完整行
                换行=块.find(b'\n')#换行
                if 换行>=0:#找到
                    块列表.append(块[:换行])#到换行
                    return b''.join(块列表).decode('utf-8')#文本
                块列表.append(块)#整块

    def 读首帧zstd行(自身,路径,信号=None):#读压缩头行
        """只读并校验可独立压缩的头帧。"""
        若已中止则抛出(信号)#取消
        with open(路径,'rb') as 文件:#读
            内容=b''#已读
            while True:#直到第一帧完整
                若已中止则抛出(信号)#取消
                块=文件.read(8192)#块
                if not 块:#EOF
                    return None#无
                内容+=块#累加
                帧列表=扫描zstd帧(内容,1).get('frames') or []#最多一帧
                if len(帧列表)==0:#不完整
                    continue#继续
                首=帧列表[0]#首帧
                try:#解压
                    明文=解压zstd帧(内容[首['start']:首['end']])#解压
                except zstd帧错误 as 错误:
                    raise 持久化错误('corrupt Zstandard session log: header frame failed validation') from 错误#损坏
                _断言zstd头帧(明文)#断言
                return 明文[:-1].decode('utf-8')#去换行

    def 解码日志字节(自身,原始,信号=None):#解码日志字节
        """解码明文或 zstd 日志，含撕裂尾恢复。"""
        if 自身.压缩=='none':#明文
            扫描=扫描日志(原始)#扫描
            撕裂=None if 扫描.get('committedBytes',len(原始))==len(原始) else 扫描.get('committedBytes')#撕裂点
            return {#结果
                'meta':扫描['meta'],#头
                'inheritedEventCount':扫描['inheritedEventCount'],#继承
                'events':扫描['events'],#事件
                'eventState':扫描['eventState'],#状态
                'tornTruncateTo':撕裂,#截断点
                'recoveredTail':[],#明文无单独恢复尾
                'status':'current',#当代
            }#返回
        return 自身.读zstd前缀(原始,信号)#zstd

    def 读zstd前缀(自身,缓冲,信号=None):#读压缩前缀
        """解码完整帧，并从撕裂末帧保留完整 JSONL 记录。"""
        若已中止则抛出(信号)#取消
        扫描=扫描zstd帧(缓冲)#扫描
        帧列表=扫描['frames']#帧
        撕裂起点=扫描.get('tornStart')#撕裂
        if len(帧列表)==0:#空
            raise 持久化错误('empty or header-less Zstandard session log')#损坏
        解码器=创建zstd帧解码器()#解码器
        try:#解码完整帧
            产出=list(解码器.解码(缓冲,帧列表))#全部
            if len(产出)==0:#无
                raise 持久化错误('empty or header-less Zstandard session log')#损坏
            _断言zstd头帧(产出[0])#头帧
            明文=b''.join(产出)#拼接
            扫描结果=扫描日志(明文)#扫描
            if 扫描结果.get('committedBytes',len(明文))!=len(明文):#完整帧内撕裂
                raise 持久化错误('corrupt Zstandard session log: complete frame contains a torn JSONL record')#损坏
            完整事件数=len(扫描结果['events'])#完整帧内事件数
            恢复尾=[]#待耐久重写的恢复尾
            截断点=None#截断
            if 撕裂起点 is not None:#有撕裂末帧
                截断点=撕裂起点#截到完整帧末
                try:#解压前缀
                    恢复=解压zstd前缀(缓冲[撕裂起点:])#前缀
                except zstd帧错误:
                    恢复=b''#空
                换行=恢复.rfind(b'\n')#最后换行
                if 换行>=0:#有完整行
                    合并=明文+恢复[:换行+1]#完整帧明文+恢复行
                    再扫=扫描日志(合并)#再扫
                    恢复尾=list(再扫['events'][完整事件数:])#新增完整事件
                    #打开写句柄的游标含恢复尾；首次追加前截断撕裂字节再重写恢复尾
                    扫描结果=再扫#逻辑前缀含恢复行
            return {#结果
                'meta':扫描结果['meta'],#头
                'inheritedEventCount':扫描结果['inheritedEventCount'],#继承
                'events':扫描结果['events'],#事件（含恢复完整行）
                'eventState':扫描结果['eventState'],#状态
                'tornTruncateTo':截断点,#截断点
                'recoveredTail':恢复尾,#待重写尾
                'status':'current',#当代
            }#返回
        finally:#清理
            解码器.关闭()#关闭

    def 加载已存日志(自身,标识,信号=None):#加载已存
        """查找并解码；历史代走准备迁移（不发布）。"""
        选中=自身.查找日志(标识,信号)
        if 选中 is None:#无
            return None#无
        if 选中['sourceVersion']<会话格式版本:#历史
            return 自身.准备已存迁移(标识,选中,信号)#准备
        if 选中['sourceVersion']>会话格式版本:#未来
            raise 会话格式不支持错误(#拒绝
                会话格式版本拒绝文案(标识,选中['sourceVersion'])+f' (raw log: {选中["sourcePath"]})',
                {'kind':'jsonl','path':选中['sourcePath']},
            )#错误
        稳定=读稳定jsonl文件(选中['sourcePath'],信号)#稳定读
        解码=自身.解码日志字节(稳定['bytes'],信号)#解码
        解码['revision']=会话持久化修订(身份串(稳定['identity']))#修订
        解码['status']='current'#当代
        return 解码#返回

    def 要求已存日志(自身,标识,信号=None):#要求已存
        """产物缺失时大声拒绝。"""
        已存=自身.加载已存日志(标识,信号)#加载
        if 已存 is None:#缺失
            raise 会话持久化未找到错误(标识)#未找到
        return 已存#返回

    def 准备已存迁移(自身,标识,选中,信号=None):#准备迁移
        """解码历史代，不发布后继。"""
        def 子列表():#父的直接子
            """列出 origin=subagent 且 parentSession=本 id 的产物。"""
            结果=[]#子
            for 项 in 自身.列出产物(信号):#产物
                头=项['header']#头
                if 头.get('origin')=='subagent' and 头.get('parentSession')==标识:#直接子
                    结果.append({'header':头,'path':项['path']})#记下
            return 结果#子
        源列表=子列表()#子源
        相关=准备名录事实(标识,源列表,自身.压缩,信号)#名录事实
        for 失败 in 相关['failures']:#子失败
            if hasattr(自身.上下文,'日志'):#有日志
                自身.上下文.日志.警告(f'{名称}: session "{标识}" catalog retained a child with unknown descriptor (raw log: {失败["path"]}): {失败["error"]}')#警告
        成员=sorted(源['path'] for 源 in 源列表)#成员路径
        def 校验相关源():#相关源再核
            """成员集合与物理修订必须仍与准备时一致。"""
            当前=sorted(源['path'] for 源 in 子列表())#当前成员
            前=set(成员)#准备时
            后=set(当前)#现在
            变更=None#漂移路径
            for 路径 in 当前:#新增
                if 路径 not in 前:#新增
                    变更=路径#记下
                    break#停
            if 变更 is None:#无新增
                for 路径 in 成员:#删除
                    if 路径 not in 后:#删除
                        变更=路径#记下
                        break#停
            if 变更 is not None:#漂移
                raise 代次源变更错误(os.path.basename(变更))#源已变
            相关['validate']()#物理修订
        带子项格式={#绑定子证据的格式适配
            **自身.代次格式,#默认编码
            'createRestore':lambda 头:创建带子项的会话格式目录(相关['facts']).创建恢复(头,{'recovery':'recoverable','validation':'transformed'}),#带子项恢复
        }#格式结束
        try:#准备
            已准备=准备jsonl迁移({#选项
                'sourcePath':选中['sourcePath'],#源
                'sourceVersion':选中['sourceVersion'],#版本
                'currentPath':选中['currentPath'],#当代
                'compression':自身.压缩,#压缩
                'format':带子项格式,#带子项
                'validateRelatedSources':校验相关源,#相关源
                'verifyCurrentFile':进程内校验当代代,#进程内校验
                'signal':信号,#取消
            })#准备
        except 代次不支持迁移错误 as 错误:#不支持
            raise 会话格式不支持错误(#映射
                f'{错误}; source v{错误.fromVersion} artifact remains unchanged (raw log: {os.path.basename(选中["sourcePath"])})',
                {'kind':'jsonl','path':选中['sourcePath']},
            ) from 错误#cause
        产物=已准备['artifact']#产物
        元={#逻辑头（当代）
            'version':产物['header']['version'],#版本
            'id':产物['header']['id'],#id
            'createdAt':产物['header']['createdAt'],#创建
            'isSeeded':产物['header']['isSeeded'],#播种
            'delegationDepth':产物['header'].get('delegationDepth',0),#深度
        }#基
        for 键 in ('cwd','parentSession','origin','agentPreset'):#可选
            if 键 in 产物['header']:#有
                元[键]=产物['header'][键]#带上
        断言已存标识(标识,元)#身份
        校验已存事件(元,list(产物['events']),{'kind':'jsonl','path':选中['sourcePath']})#事件契约
        return {#已准备日志
            'status':'prepared',#状态
            'meta':元,#头
            'events':list(产物['events']),#事件
            'eventState':'shared-frozen',#冻结（迁移产物）
            'inheritedEventCount':产物.get('inheritedEventCount',0),#继承
            'tornTruncateTo':None,#无撕裂
            'recoveredTail':[],#无恢复尾
            'revision':会话持久化修订(身份串(已准备['sourceIdentity'])),#源修订
            'validateRelatedSources':校验相关源,#相关源
            'publication':{'source':选中,'value':已准备},#发布载荷
        }#返回

    def 发布已存迁移(自身,标识,已存):#发布迁移
        """在授予写访问前发布已准备历史日志。"""
        迁移=已存['publication']#载荷
        try:#发布
            身份=迁移['value']['publish']()#幂等发布
        except 代次源变更错误:#源变更
            raise#原样
        已存['status']='current'#当代
        已存['revision']=会话持久化修订(身份串(身份))#当代修订
        return 已存#返回

    def 物化(自身,头,继承事件数,事件列表):#物化
        """原子发布头（及可选首批）到当代代文件。"""
        内容=自身.编码物化(头,继承事件数,事件列表)#编码
        目录=会话目录(自身.根,头.get('cwd'),头['id'])#会话目录
        项目=项目目录(自身.根,头.get('cwd'))#项目
        最终=日志路径(自身.根,头,自身.压缩)#最终路径
        if 自身.解析目录内代(目录) is not None:#已有代
            raise 持久化错误(f'refusing to materialize "{头["id"]}": a log already exists on disk (open it instead)')#拒绝
        if sys.platform=='win32':#Win32
            os.makedirs(自身.根,exist_ok=True)#根
            os.makedirs(项目,exist_ok=True)#项目
            os.makedirs(目录,exist_ok=True)#会话
            临时=自身.写已同步临时(最终,内容)#临时
            try:#发布
                发布新文件win32(临时,最终)#写穿
            except BaseException:
                try:#清理
                    os.remove(临时)#删
                except OSError:#忽略
                    pass#忽略
                raise#抛出
            return
        #POSIX：独占写临时、硬链接发布、fsync 目录
        os.makedirs(目录,mode=0o700,exist_ok=True)#建目录
        临时=自身.写已同步临时(最终,内容)#临时
        try:#链接
            os.link(临时,最终)#硬链接发布
        except BaseException:
            try:#清理
                os.remove(临时)#删
            except OSError:#忽略
                pass#忽略
            raise#抛出
        同步目录(目录)#目录 fsync
        try:#清临时链接
            os.remove(临时)#删
        except OSError:#忽略
            pass#已发布

    def 写已同步临时(自身,最终路径,内容):#写已同步临时
        """写出已 fsync 临时文件。"""
        if isinstance(内容,str):#文本
            内容=内容.encode('utf-8')#转字节
        临时=f'{最终路径}.{secrets.token_hex(6)}.tmp'#临时名
        描述符=os.open(临时,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#独占
        try:#写
            os.write(描述符,内容)#写
            os.fsync(描述符)#同步
        finally:#关闭
            os.close(描述符)#关闭
        return 临时#路径

    def 编码物化(自身,元,继承事件数,事件列表):#编码物化内容
        """编码头与首批，不合并它们的帧边界。"""
        import json#JSON
        头值=头转头行(元,继承事件数 if 元.get('isSeeded') else None)#头行对象
        头行=json.dumps(头值,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n'#头行
        if len(事件列表)==0:#无事件
            return 压缩zstd帧(头行) if 自身.压缩=='zstd' else 头行.encode('utf-8')#仅头
        体=事件行文本(事件列表)+'\n'#事件行
        if 自身.压缩=='none':#明文
            return (头行+体).encode('utf-8')#拼接
        return 压缩zstd帧(头行)+压缩zstd帧(体)#两帧

    def 追加行(自身,元,事件列表):#追加事件行
        """追加并 fsync；失败时回滚部分写入。"""
        体=事件行文本(事件列表)+'\n'#事件行
        内容=压缩zstd帧(体) if 自身.压缩=='zstd' else 体.encode('utf-8')#编码
        路径=日志路径(自身.根,元,自身.压缩)#路径
        with open(路径,'r+b') as 文件:#读写打开以便失败回滚
            之前=os.fstat(文件.fileno()).st_size#追加前大小
            文件.seek(0,os.SEEK_END)#定位末尾
            try:#写
                文件.write(内容)#写
                文件.flush()#刷
                os.fsync(文件.fileno())#同步
            except BaseException as 错误:
                try:#回滚
                    文件.truncate(之前)#截回
                    文件.flush()#刷
                    os.fsync(文件.fileno())#同步
                except BaseException as 回滚:#回滚失败
                    raise ExceptionGroup(f'failed to roll back append to "{路径}"',[错误,回滚])#聚合
                raise#抛原错

    def 列出代次(自身,信号=None):#列出物理代
        """枚举选出的物理代，不解读头或体。"""
        源列表=[]#代
        if not os.path.isdir(自身.根):#无根
            return 源列表#空
        for 项目名 in os.listdir(自身.根):#项目
            项目路径=os.path.join(自身.根,项目名)#路径
            if not os.path.isdir(项目路径):#非目录
                continue#跳过
            for 会话名 in os.listdir(项目路径):#会话
                会话路径=os.path.join(项目路径,会话名)#路径
                if not os.path.isdir(会话路径):#非目录
                    continue#跳过
                选中=自身.解析目录内代(会话路径,信号)#解析
                if 选中 is not None:#有代
                    源列表.append(选中)#记下
        return 源列表#返回

    def 历史语料修订(自身,信号=None):#历史语料修订
        """历史逻辑事件依赖整份语料，含头不可读成员。"""
        路径列表=sorted(源['sourcePath'] for 源 in 自身.列出代次(信号))#路径
        摘要=hashlib.sha256()#摘要
        for 路径 in 路径列表:#逐路径
            若已中止则抛出(信号)#取消
            try:#stat
                修订=身份串(物理身份(os.stat(路径)))#修订
            except FileNotFoundError:#缺失
                修订='missing'#缺失
            摘要.update(json.dumps([路径,修订],ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8'))#喂入
        若已中止则抛出(信号)#取消
        return 摘要.hexdigest()#十六进制

    def 读代次头(自身,选中,期望标识=None,信号=None):#读代次头
        """读并翻译一代头，不看事件行。"""
        try:#读首行
            if 自身.压缩=='zstd':#压缩
                文本=自身.读首帧zstd行(选中['sourcePath'],信号)#头行
            else:#明文
                文本=自身.读明文首行(选中['sourcePath'],信号)#头行
        except FileNotFoundError:
            return None#缺席
        若已中止则抛出(信号)#取消
        if 文本 is None:#无
            return None#无
        try:#解析
            值=json.loads(文本)#对象
        except (ValueError,TypeError):
            return None#畸形
        断言无已退役头字段(值)#退役字段
        结果=会话格式目录.读头(值)#分类
        if 'storedVersion' in 结果 and 结果['storedVersion'] is not None and 结果['storedVersion']!=选中['sourceVersion']:
            raise 持久化错误('session generation filename identifies v'+str(选中['sourceVersion'])+', but its header identifies v'+str(结果['storedVersion']))#版本不一致
        if 结果['status']=='unsupported':#不支持
            物理标识=''#id
            if isinstance(值,dict) and 'id' in 值:
                物理标识=str(值['id'])#物理 id
            原因=结果['reason']#原因
            if 结果.get('storedVersion') is not None and 结果['storedVersion']>会话格式版本:
                原因=会话格式版本拒绝文案(物理标识,结果['storedVersion'])#未来版本
            raise 会话格式不支持错误(原因)#不支持
        if 结果['status']=='malformed':#畸形
            return None#无
        头=自身.当代头(结果['header'])#当代头
        if 期望标识 is not None and 头['id']!=期望标识:
            raise 持久化错误('stored session identity mismatch')#身份不符
        return 头#头

    def 当代头(自身,头):#当代头
        """把目录字符串身份收成当代会话头。"""
        if 头['version']!=会话格式版本:#非当代
            raise 持久化错误('format catalog returned non-current logical header v'+str(头['version']))#拒绝
        结果={'version':会话格式版本,'id':头['id'],'createdAt':头['createdAt'],'isSeeded':头['isSeeded'],'delegationDepth':头['delegationDepth']}#基
        if 'cwd' in 头:#cwd
            结果['cwd']=头['cwd']#cwd
        if 'parentSession' in 头:#父
            结果['parentSession']=头['parentSession']#父
        if 'origin' in 头:#来源
            结果['origin']=头['origin']#来源
        if 'agentPreset' in 头:#预设
            结果['agentPreset']=头['agentPreset']#预设
        return 结果#头

    def 列出产物(自身,信号=None):#列出产物
        """扫描根下全部规范代产物。"""
        若已中止则抛出(信号)#取消
        结果=[]#产物
        已见=set()#已见 id
        for 选中 in 自身.列出代次(信号):#代
            若已中止则抛出(信号)#取消
            try:#读头
                头=自身.读代次头(选中,None,信号)#头
            except (会话格式不支持错误,会话持久化损坏错误):
                continue#跳过
            if 头 is None:#无
                continue#跳过
            if 头['id'] in 已见:#重复
                raise 持久化错误('duplicate JSONL session id "'+str(头['id'])+'" appears in multiple project directories')#拒绝
            已见.add(头['id'])#记下
            结果.append({'header':头,'path':选中['sourcePath'],'sourceVersion':选中['sourceVersion']})#产物
        return 结果#返回

    # --- 遗留转发 ---

    def 定位(自身,头):#转发定位
        """转发定位。"""
        return 自身.协调器.后端.locate(头)#转发

    def 追加(自身,标识,事件列表):#转发追加
        """转发追加。"""
        return 自身.协调器.追加(标识,事件列表)#转发

    def 预备(自身,标识,信号=None):#降级预备
        """经协调器预备。"""
        return 自身.协调器.预备(标识,信号)#转发

    def 加载(自身,标识):#转发加载
        """转发加载。"""
        return 自身.协调器.加载(标识)#转发

    def 检查(自身,标识,信号=None):#转发检查
        """转发检查。"""
        return 自身.协调器.检查(标识,信号)#转发

    def 从序号读(自身,标识,起始序号,信号=None):#转发后缀读
        """转发后缀读。"""
        return 自身.协调器.从序号读(标识,起始序号,信号)#转发

def 应用(上下文,配置值):#加载
    """加载 JSONL 会话持久化。"""
    jsonl会话持久化(上下文,配置值)#注册

默认=jsonl会话持久化
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
jsonl会话持久化.inject=依赖#框架槽
jsonl会话持久化.name=名称#框架槽
