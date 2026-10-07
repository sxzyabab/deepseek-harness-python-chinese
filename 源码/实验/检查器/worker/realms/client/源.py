import base64#分块解码
from ......基础设施.js特性 import PromiseEX as 期约扩展#后端方法的返回期约

__all__=['Client源后端']#仅中文公开名

class Client源后端:#Client源后端
    '经公共只读源模型呈现一个 Client 包目录'
    def __init__(自身,目标,会话id,路由,脚本身份):#构造
        '保存依赖'
        自身.目标=目标#目标
        自身.会话id=会话id#会话
        自身.路由=路由#路由
        自身.脚本身份=脚本身份#脚本身份
        自身._脚本={}#脚本表
        自身._目录=None#目录缓存
        自身._已关闭=False#是否已关闭

    def 列脚本(自身):#列脚本
        '确保目录已加载，返回期约，兑现值是脚本描述列表。目录期约只创建一次，之后复用'
        if 自身._已关闭:#已关闭
            已关闭失败=期约扩展()#会话已关闭时直接拒绝的期约
            已关闭失败.拒绝(RuntimeError('客户端源会话已关闭'))#会话已关闭
            return 已关闭失败#返回已拒绝的期约
        if 自身._目录 is None:#惰性加载
            自身._目录=自身._加载目录()#保存目录期约
        return 自身._目录#目录期约

    def 取脚本来源(自身,脚本键):#取脚本来源
        '读 source 分块，返回期约，兑现值是源文本'
        def 读源(路由):#路由解析后读取源
            '按本地脚本键读 source 并校验可用'
            def 校验源(源):#源读完后校验
                '源不可用时拒绝'
                if 源 is None:#不可用
                    raise RuntimeError('客户端脚本源不可用')#抛错
                return 源#返回
            return 自身._读(路由['localKey'],'source').然后(校验源)#读完再校验
        return 自身._路由(脚本键).然后(读源)#路由解析后再读源

    def 取源映射(自身,脚本键):#取源映射
        '读 source-map 分块，返回期约，兑现值是映射文本或 None'
        def 读映射(路由):#路由解析后读取映射
            '按本地脚本键读 source-map'
            return 自身._读(路由['localKey'],'source-map')#读映射
        return 自身._路由(脚本键).然后(读映射)#路由解析后再读映射

    def 订阅(自身,_监听):#订阅
        '无动态发现'
        def 空拆除():#无动态发现
            '无动态发现，拆除为空操作'
            return#空
        return 空拆除#拆除器

    def 关闭(自身):#关闭
        '拒绝本 DevTools 连接拥有的待决读取'
        if 自身._已关闭:#幂等
            return#返回
        自身._已关闭=True#置位
        自身.路由.关闭会话(自身.目标['source'],自身.会话id)#关会话
        自身._脚本.clear()#清脚本

    def _加载目录(自身):#加载目录
        '请求 list-scripts，返回期约'
        def 登记目录(结果):#列表响应到达后登记
            '校验操作名并登记全部脚本'
            结果=自身._期望(结果,'list-scripts')#校验操作名
            return [自身._登记(脚本) for 脚本 in 结果['scripts']]#登记映射
        return 自身.路由.请求(自身.目标['source'],自身.会话id,{'op':'list-scripts'}).然后(登记目录)#响应到达后再登记

    def _登记(自身,脚本):#登记脚本
        '登记公开键'
        脚本键=自身.脚本身份.转Runtime(脚本['scriptKey'])#公开键
        描述={**脚本,'scriptKey':脚本键,'executionContextId':自身.目标['contextId']}#描述
        自身._脚本[脚本键]={'localKey':脚本['scriptKey']}#路由
        return 描述#返回

    def _路由(自身,脚本键):#解析路由
        '确保目录后取路由，返回期约，兑现值是路由记录'
        def 查路由(目录):#目录加载完成后查路由
            '按脚本键取路由，不存在则拒绝'
            路由=自身._脚本.get(脚本键)#取路由
            if 路由 is None:#不可用
                raise RuntimeError('客户端脚本已不可用')#抛错
            return 路由#返回
        return 自身.列脚本().然后(查路由)#目录加载完成后再查路由

    def _读(自身,脚本键,内容):#读内容分块
        '逐块请求直至 eof，返回期约，兑现值是解码文本，不可用时为 None'
        块列表=[]#已收到的字节块
        def 读下一块(偏移):#请求从偏移起的一块
            '请求一块，响应到达后收集并决定是否继续'
            def 处理块(结果):#块响应到达后处理
                '校验块并收集，未到 eof 就接着读下一块'
                结果=自身._期望(结果,'get-content-chunk')#校验操作名
                if not 结果.get('available'):#不可用
                    return None#无
                字节=base64.b64decode(结果['data'])#解码
                if len(字节)>自身.路由.分块字节 or 结果['nextOffset']!=偏移+len(字节) or (not 结果.get('eof') and 结果['nextOffset']==偏移) or 结果['nextOffset']>自身.路由.最大内容字节:#无效块
                    raise RuntimeError('客户端源返回了无效内容块')#无效块
                块列表.append(字节)#收集
                if 结果.get('eof'):#结束
                    return b''.join(块列表).decode('utf-8')#解码文本
                return 读下一块(结果['nextOffset'])#从新偏移继续读
            return 自身.路由.请求(自身.目标['source'],自身.会话id,{#请求块
                'op':'get-content-chunk','scriptKey':脚本键,'content':内容,#种类
                'offset':偏移,'maxBytes':自身.路由.分块字节,#上限
            }).然后(处理块)#块响应到达后再处理
        return 读下一块(0)#从偏移0开始

    def _期望(自身,结果,操作):#期望结果
        '窄化结果操作'
        if 结果.get('op')!=操作:#不符
            raise RuntimeError(f"Client source returned {结果.get('op')} for {操作}")#抛错
        return 结果#返回
