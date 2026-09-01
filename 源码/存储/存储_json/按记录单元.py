"""一个已打开的 `per-record` 布局 JSON 单元。"""
import asyncio,json,os,re,shutil#异步、JSON、路径、正则、删除
from ..存储.错误 import 存储错误#存储错误
from .格式 import 单元状态,序列化记录,解析记录#格式
from .原子 import 原子写#原子写
__all__=['打开按记录单元','按记录Json单元']#仅中文公开名

安全键正则=re.compile(r'^[a-zA-Z0-9_-]+$')#路径安全键

def _断言安全键(单元名,键):#拒绝不安全键
    if 安全键正则.fullmatch(键) is None:#不安全
        raise Exception(f"unit '{单元名}': per-record key '{键}' is not path-safe (must match {安全键正则.pattern})")#拒绝

async def _读记录(路径,版本):#读一条记录文档
    try:#读文件
        with open(路径,'r',encoding='utf-8') as 文件:#打开
            return 解析记录(文件.read(),版本)#解析
    except OSError:#读失败
        return None#外文档

async def _加载表记录(记录映射,版本,目录):#加载一张表的记录
    有文档=False#目录里是否有 .json
    try:#列目录
        条目=os.listdir(目录)#列文件
    except FileNotFoundError:#缺目录
        return False#无文档
    for 名 in 条目:#每个文件
        if not 名.endswith('.json'):#非记录文件
            continue#跳过
        有文档=True#见到文档路径
        键=名[:-5]#去 .json
        if 安全键正则.fullmatch(键) is None:#键不安全
            continue#跳过
        值=await _读记录(os.path.join(目录,名),版本)#读记录
        if 值 is not None:#有效记录
            记录映射[键]=值#记下
    return 有文档#是否见到文档路径

async def _引导遗留单元(描述符,目录,状态):#从 legacy 整文件引导
    遗留路径=os.path.join(os.path.dirname(目录),f'{描述符.name}.json')#legacy 文件
    try:#读 legacy
        with open(遗留路径,'r',encoding='utf-8') as 文件:#打开
            文本=文件.read()#读全文
    except FileNotFoundError:#无 legacy
        return#结束
    except OSError as 错误:#其它错
        raise 错误#原样抛
    try:#解析 legacy
        文档=json.loads(文本)#JSON
    except json.JSONDecodeError:#损坏
        return#不解释
    if not isinstance(文档,dict):#不是对象
        return#不解释
    单元头=文档.get('unit')#头
    if not isinstance(单元头,dict) or 单元头.get('name')!=描述符.name:#外单元
        return#不引导
    表对象=文档.get('tables')#表
    if not isinstance(表对象,dict):#不是对象
        return#不引导
    for 表名,记录 in 表对象.items():#每张表
        目标=状态.tables.get(表名)#声明表
        if 目标 is None:#未声明
            continue#跳过
        if not isinstance(记录,dict):#表不是对象
            continue#跳过
        for 键,值 in 记录.items():#每条记录
            路径=os.path.join(目录,表名,f'{键}.json')#目标路径
            os.makedirs(os.path.dirname(路径),mode=0o700,exist_ok=True)#建父目录
            await asyncio.to_thread(原子写,路径,序列化记录(描述符.version,值))#写记录
            目标[键]=值#记入状态

async def _加载按记录状态(描述符,目录):#从目录树重建状态
    状态=单元状态(描述符.version,None,{表: {} for 表 in 描述符.tables})#空树
    有新文档=False#是否见到新树文档
    try:#列单元目录
        条目=os.listdir(目录)#列项
    except FileNotFoundError:#缺目录
        条目=None#空树
    if 条目 is not None:#目录存在
        for 名 in 条目:#每项
            完整=os.path.join(目录,名)#完整路径
            if os.path.isdir(完整) and 名 in 状态.tables:#声明表目录
                if await _加载表记录(状态.tables[名],描述符.version,完整):#加载表
                    有新文档=True#见到文档
            elif 名=='global.json' and 描述符.hasGlobal:#全局文件
                全局=await _读记录(完整,描述符.version)#读全局
                if 全局 is not None:#有效
                    状态.全局值=全局#记下
                    有新文档=True#见到文档
    if not 有新文档:#可跑 legacy 引导
        await _引导遗留单元(描述符,目录,状态)#引导
    return 状态#权威状态

class 按记录Json单元:#per-record 布局；目录即状态
    def __init__(自身,描述符,目录,关闭回调):#构造
        自身._描述符=描述符#描述符
        自身._目录=目录#单元目录
        自身._关闭回调=关闭回调#释放槽
        自身._已关=False#关闭旗标
        自身._在途=set()#在途写
    async def loadAll(自身):#重读树
        自身._断言打开()#已关拒绝
        状态=await _加载按记录状态(自身._描述符,自身._目录)#重建
        表={}#投影
        for 表名,记录 in 状态.tables.items():#每张表
            表[表名]=dict(记录)#转 dict
        return {'tables':表,'global':状态.全局值}#快照
    async def putRecord(自身,表,键,值):#写一条记录
        自身._断言打开()#已关拒绝
        _断言安全键(自身._描述符.name,键)#键安全
        路径=os.path.join(自身._目录,表,f'{键}.json')#记录路径
        await 自身._跟踪(自身._写文档(路径,值))#耐久写
    async def deleteRecord(自身,表,键):#删一条记录
        自身._断言打开()#已关拒绝
        _断言安全键(自身._描述符.name,键)#键安全
        路径=os.path.join(自身._目录,表,f'{键}.json')#记录路径
        await 自身._跟踪(asyncio.to_thread(_静默删,路径))#删文件
    async def setGlobal(自身,值):#写全局
        自身._断言打开()#已关拒绝
        if not 自身._描述符.hasGlobal:#未声明
            raise Exception(f"unit '{自身._描述符.name}' does not declare a global slot")#调用方错误
        路径=os.path.join(自身._目录,'global.json')#全局路径
        await 自身._跟踪(自身._写文档(路径,值))#耐久写
    async def close(自身):#关闭
        if 自身._已关:#重复
            await asyncio.gather(*list(自身._在途),return_exceptions=True)#排空
            return#结束
        自身._已关=True#标记
        await asyncio.gather(*list(自身._在途),return_exceptions=True)#排空
        自身._关闭回调()#释放槽
    def _断言打开(自身):#打开守卫
        if 自身._已关:#已关
            raise 存储错误('closed',f"unit '{自身._描述符.name}' is closed")#拒绝
    async def _写文档(自身,路径,值):#写一条文档
        os.makedirs(os.path.dirname(路径),mode=0o700,exist_ok=True)#建父目录
        await asyncio.to_thread(原子写,路径,序列化记录(自身._描述符.version,值))#原子写
    async def _跟踪(自身,写):#跟踪在途写
        自身._在途.add(写)#加入
        try:#等写
            await 写#等完成
        finally:#摘掉
            自身._在途.discard(写)#摘掉

def _静默删(路径):#删文件忽略缺失
    try:#删
        os.remove(路径)#删除
    except FileNotFoundError:#已缺失
        pass#幂等

async def 打开按记录单元(描述符,根目录,关闭回调):#打开 per-record 单元
    """打开 `<root>/<name>/`；打开时不碰介质。"""
    目录=os.path.join(根目录,描述符.name)#单元目录
    return 按记录Json单元(描述符,目录,关闭回调)#无状态单元
