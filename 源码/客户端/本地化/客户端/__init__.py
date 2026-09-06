"""浏览器侧语言注册表。绑定后的翻译函数对注入消费方保持稳定身份。

对齐上游 `locale/src/client/index.ts`。公开面仅中文名。
"""
import re#模板占位替换
from ..语言设置 import 语言偏好字段,语言设置命名空间,本地化错误#偏好字段、命名空间与本包错误
from ..词表 import 中文,英文,设置中文,设置英文#公共与设置词表
from .设置存储 import 创建语言行存储#语言行存储
from .语言行 import 语言行#语言行组件

__all__=[#仅中文公开名
    '注入','应用','语言运行时','回退语言','公共命名空间','设置命名空间',
    '创建语言行存储','语言行','本地化错误',
]#公开面结束

回退语言='zh'#回退语言为中文
公共命名空间='common'#公共命名空间
设置命名空间='settings.locale'#设置行命名空间
注入=['slots','connection','remote','settingsScope']#依赖槽位、连接、远端与设置作用域

语言定义表=(#冻结的可选语言表
    {'id':'zh','label':'中文'},#中文
    {'id':'en','label':'English'},#英文
)#语言表结束

占位模式=re.compile(r'\{([A-Za-z0-9_]+)\}',re.ASCII)#模板 {name} 占位

def 探测浏览器语言():
    """浏览器请求的第一种随包语言；非浏览器返回 None。"""
    if 'window' not in globals():#非浏览器
        return None#未识别
    if 'navigator' not in globals():#无导航
        return None#未识别
    导航=globals()['navigator']#navigator
    标签表=[]#候选标签
    语言列表=导航.languages#languages
    if 语言列表 is not None:#有列表
        标签表=list(语言列表)#拷贝
    单标签=导航.language#language
    if 单标签 is not None:#有单标签
        标签表.append(单标签)#追加
    for 标签 in 标签表:#逐个匹配
        主标签=str(标签).lower().split('-')[0]#主子标签
        for 定义 in 语言定义表:#随包列表
            if 定义['id']==主标签:#命中
                return 定义['id']#该语言
    return None#都不在随包列表

def 解析初始语言():
    """浏览器自带语言优先于回退语言。"""
    探测=探测浏览器语言()#浏览器语言
    if 探测 is None:#浏览器未识别
        return 回退语言#回退中文
    return 探测#浏览器语言

class 语言运行时:
    """词表注册表加语言偏好。查找链：当前语言命名空间 → zh 回退 → common → 键本身。"""
    def __init__(自身,上下文,宿主=None):
        """播种临时语言；有宿主则订阅并采纳。"""
        自身.上下文=上下文#保存上下文
        自身.宿主=宿主#保存作用域
        自身.词表表={}#命名空间 → 语言 → 词表
        自身.绑定表={}#命名空间 → 稳定翻译函数
        自身.临时=解析初始语言()#浏览器推导的临时语言
        自身.快照={'active':自身.临时,'locales':list(语言定义表),'revision':0}#初始快照
        自身.监听者=set()#LocaleFace 订阅者
        if 宿主 is not None:#有持久化作用域
            def 订阅采纳():
                """登记采纳订阅。"""
                def 采纳宿主():
                    """作用域变更时采纳。"""
                    自身.采纳(宿主)#采纳
                return 宿主.subscribe(采纳宿主)#订阅
            上下文.副作用(订阅采纳,'locale: settings scope adoption')#生命周期
            自身.采纳(宿主)#先采纳当前选择

    def getLocale(自身):
        """读取当前不可变语言快照。方法名对齐 LocaleFace。"""
        return 自身.快照#当前快照

    def getSnapshot(自身):
        """LocaleFace getSnapshot。"""
        return 自身.快照#当前快照

    def subscribe(自身,回调):
        """每次快照变更都通知。"""
        自身.监听者.add(回调)#加入
        def 退订():
            """取消订阅。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def setLocale(自身,标识):
        """切换当前语言 — 唯一的用户偏好写入入口。"""
        匹配=None#命中项
        for 项 in 自身.快照['locales']:#在已提供列表里找
            if 项['id']==标识:#命中
                匹配=项#记下
                break#找到
        if 匹配 is None:#未登记
            raise 本地化错误('locale "'+标识+'" is not registered')#失败
        if 自身.快照['active']==匹配['id']:#已经是当前
            return#跳过
        自身.发布(匹配['id'],True)#发布语言切换
        if 自身.宿主 is not None:#有作用域则持久化
            自身.宿主.set(语言偏好字段,匹配['id'])#不等待

    def 采纳(自身,宿主):
        """采纳作用域已接受的持久化选择，不写回。分区是设置载荷 dict。"""
        快照=宿主.getSnapshot()#作用域快照 dict
        if 'value' not in 快照:#分区尚未到达
            return#跳过
        分区=快照['value']#当前分区值
        if 分区 is None:#分区尚未到达
            return#跳过
        if 'preference' not in 分区:#无显式偏好
            目标=自身.临时#浏览器推导
        else:#显式偏好
            目标=分区['preference']#已登记
        if 自身.快照['active']==目标:#已经是目标
            return#跳过
        自身.发布(目标,True)#发布语言切换

    def register(自身,命名空间,语言或词表,词表=None):
        """一次登记一个命名空间的词表；重复 (ns, locale) 抛错。"""
        if isinstance(语言或词表,str):#单语言形态
            对表=[(语言或词表,词表)]#单对
        else:#全表形态
            对表=list(语言或词表.items())#转成对
        语言表=自身.词表表[命名空间] if 命名空间 in 自身.词表表 else None#该命名空间已有的语言表
        if 语言表 is None:#第一次登记该命名空间
            语言表={}#新建
            自身.词表表[命名空间]=语言表#写入
        for 语言,_ in 对表:#先查重复
            if 语言 in 语言表:#已有
                raise 本地化错误('locale namespace "'+命名空间+'" already has locale "'+语言+'"')#单占用者
        for 语言,条目 in 对表:#写入各语言词表
            语言表[语言]=条目#写入
        自身.发布(自身.快照['active'],False)#只抬修订
        def 拆除():
            """幂等拆除本次写入的语言。"""
            if 命名空间 not in 自身.词表表:#无
                return#跳过
            拥有=自身.词表表[命名空间]#取出
            删过=False#是否真正删过
            for 语言,条目 in 对表:#只删本次同一引用
                if 语言 in 拥有 and 拥有[语言] is 条目:#仍是本次
                    del 拥有[语言]#去掉
                    删过=True#记下
            if 删过:#删过才抬修订
                自身.发布(自身.快照['active'],False)#抬修订
        return 拆除#拆除器

    def bind(自身,命名空间):
        """返回按命名空间稳定的翻译函数。"""
        if 命名空间 in 自身.绑定表:#已有稳定函数
            return 自身.绑定表[命名空间]#复用
        def 翻译(键,参数=None):
            """调用时读取当前语言。"""
            return 自身.翻译(命名空间,键,参数)#查找链
        自身.绑定表[命名空间]=翻译#记下稳定引用
        return 翻译#新建函数

    def 翻译(自身,命名空间,键,参数=None):
        """条目命名空间 → common → 键本身。"""
        模板=自身.查找(命名空间,键)#先查条目命名空间
        if 模板 is None and 命名空间!=公共命名空间:#再查公共
            模板=自身.查找(公共命名空间,键)#公共
        if 模板 is None:#都没有
            模板=键#露出键本身
        if 参数 is None:#无占位
            return 模板#原文
        def 替换(匹配):
            """未知占位保持原文。"""
            名=匹配.group(1)#占位名
            if 名 in 参数:#有值
                return str(参数[名])#字符串化
            return 匹配.group(0)#保持
        return 占位模式.sub(替换,模板,count=0)#全部占位

    def 查找(自身,命名空间,键):
        """先当前语言再 zh。"""
        if 命名空间 not in 自身.词表表:#无
            return None#未命中
        语言表=自身.词表表[命名空间]#语言表
        当前语言=自身.快照['active']#当前
        if 当前语言 in 语言表:#有当前语言词表
            当前=语言表[当前语言]#当前语言词表
            if 键 in 当前:#命中
                return 当前[键]#模板
        if 回退语言 in 语言表:#有 zh 回退
            回退=语言表[回退语言]#zh 回退
            if 键 in 回退:#命中
                return 回退[键]#模板
        return None#未命中

    def 发布(自身,当前,语言已变):
        """推进修订；语言切换才发 locale/change。"""
        自身.快照={#新快照
            'active':当前,#当前语言
            'locales':自身.快照['locales'],#可选列表不变
            'revision':自身.快照['revision']+1,#修订加一
        }#快照结束
        if 语言已变:#语言切换
            自身.上下文.广播('locale/change',自身.快照)#发事件
        for 回调 in list(自身.监听者):#快照后逐个通知
            try:#订阅者抛错不得打断其余
                回调()#通知
            except BaseException as 错误:#订阅者异常契约未定，槽位回调可抛任意类型
                print('locale subscriber crashed:',错误)#诊断

def 应用(上下文):
    """用底表提供语言服务，并把语言偏好行登记进常规条目分区。"""
    宿主=上下文.settingsScope.bind({'namespace':语言设置命名空间})#绑定语言设置作用域
    语言=语言运行时(上下文,宿主)#语言运行时
    语言.register(公共命名空间,{'zh':中文,'en':英文})#登记公共词表
    语言.register(设置命名空间,{'zh':设置中文,'en':设置英文})#登记设置行词表
    上下文.提供服务('locale',语言)#提供 ctx.locale
    上下文.slots.installLocale(语言)#安装给槽位渲染
    存储=创建语言行存储()#语言行存储
    已绑动作={'ref':None}#槽位绑定后的动作

    def 同步(快照):
        """仓库尚未绑定时跳过。快照是 dict。"""
        动作=已绑动作['ref']#已绑动作
        if 动作 is None:#尚未绑定
            return#跳过
        动作['sync'](#镜像
            快照['active'],#当前语言
            [{'id':项['id'],'label':项['label']} for 项 in 快照['locales']],#选项行
            快照['revision'],#修订号
        )#结束 sync

    上下文.监听('locale/change',同步)#语言切换时同步仓库

    def 注入面(动作):
        """保存动作并立刻对齐当前快照。setLocale 是注入面键名。"""
        已绑动作['ref']=动作#保存
        同步(语言.getLocale())#立刻对齐
        def 写入语言(标识):
            """写入偏好。"""
            语言.setLocale(标识)#切换
        return {'setLocale':写入语言}#注入给组件

    def 登记行():
        """把语言行注入通用设置条目槽。"""
        return 上下文.slots.register({#登记
            'name':'settings.general.item',#槽名
            'id':'language',#条目 id
            'order':0,#排在最前
            'store':存储,#语言行存储
            'locale':设置命名空间,#本行文案命名空间
            'inject':注入面,#注入动作
        },语言行)#语言行组件
    上下文.slots.inject('settings.general.item',登记行)#等槽出现

inject=注入#框架槽
apply=应用#框架槽
