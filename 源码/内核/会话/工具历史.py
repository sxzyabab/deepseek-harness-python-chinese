"""有状态重建历史工具定义，供请求投影使用。"""
import json
from .json值 import 冻结树

__all__=['工具历史投影']

class 工具历史投影:
    """独立于模型能力折叠已提交头与开发者消息。"""
    def __init__(自身):
        """初始化空投影状态。"""
        自身._头表={}#按追加所引用的头序号索引的历史声明
        自身._已声明={}#当前声明序列中保留的定义，含已移除工具
        自身._活动=[]#最近请求头中的活动定义
        自身._可用=set()#由基线与已记录更新重建的可用名
        自身._基线序号=None#当前声明序列的起始头；首个头之前缺席
        自身._历史=冻结树({'tools':[],'updates':[]})#当前基线与已解析更新的不可变请求快照

    def 应用(自身,事件):
        """按日志顺序消费下一则已提交事件。事件含恢复期间的继承事件。"""
        if 事件['type']=='request/header':#请求头
            工具列表=事件['data']['header']['tools'] if 'tools' in 事件['data']['header'] else []#工具列表
            自身._头表[事件['seq']]=工具列表#记入头表
            # 保留名若换定义会丢掉前缀复用；未改动的恢复名由其记录的追加再次提供。
            重声明=False#是否重声明
            for 工具 in 工具列表:#扫活动工具
                先前=自身._已声明.get(工具['name'])#先前定义
                if 先前 is not None and json.dumps(先前,ensure_ascii=False,separators=(',',':'))!=json.dumps(工具,ensure_ascii=False,separators=(',',':')):#定义变了
                    重声明=True#标重声明
                    break#跳出
            数据=事件['data']#载荷
            if (自身._基线序号 is None
                or 数据.get('reason')=='series'
                or 数据.get('startsSeries') is True
                or 重声明):#新序列
                自身._基线序号=事件['seq']#更新基线
                自身._已声明={工具['name']:工具 for 工具 in 工具列表}#重置声明
                自身._历史=冻结树({'tools':list(工具列表),'updates':[]})#重置历史
                自身._可用=set(工具['name'] for 工具 in 工具列表)#重置可用
            自身._活动=工具列表#更新活动
        elif 事件['type']=='developer/message':#开发者消息
            数据=事件['data']#载荷
            消息=数据['message']#消息
            头序号=数据.get('headerSeq')#头序号
            定义列表=[] if 头序号 is None else 自身._头表.get(头序号)#头内定义
            追加列表=[]#追加工具
            for 块 in 消息['content']:#扫内容块
                if 块.get('type')!='tool-addition':#非追加
                    continue#跳过
                工具=None#候选定义
                if 定义列表 is not None:#有定义表
                    for 项 in 定义列表:#按名找
                        if 项['name']==块['toolName']:#命中
                            工具=项#收下
                            break#跳出
                if 工具 is None:#缺定义
                    raise ValueError('tool history: missing definition for '+str(块['toolName']))#缺定义
                追加列表.append(工具)#收集
            for 工具 in 追加列表:#写入声明
                自身._已声明[工具['name']]=工具#记名
            for 块 in 消息['content']:#扫内容块更新可用名
                if 块.get('type')=='tool-addition':#追加
                    自身._可用.add(块['toolName'])#加名
                elif 块.get('type')=='tool-removal':#移除
                    自身._可用.discard(块['toolName'])#删名
            自身._历史=冻结树({#追加更新记录
                'tools':list(自身._历史['tools']),#基线工具
                'updates':list(自身._历史['updates'])+[{'messageId':消息['id'],'additions':追加列表}],#更新列表
            })#冻结

    def 快照(自身):
        """读取不可变快照；后续事件不会改动它。返回当前序列的初始声明与历史上已解析的追加。"""
        # 工具更新发出前写入的会话，头与更新可能对不上。
        if len(自身._活动)!=len(自身._可用) or any(工具['name'] not in 自身._可用 for 工具 in 自身._活动):#不一致
            return 冻结树({'tools':list(自身._活动),'updates':[]})#退回活动头
        return 自身._历史#返回历史
