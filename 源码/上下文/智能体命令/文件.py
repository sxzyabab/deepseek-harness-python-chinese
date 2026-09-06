"""指令文件发现，以及带上限、可中止的提供方读取。"""
import errno,os,stat#路径、错误码与文件类型
from ...工具.工作区路径 import 主目录展示#导入家目录展示路径
from .配置 import 解析配置,解析发现配置,智能体命令错误,若已中止则抛出#导入配置解析与中止
from .摘要 import 去空白指令摘要#导入去空白摘要
from ...文件系统.文件系统 import 文件系统错误#提供方错误
from .渲染 import (
    解码作用域键,#解码候选作用域键
    渲染工作区指令集,#按预算渲染指令集
    用户全局目录,#用户全局目录占位
    用户全局文件,#用户全局文件名
)#从渲染导入结束

def 信号选项(信号=None):#把可选信号收成提供方选项
    """无信号则不传选项对象。"""
    return None if 信号 is None else {'signal':信号}#有则带上

def 是否缺失路径错误(错误):#判断是否为路径缺失类错误
    """ENOENT 或 ENOTDIR。"""
    if isinstance(错误,OSError):#宿主错误
        return 错误.errno in (errno.ENOENT,errno.ENOTDIR)#缺失或非目录
    码=getattr(错误,'code',None)#Node码
    return 码=='ENOENT' or 码=='ENOTDIR'#缺失类

def 宿主探测文件(路径,信号=None):#用宿主stat探测文件
    """返回三分探测：present/absent/unavailable。"""
    try:#尝试stat
        若已中止则抛出(信号)#已取消则抛出
        信息=os.stat(路径)#取路径元数据
        若已中止则抛出(信号)#stat后再次检查取消
        if not stat.S_ISREG(信息.st_mode):#非普通文件当作缺失
            return {'kind':'absent'}#缺失
        return {'kind':'present','info':{'size':信息.st_size}}#存在则记下大小
    except OSError as 错误:#stat抛错
        return {'kind':'absent'} if 是否缺失路径错误(错误) else {'kind':'unavailable'}#缺失与其他失败分开

def 提供方探测文件(路径,文件系统,信号=None):#用提供方resolve+stat探测文件
    """返回三分探测。"""
    try:#尝试resolve再stat
        目标=文件系统.解析(路径,信号选项(信号))#解析稳定目标
        若已中止则抛出(信号)#resolve后检查取消
        信息=文件系统.状态(目标,信号)#取目标元数据
        若已中止则抛出(信号)#stat后检查取消
        if 信息 is None or 信息['type']!='file':#非文件当作缺失
            return {'kind':'absent'}#缺失
        元={'target':目标,'version':信息['version']}#目标与版本
        if 'size' in 信息:#有大小
            元['size']=信息['size']#带上
        return {'kind':'present','info':元}#存在
    except 文件系统错误:#吞掉resolve/stat的提供方异常，取消除外
        若已中止则抛出(信号)#取消优先
        return {'kind':'unavailable'}#其余当作暂时不可用

def 探测文件(路径,文件系统=None,信号=None):#按是否有提供方选择探测实现
    """返回三分探测。"""
    return 宿主探测文件(路径,信号) if 文件系统 is None else 提供方探测文件(路径,文件系统,信号)#无提供方走宿主stat

def 存在为标记(路径,文件系统=None,信号=None):#判断根标记路径是否存在
    """标记路径是否存在。"""
    if 文件系统 is not None:#有提供方
        try:#尝试resolve再stat
            目标=文件系统.解析(路径,信号选项(信号))#解析标记路径
            return 文件系统.状态(目标,信号) is not None#有元数据即存在
        except 文件系统错误:#吞掉提供方失败，暂当标记不存在
            若已中止则抛出(信号)#取消优先
            return False#当前把失败当成不存在
    try:#宿主stat
        若已中止则抛出(信号)#stat前检查取消
        os.stat(路径)#路径存在即可，不要求是文件
        若已中止则抛出(信号)#stat后检查取消
        return True#存在
    except OSError:#吞掉宿主stat失败
        return False#当作标记不存在

def 寻找项目根(工作目录,标记列表,文件系统=None,信号=None):#向上寻找项目根
    """从会话 cwd 向上走到第一个含已配置根标记的目录。没有任何标记时为 cwd。"""
    当前=os.path.abspath(工作目录)#从绝对cwd开始
    while True:#一直向上直到根或命中标记
        for 标记 in 标记列表:#逐个检查标记
            if 存在为标记(os.path.join(当前,标记),文件系统,信号):#命中则当前目录即项目根
                return 当前#项目根
        父=os.path.dirname(当前)#上一级
        if 父==当前:#已到文件系统根则回退cwd
            return os.path.abspath(工作目录)#回退cwd
        当前=父#继续向上

def 祖先链(根,工作目录):#构建根到cwd的祖先链
    """构建含两端的根到 cwd 目录链。从最宽到最具体。"""
    链=[]#收集从cwd向上的目录
    当前=os.path.abspath(工作目录)#从绝对cwd开始
    解析根=os.path.abspath(根)#绝对项目根
    while 当前!=解析根:#尚未走到根
        链.append(当前)#记下当前目录
        父=os.path.dirname(当前)#上一级
        if 父==当前:#已到文件系统根则停
            break#停
        当前=父#继续向上
    链.append(解析根)#最后纳入根
    链.reverse()#改成从根到cwd
    return 链#目录链

def 后代目录之间(根,触及路径):#cwd与触及路径之间的后代目录
    """找出 cwd 与被触及文件之间穿过的后代目录。"""
    解析根=os.path.abspath(根)#绝对根
    目标路径=os.path.abspath(触及路径) if os.path.isabs(触及路径) else os.path.abspath(os.path.join(解析根,触及路径))#归一触及路径
    目标目录=os.path.dirname(目标路径)#触及文件所在目录
    相对=os.path.relpath(目标目录,解析根)#相对根的目录
    if 相对=='.' or 相对.startswith('..') or os.path.isabs(相对):#不在根内则无后代
        return []#无
    return 祖先链(解析根,目标目录)[1:]#去掉根本身

def 相对展示(根,路径):#计算相对展示路径
    """把绝对指令路径转成相对项目根的展示形式。"""
    return os.path.relpath(路径,根).replace('\\','/')#相对项目根

def 用户全局展示路径(家目录):#用户全局文件的展示路径
    """家目录展示名加固定文件名。"""
    return 主目录展示(家目录)+'/AGENTS.md'#家目录展示名加固定文件名

def 目录下现存指令文件(目录,根,指令文件候选,文件系统=None,信号=None):#列出某目录下存在的全部候选
    """返回该目录命中的候选。"""
    找到=[]#收集存在的候选
    for 候选 in 指令文件候选:#按配置顺序探测
        路径=os.path.join(目录,候选)#拼绝对路径
        探测=探测文件(路径,文件系统,信号)#三分探测
        种类=探测['kind']#探测种类
        if 种类=='present':#存在
            项={'absolutePath':路径,'displayPath':相对展示(根,路径)}#路径身份
            项.update(探测['info'])#带上探测元数据
            找到.append(项)#记下
            continue#下一候选
        if 种类 in ('absent','unavailable'):#缺失或失败则跳过该候选
            continue#跳过
        raise 智能体命令错误('StatFileProbe')#不可达：封闭联合
    return 找到#返回该目录命中列表

def 发现指令文件(选项,文件系统=None):#发现用户全局与根到cwd的全部候选
    """按模型优先级返回去重候选。"""
    配置值=解析发现配置(选项)#解析发现配置
    文件列表=[]#收集候选
    已见=set()#按绝对路径去重
    def 加入(文件):#加入尚未见过的路径
        """按绝对路径去重追加。"""
        if 文件['absolutePath'] in 已见:#已见则跳过
            return#跳过
        已见.add(文件['absolutePath'])#记下路径
        文件列表.append(文件)#按发现顺序追加
    用户全局=os.path.join(配置值['dshHome'],用户全局文件)#用户全局AGENTS.md
    全局探测=探测文件(用户全局,文件系统,选项['signal'] if 'signal' in 选项 else None)#探测全局文件
    全局种类=全局探测['kind']#探测种类
    if 全局种类=='present':#存在
        项={'absolutePath':用户全局,'displayPath':用户全局展示路径(配置值['dshHome'])}#全局候选
        项.update(全局探测['info'])#带上探测元数据
        加入(项)#加入
    elif 全局种类 in ('absent','unavailable'):#全局文件不是硬性必需
        pass#放过
    else:#不可达
        raise 智能体命令错误('StatFileProbe')#封闭联合
    工作目录=os.path.abspath(选项['cwd'])#绝对会话cwd
    项目根=选项['projectRoot'] if 'projectRoot' in 选项 else None#已选定的项目根
    if 项目根 is None:#未选定
        项目根=寻找项目根(工作目录,配置值['projectRootMarkers'],文件系统,选项['signal'] if 'signal' in 选项 else None)#否则向上寻找
    for 目录 in 祖先链(项目根,工作目录):#从根走到cwd
        for 候选组 in (配置值['instructionFileCandidates'],配置值['localInstructionFileCandidates']):#先基线后本地覆盖
            for 文件 in 目录下现存指令文件(目录,项目根,候选组,文件系统,选项['signal'] if 'signal' in 选项 else None):#该目录该组候选
                加入(文件)#按路径去重追加
    return 文件列表#返回发现列表

def 发现基线指令文件(选项):#只返回路径身份
    """发现宿主可见的用户全局与根到 cwd 指令候选。"""
    return [{'absolutePath':文件['absolutePath'],'displayPath':文件['displayPath']} for 文件 in 发现指令文件(选项)]#丢掉探测元数据

def 宿主文本块(路径,信号=None):#按UTF-8块读取宿主文件
    """逐块产出 UTF-8 文本。"""
    若已中止则抛出(信号)#读前检查
    with open(路径,'r',encoding='utf-8') as 句柄:#打开文件
        while True:#逐块
            若已中止则抛出(信号)#每块检查取消
            块=句柄.read(65536)#读一块
            if 块=='':#读完
                break#结束
            yield 块#产出

def 有界读取(文件,单源上限,文件系统=None,信号=None):#按单文件字节上限读取
    """超限、消失或不可读则为 None。"""
    若已中止则抛出(信号)#读取前检查取消
    大小=文件['size'] if 'size' in 文件 else None#元数据大小
    if 大小 is not None and 大小>单源上限:#元数据已超上限则不读
        return None#不读
    try:#尝试流式读
        目标=文件['target'] if 'target' in 文件 else None#提供方目标
        if 文件系统 is None or 目标 is None:#无提供方或无目标
            块流=宿主文本块(文件['absolutePath'],信号)#走宿主流
        else:#有提供方
            块流=文件系统.流文本(目标,信号)#走提供方文本流
        片段=[]#收集块
        字节=0#已读UTF-8字节
        for 块 in 块流:#逐块累计
            若已中止则抛出(信号)#每块检查取消
            字节+=len(块.encode('utf-8'))#按UTF-8计字节
            if 字节>单源上限:#累计超上限则丢弃
                return None#丢弃
            片段.append(块)#收下该块
        若已中止则抛出(信号)#读完再检查取消
        return ''.join(片段)#拼成完整文本
    except (OSError,文件系统错误):#吞掉元数据探测之后文件消失或不可读
        若已中止则抛出(信号)#取消优先
        return None#当作该候选不可用

def 按目录去重指令文件(文件列表):#按目录去空白内容去重
    """丢掉同目录里去空白内容与更早兄弟重复的较晚候选。"""
    已保留摘要={}#每目录已保留摘要
    保留=[]#保留列表
    for 文件 in 文件列表:#按发现顺序
        目录=os.path.dirname(文件['displayPath']).replace('\\','/')#用展示路径的目录分组
        摘要集=已保留摘要.get(目录)#该目录已见摘要
        if 摘要集 is None:#该目录第一次出现
            摘要集=set()#新建摘要集
            已保留摘要[目录]=摘要集#记下
        摘要=去空白指令摘要(文件['content'])#去首尾空白后的内容身份
        if 摘要 in 摘要集:#同目录重复则丢掉较晚者
            continue#丢掉
        摘要集.add(摘要)#记下本摘要
        保留.append(文件)#保留该文件
    return 保留#返回去重结果

def 加载基线指令集(选项,文件系统=None):#加载基线并带上保留文件
    """加载一份基线，以及渲染后保留的文件。空/禁用时为 None。"""
    配置值=解析配置(选项)#解析完整运行时配置
    if 配置值['maxBytes']<=0 or not (配置值['maxBytes']==配置值['maxBytes']):#非正或NaN
        return None#禁用
    import math#有限数检查
    if not math.isfinite(配置值['maxBytes']):#非有限
        return None#禁用
    if 配置值['maxSourceBytes']<=0 or not math.isfinite(配置值['maxSourceBytes']):#单源上限非法则禁用
        return None#禁用
    发现=发现指令文件(选项,文件系统)#发现候选
    已载=[]#成功读出的文件
    for 文件 in 发现:#逐个按上限读
        内容=有界读取(文件,配置值['maxSourceBytes'],文件系统,选项['signal'] if 'signal' in 选项 else None)#带上限读取
        if 内容 is not None:#读成功
            项={'absolutePath':文件['absolutePath'],'displayPath':文件['displayPath'],'content':内容}#记下内容
            if 'version' in 文件:#有版本
                项['version']=文件['version']#带上
            已载.append(项)#收下
    去重=按目录去重指令文件(已载)#按目录去重
    if len(去重)==0:#没有可渲染文件
        if ('replacePreviousBaseline' not in 选项) or 选项['replacePreviousBaseline'] is not True:#非替换模式则表示无基线
            return None#无基线
        结果=渲染工作区指令集([],{'maxBytes':配置值['maxBytes'],'replacePreviousBaseline':True})#空集显式替换
        return {'rendered':结果['rendered'],'observed':[],'included':结果['included']}#空观察与空纳入
    渲染选项={'maxBytes':配置值['maxBytes']}#渲染字节预算
    if 'replacePreviousBaseline' in 选项:#声明了替换
        渲染选项['replacePreviousBaseline']=选项['replacePreviousBaseline']#原样转发
    结果=渲染工作区指令集(去重,渲染选项)#按预算渲染去重后的文件
    return {'rendered':结果['rendered'],'observed':已载,'included':结果['included']}#观察集与纳入集

def 加载基线指令(选项,文件系统=None):#只返回渲染结果
    """发现、读取并渲染基线指令链。什么都加载不了时为 None。"""
    集合=加载基线指令集(选项,文件系统)#完整集合
    return None if 集合 is None else 集合['rendered']#从完整集合取出渲染

def 探测作用域指令(作用域,项目根,已解析,文件系统,信号=None):#探测单个作用域候选
    """三分状态：present/absent/unavailable。"""
    拆=解码作用域键(作用域)#拆目录与候选文件名
    目录=拆['directory']#目录分量
    候选名=拆['candidateName']#候选文件名
    if 目录==用户全局目录:#用户全局占位
        绝对目录=已解析['dshHome']#用家目录
    elif 目录=='.':#项目根
        绝对目录=项目根#项目根
    else:#相对项目目录
        绝对目录=os.path.join(项目根,目录)#拼相对目录
    绝对路径=os.path.join(绝对目录,候选名)#绝对候选路径
    try:#尝试resolve再stat
        目标=文件系统.解析(绝对路径,信号选项(信号))#解析稳定目标
        信息=文件系统.状态(目标,信号)#取元数据
    except 文件系统错误:#吞掉提供方异常
        若已中止则抛出(信号)#取消优先
        return {'kind':'unavailable'}#其余为暂时不可用
    if 信息 is None or 信息['type']!='file':#非文件为确认缺失
        return {'kind':'absent'}#缺失
    展示=用户全局展示路径(已解析['dshHome']) if 目录==用户全局目录 else 相对展示(项目根,绝对路径)#全局用家目录展示
    文件={'absolutePath':绝对路径,'displayPath':展示,'target':目标,'version':信息['version']}#组装探测文件
    if 'size' in 信息:#有大小
        文件['size']=信息['size']#带上
    return {'kind':'present','file':文件}#报告存在

def 读取作用域指令(文件,单源上限,文件系统,信号=None):#读取已探测的作用域候选
    """按配置的源上限读取。不可用时为 None。"""
    内容=有界读取(文件,单源上限,文件系统,信号)#按上限读取
    if 内容 is None:#超限或不可读
        return None#不可用
    return {#组装已加载文件
        'absolutePath':文件['absolutePath'],#绝对路径
        'displayPath':文件['displayPath'],#展示路径
        'content':内容,#正文
        'version':文件['version'],#沿用探测版本
    }#返回对象结束
