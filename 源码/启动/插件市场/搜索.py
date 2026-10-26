'对一份已校验索引做过滤、模糊匹配和排序'
import time,unicodedata,threading#让出、规范化、构建锁
from ...工具.值 import 断言永不#封闭排序

__all__=['市场搜索']#仅中文公开名

构建块=500#每处理这么多个插件让出一次

def 是词字符(字符):
    '字母、组合记号或数字'
    类别=unicodedata.category(字符)#Unicode 类别
    return 类别[:1] in ('L','M','N')#词字符

def 是汉字系(字符):
    '汉字、假名、谚文，以及不空格分词的共用记号'
    码位=ord(字符)#码位
    if 0x1100<=码位<=0x11FF or 0x2E80<=码位<=0x2FDF:#谚文字母或部首
        return True#是
    if 码位 in (0x3005,0x3006,0x3007,0x303B) or 0x3040<=码位<=0x30FF:#々〆〇与假名，含ー
        return True#是
    if 0x31F0<=码位<=0x31FF or 0x3400<=码位<=0x4DBF or 0x4E00<=码位<=0x9FFF:#小假名与汉字
        return True#是
    if 0xAC00<=码位<=0xD7AF or 0xF900<=码位<=0xFAFF or 0xFF66<=码位<=0xFF9D:#谚文音节、兼容汉字、半角片假名
        return True#是
    if 0x20000<=码位<=0x3FFFF:#扩展区
        return True#是
    return False#否

def 搜索词(文本):
    'NFKC 后拆成词。汉字系连续段变成二字组并保留末字，其余连续段整段为一个词'
    规范=unicodedata.normalize('NFKC',文本)#同一词面
    词表=[]#结果
    缓冲=[]#当前段
    缓冲是汉字=None#当前段种类

    def 收下():
        '把当前段收成词'
        nonlocal 缓冲是汉字
        if len(缓冲)==0:#空
            return#无
        一段=''.join(缓冲)#段文本
        缓冲.clear()#清空
        if not 缓冲是汉字:#非汉字系
            词表.append(一段)#整段
        else:#汉字系没有空格
            字符表=list(一段)#一字一个码位
            for 位置 in range(1,len(字符表)):#相邻对
                词表.append(字符表[位置-1]+字符表[位置])#二字
            词表.append(字符表[-1])#末字
        缓冲是汉字=None#复位

    for 字符 in 规范:#逐字
        if not 是词字符(字符):#分隔
            收下()#结束上一段
            continue#下一个
        汉字=是汉字系(字符)#本字
        if len(缓冲)>0 and 汉字!=缓冲是汉字:#种类变了
            收下()#先收上一段
        缓冲.append(字符)#续上
        缓冲是汉字=汉字#记下种类
    收下()#尾段
    return 词表#尚未小写

def 变体(文本):
    '本地化文本的每一种语言'
    if 文本 is None:#无
        return []#空
    if isinstance(文本,str):#单语
        return [文本]#自身
    if isinstance(文本,dict):#多语
        return [值 for 值 in 文本.values() if isinstance(值,str)]#各语言
    return []#其余不索引

def 编辑距离(左词,右词,上限):
    '有上限的编辑距离；超过上限则返回上限加一'
    if abs(len(左词)-len(右词))>上限:#长度差已超过
        return 上限+1#失败
    上一行=list(range(len(右词)+1))#第一行
    for 左字序号,左字 in enumerate(左词):#左
        本行=[左字序号+1]#删除
        行最小=左字序号+1#本行最小
        for 右字序号,右字 in enumerate(右词):#右
            替换代价=0 if 左字==右字 else 1#相等则不替换
            距离=min(上一行[右字序号+1]+替换代价,上一行[右字序号]+1,本行[右字序号]+1)#替换、插入、删除
            本行.append(距离)#写入
            if 距离<行最小:#更小
                行最小=距离#记下
        if 行最小>上限:#整行都超过
            return 上限+1#放弃
        上一行=本行#滚动
    return 上一行[-1]#距离

def 词可匹配(查询词,索引词):
    '前缀，或查询词至少四字时有界编辑距离'
    if 索引词.startswith(查询词):#查询词是索引词的前缀，含相等
        return True#命中
    if len(查询词)<4:#短词只认前缀
        return False#否
    距离上限=min(2,round(0.2*len(查询词)))#五分之一，最多 2
    if 距离上限<=0:#没有额度
        return False#否
    return 编辑距离(查询词,索引词,距离上限)<=距离上限#模糊

class 市场搜索:
    '对一份索引匹配查询。第一次带文本的查询才建词表'
    def __init__(自身,索引):
        '记下已校验索引'
        自身.索引=索引#文档
        自身.引擎=None#词到 (插件序号, 字段权重)
        自身.构建锁=threading.Lock()#只建一次

    def 选择(自身,选择条件):
        '选出匹配的插件并排好序'
        插件表=自身.索引['plugins']#全部插件
        文本=选择条件.get('text') or ''#查询文本
        得分={}#序号到分数
        if len(搜索词(文本))==0:#没有词：全部，索引顺序
            位置表=list(range(len(插件表)))#全部位置
        else:#有词
            for 命中 in 自身.搜索(文本):#每个命中
                得分[命中['id']]=命中['score']#分数
            位置表=sorted(得分)#按索引位置
        标签表=选择条件.get('labels') or []#必须全有
        分类=选择条件.get('category')#分类
        匹配=[]#过滤后
        for 位置 in 位置表:#逐个
            元数据=插件表[位置]['metadata']#元数据
            if 分类 is not None and 元数据.get('category')!=分类:#分类不符
                continue#跳过
            已有标签=元数据.get('labels') or []#标签
            if any(标签 not in 已有标签 for 标签 in 标签表):#缺标签
                continue#跳过
            匹配.append(位置)#留下
        return [插件表[位置] for 位置 in 自身.排序(匹配,选择条件['sort'],得分)]#结果顺序

    def 搜索(自身,文本):
        '确保词表已建，再按 AND 匹配'
        if 自身.引擎 is None:#尚未
            with 自身.构建锁:#只一个建
                if 自身.引擎 is None:#仍未
                    自身.引擎=自身.构建()#建
        查询词表=[词.lower() for 词 in 搜索词(文本)]#小写
        每词=[]#每个查询词的序号到权重和
        for 查询词 in 查询词表:#逐词
            本次={}#本词命中
            for 索引词,出现表 in 自身.引擎.items():#已索引词
                if not 词可匹配(查询词,索引词):#不匹配
                    continue#下一个词
                for 序号,权重 in 出现表:#每处出现
                    本次[序号]=本次.get(序号,0)+权重#字段权重相加
            if len(本次)==0:#这个词没有任何插件
                return []#AND 失败
            每词.append(本次)#收下
        候选=set(每词[0])#第一词
        for 本次 in 每词[1:]:#其余词
            候选&=set(本次)#交集
        结果=[]#命中
        for 序号 in 候选:#每个插件
            分数=0#合计
            for 本次 in 每词:#各词
                分数+=本次[序号]#加上
            结果.append({'id':序号,'score':分数})#一条
        return 结果#未排序

    def 构建(自身):
        '名称与标题权重 3，关键词 2，其余 1'
        元数据=自身.索引['metadata']#索引声明
        分类表=元数据.get('categories') or {}#分类
        标签声明=元数据.get('labels') or {}#标签
        引擎={}#词到出现

        def 放入(词语,序号,权重):
            '小写后记入'
            小写词=词语.lower()#小写
            if 小写词=='':#空
                return#不记
            出现=引擎.get(小写词)#已有
            if 出现 is None:#新建
                出现=[]#空
                引擎[小写词]=出现#放入
            出现.append((序号,权重))#记下

        for 序号,插件 in enumerate(自身.索引['plugins']):#逐个插件
            插件元=插件['metadata']#插件元数据
            分类标识=插件元.get('category')#分类
            分类标题=[] if 分类标识 is None else 变体((分类表.get(分类标识) or {}).get('title'))#分类标题
            标签标题=[]#标签标题
            for 标签 in 插件元.get('labels') or []:#每个标签
                标签标题.extend(变体((标签声明.get(标签) or {}).get('title')))#标题
            字段={#可搜索字段
                'name':(插件.get('name') or '',3),#名
                'title':('\n'.join(变体(插件.get('title'))),3),#标题
                'keywords':('\n'.join(关键词 for 关键词 in (插件元.get('keywords') or []) if isinstance(关键词,str)),2),#关键词
                'description':('\n'.join(变体(插件.get('description'))),1),#描述
                'author':(插件.get('author') if isinstance(插件.get('author'),str) else '',1),#作者
                'taxonomy':('\n'.join(分类标题+标签标题),1),#分类与标签
            }#字段结束
            for 文本,权重 in 字段.values():#每个字段
                for 词语 in 搜索词(文本):#每个词
                    放入(词语,序号,权重)#记入
            if (序号+1)%构建块==0:#让出
                time.sleep(0)#其它线程可运行
        return 引擎#词表

    def 排序(自身,位置表,排序,得分):
        '按排序种类重排位置。相同则保持索引顺序'
        种类=排序['kind']#种类
        if 种类=='index':#索引顺序
            return list(位置表)#原样
        if 种类=='relevance':#相关度
            def 相关键(位置):
                '分数高的在前，分数相同按索引位置'
                return (-(得分.get(位置) or 0),位置)#键
            return sorted(位置表,key=相关键)#分高在前
        if 种类=='published' or 种类=='key':#有方向
            方向=1 if 排序.get('direction')=='asc' else -1#升序为正

            def 取值(位置):
                '排序值；没有则为 None，排在最后'
                插件=自身.索引['plugins'][位置]#插件
                if 种类=='published':#最新发布时间
                    return max(版本['publishTimestamp'] for 版本 in 插件['versions'])#最大
                键表=插件['metadata'].get('sortKeys') or {}#排序键
                if 排序['id'] in 键表:#有值
                    return 键表[排序['id']]#值
                return None#没有

            def 比较键(位置):
                'None 在后；有值再按方向'
                排序值=取值(位置)#值
                if 排序值 is None:#缺失
                    return (1,0,位置)#最后，再按索引
                return (0,排序值*方向,位置)#方向已乘进值

            return sorted(位置表,key=比较键)#排好
        return 断言永不(排序)#封闭联合
