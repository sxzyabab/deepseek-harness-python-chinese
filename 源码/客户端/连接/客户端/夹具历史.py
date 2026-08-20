"""fx-alpha 历史脚本与消息工厂。

对齐上游 `connection/src/client/fixture.ts` 的 `buildAlphaLog` 与消息构造辅助。
公开面仅中文名；协议键保持英文。假宿主世界与接口客户端见 `夹具.py`。
"""
import json,time#参数序列化、时间戳
from .夹具样本 import (#构造甲日志用到的样本与用量
    markdown样本,用户markdown字面量,终端输出样本,搜索命中正文,搜索路径正文,
    读样本路径,读样本首行,读样本正文,夹具图像引用,夹具用量,
)#结束样本导入

__all__=[#仅历史脚本与消息工厂
    '造文本块','造用户消息','造助手消息','造工具结果消息','构造甲日志',
]#仅中文公开名结束

def 造文本块(文本):#包成文本块
    """单块纯文本内容。"""
    return [{'type':'text','text':文本}]#单元素数组

def 造用户消息(内容,来源=None):#造用户消息
    """来源默认真人用户。"""
    return {'role':'user','content':内容,'source':来源 or {'kind':'user'}}#用户消息

def 造助手消息(内容,模型='fx-1'):#造助手消息
    """假提供方 fixture。"""
    return {'role':'assistant','content':内容,'source':{'provider':'fixture','model':模型}}#助手消息

def 造工具结果消息(调用标识,内容,是否错误):#造工具结果
    """品牌化 callId 后的工具结果。"""
    return {'role':'tool','callId':调用标识,'content':内容,'isError':是否错误,'source':{'callId':调用标识}}#工具结果

def 构造甲日志():#手写 fx-alpha 历史
    """75 轮（约 150+ 条消息，PAGE_MESSAGES=50 时 4 页），混有 reasoning / 工具调用+结果 / 上下文。"""
    事件们=[]#尚未编号的事件
    时刻=[time.time()*1000-3_600_000]#从一小时前起（可变盒）

    def 推(条目):#追加一条并回 seq
        """助手消息补 usage。"""
        序号=len(事件们)#下标即 seq
        数据=条目.get('data')#可选 data
        if 条目.get('type')=='assistant/message' and isinstance(数据,dict):#助手消息要挂用量
            数据=dict(数据)#拷
            数据['usage']=夹具用量(数据.get('turn',0),数据.get('step',0))#确定性账单
            条目=dict(条目,data=数据)#覆盖
        时刻[0]+=800#每条间隔 800ms
        事件们.append({'seq':序号,'time':时刻[0],**条目})#写入
        return 序号#给标题等引用

    def 工具轮(轮次,名,参数,结果正文):#一轮用户+单次工具调用+结果
        """用户点名工具。"""
        调用标识=f'fx-call-{轮次}'#按轮次稳定
        推({'type':'turn/start','data':{'turn':轮次}})#开轮
        推({'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块(f'问题 {轮次}：{名} 样本。'))})#用户
        推({'type':'step/start','data':{'turn':轮次,'step':0}})#开步
        推({'type':'assistant/message','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造助手消息([{'type':'tool-call','id':调用标识,'name':名,'arguments':参数}])}})#助手
        推({'type':'tool/call','data':{'turn':轮次,'step':0,'callId':调用标识,'name':名,'arguments':参数}})#调用
        推({'type':'tool/result','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造工具结果消息(调用标识,造文本块(结果正文),False)}})#成功结果
        推({'type':'step/end','data':{'turn':轮次,'step':0}})#收步
        推({'type':'turn/end','data':{'turn':轮次,'reason':{'kind':'completed'}}})#收轮

    #常驻历史代表已完成的模型请求，因此保留当时的路由容量，与直播 prompt 路径一致。
    推({'type':'request/context','data':{'provider':'deepseek-official','model':'deepseek-v4-flash','contextWindow':128_000}})#请求上下文
    for 轮次 in range(60):#前 60 轮批量历史
        推({'type':'turn/start','data':{'turn':轮次}})#开轮
        用户序号=推({'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块(用户markdown字面量 if 轮次==59 else f'问题 {轮次}：fixture 历史消息，用于翻页与渲染验收。'))})#用户
        if 轮次==0:#首轮落标题
            推({'type':'session/title','data':{'title':'Fixture 历史会话','messageSeqs':[用户序号],'source':{'kind':'fallback'}}})#标题
        if 轮次%9==4:#每隔若干轮插插件上下文
            推({'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块(f'[fixture] 上下文注入（turn {轮次}）'),{'kind':'plugin','plugin':'fixture'})})#插件来源
        推({'type':'step/start','data':{'turn':轮次,'step':0}})#开步
        带工具=轮次%5==2#每五轮一次工具
        带思考=轮次%3==1#每三轮一次思考
        块们=[]#本步助手块
        if 带思考:#可折叠思考
            块们.append({'type':'reasoning','text':f'思考过程 {轮次}：这是一段可折叠的 reasoning 内容。'})#思考
        块们.append({'type':'text','text':markdown样本 if 轮次==59 else f'回答 {轮次}：这是 fixture 生成的历史回复正文。'})#正文
        if 带工具:#工具轮：调用 + 结果 + 第二步消化
            调用标识=f'fx-call-{轮次}'#稳定调用 id
            块们.append({'type':'tool-call','id':调用标识,'name':'echo','arguments':f'{{"text":"turn {轮次}"}}'})#echo 无展示器
            推({'type':'assistant/message','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造助手消息(块们)}})#带工具
            推({'type':'tool/call','data':{'turn':轮次,'step':0,'callId':调用标识,'name':'echo','arguments':f'{{"text":"turn {轮次}"}}'}})#调用事件
            推({'type':'tool/result','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造工具结果消息(调用标识,造文本块(f'ECHO: TURN {轮次}'),轮次%25==12)}})#偶发错误
            推({'type':'step/end','data':{'turn':轮次,'step':0}})#第一步结束
            推({'type':'step/start','data':{'turn':轮次,'step':1}})#消化步
            推({'type':'assistant/message','surfaceOp':'append','data':{'turn':轮次,'step':1,'message':造助手消息(造文本块(f'工具结果已消化（turn {轮次}）。'))}})#消化
            推({'type':'step/end','data':{'turn':轮次,'step':1}})#第二步结束
        else:#纯文本轮
            推({'type':'assistant/message','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造助手消息(块们)}})#助手
            推({'type':'step/end','data':{'turn':轮次,'step':0}})#一步结束
        推({'type':'turn/end','data':{'turn':轮次,'reason':{'kind':'completed'}}})#正常完成

    #三轮视图样本（60–62）覆盖内建卡片；62–63 真文件系统名练专用 generic 行。
    工具轮(60,'fx-bash','{"command":"ls -la\\necho done","cwd":"/tmp/fixture"}','total 2\ndrwxr-xr-x fixture\n-rw-r--r-- demo.txt')#终端回退行
    工具轮(61,'fx-write','{"path":"notes/demo.txt","content":"hello fixture\\n"}','wrote notes/demo.txt')#写卡
    工具轮(62,'edit','{"file_path":"notes/demo.txt","old_string":"hello","new_string":"hello fixture"}','已编辑')#单 hunk
    工具轮(63,'write','{"file_path":"notes/new-demo.txt","content":"hello fixture\\n"}','已写入')#keyed write
    工具轮(64,'edit','{"file_path":"src/config.ts","old_string":"const timeout = 30","new_string":"const timeout = 60"}','已编辑')#双 hunk
    #第 65 轮：一次 run_code，三条已记录的子派发——Code Mode 验收面。
    轮次=65#run_code 样本轮
    调用标识=f'fx-call-{轮次}'#根调用 id
    程序='const listing = await tools.bash({ command: "ls notes", description: "List notes" })\n'+'const demo = await tools.read({ file_path: "notes/demo.txt" })\n'+'await tools.read({ file_path: "notes/missing.txt" }).catch(() => "tolerated")\n'+'return { listing, demo }'#子派发
    参数=json.dumps({'code':程序,'description':'Read the notes files and summarize'},ensure_ascii=False)#run_code 参数
    推({'type':'turn/start','data':{'turn':轮次}})#开轮
    推({'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块(f'问题 {轮次}：run_code 样本。'))})#用户
    推({'type':'step/start','data':{'turn':轮次,'step':0}})#开步
    推({'type':'assistant/message','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造助手消息([{'type':'tool-call','id':调用标识,'name':'run_code','arguments':参数}])}})#助手
    推({'type':'tool/call','data':{'turn':轮次,'step':0,'callId':调用标识,'name':'run_code','arguments':参数}})#根调用
    def 派发对(号,名,派发参数,结果正文,是否错误=False):#一对 start+完成
        """子派发开始与完成。"""
        推({'type':'tool/code-dispatch-start','data':{'rootCallId':调用标识,'parentCallId':调用标识,'subCallId':f'{调用标识}:code:{号}','name':名,'arguments':派发参数}})#start
        推({'type':'tool/code-dispatch','data':{'rootCallId':调用标识,'parentCallId':调用标识,'subCallId':f'{调用标识}:code:{号}','name':名,'arguments':派发参数,'isError':是否错误,'content':[{'type':'text','text':结果正文}]}})#完成
    派发对(1,'bash',{'command':'ls notes','description':'List notes'},'demo.txt\nnew-demo.txt')#bash
    派发对(2,'read',{'file_path':'notes/demo.txt'},'hello fixture\n')#成功 read
    派发对(3,'read',{'file_path':'notes/missing.txt'},'Error: ENOENT: notes/missing.txt not found',True)#错误 read
    推({'type':'tool/result','surfaceOp':'append','data':{'turn':轮次,'step':0,'message':造工具结果消息(调用标识,造文本块('{"listing":"demo.txt\\nnew-demo.txt","demo":"hello fixture\\n"}'),False)}})#根结果
    推({'type':'step/end','data':{'turn':轮次,'step':0}})#收步
    推({'type':'turn/end','data':{'turn':轮次,'reason':{'kind':'completed'}}})#收轮
    夹具待办=[#四项待办；两项 in_progress：并行策略
        {'content':'梳理需求','status':'completed'},{'content':'实现 fixture 样本','status':'in_progress'},
        {'content':'跑后台构建','status':'in_progress'},{'content':'浏览器验收','status':'pending'},
    ]#结束夹具待办
    #故意排在 todo 轮之前：站立计划在下一次 turn/start 退役。
    工具轮(66,'bash','{"command":"pnpm run check","cwd":"/tmp/fixture/deep/nested"}',终端输出样本)#keyed 终端行
    工具轮(67,'grep','{"pattern":"SEARCH_MAX_LINES","path":"packages/client"}',搜索命中正文)#命中形态
    工具轮(68,'glob','{"pattern":"**/SearchBlock*","path":"packages/client"}',搜索路径正文)#路径形态
    工具轮(69,'read',json.dumps({'file_path':读样本路径,'offset':读样本首行},ensure_ascii=False),读样本正文)#读卡
    工具轮(70,'web_search','{"query":"deepseek harness architecture"}','Search results for deepseek harness architecture.')#搜索卡
    工具轮(71,'web_fetch','{"url":"https://www.deepseek.com/blog/harness-architecture"}','# Harness architecture\n\nEverything is a plugin.')#抓取卡
    #第 72 轮：max-tokens 样本——句中结束，必须画出 turn-max-tokens 提示。
    推({'type':'turn/start','data':{'turn':72}})#开轮
    推({'type':'user/message','surfaceOp':'append','data':造用户消息(造文本块('问题 72：请完整列出全部一百条条目。'))})#用户
    推({'type':'step/start','data':{'turn':72,'step':0}})#开步
    推({'type':'assistant/message','surfaceOp':'append','data':{'turn':72,'step':0,'message':造助手消息(造文本块('条目 1：第一条。条目 2：第二条。条目 3：这一条写到一半被'))}})#句中截断
    推({'type':'step/end','data':{'turn':72,'step':0}})#收步
    推({'type':'turn/end','data':{'turn':72,'reason':{'kind':'max-tokens'}}})#输出帽结束
    #第 73 轮：用户与助手图片共用同一持久 fixture 对象。
    推({'type':'turn/start','data':{'turn':73}})#开轮
    推({'type':'user/message','surfaceOp':'append','data':造用户消息([{'type':'image','attachment':夹具图像引用},*造文本块('历史用户图片')])})#用户图片
    推({'type':'step/start','data':{'turn':73,'step':0}})#开步
    推({'type':'assistant/message','surfaceOp':'append','data':{'turn':73,'step':0,'message':造助手消息([*造文本块('结构化模型图片：'),{'type':'image','attachment':夹具图像引用}],'fx-vision')}})#助手图片
    推({'type':'step/end','data':{'turn':73,'step':0}})#收步
    推({'type':'turn/end','data':{'turn':73,'reason':{'kind':'completed'}}})#收轮
    待办参数=json.dumps({'todos':夹具待办},ensure_ascii=False)#todo_write 参数
    工具轮(74,'todo_write',待办参数,'Updated todo list: 1 pending, 2 in progress, 1 completed.')#最后一轮：站立计划
    #真工具在执行中途追加快照——夹在 tool/call 与 tool/result 之间。
    调用下标=len(事件们)-4#tool/call 下标
    调用时刻=事件们[调用下标].get('time',时刻[0])#调用时刻
    事件们.insert(调用下标+1,{'type':'todo/write','time':调用时刻+400,'data':{'todos':夹具待办}})#插到 call 与 result 之间
    for 下标,条目 in enumerate(事件们):#splice 后重编号
        条目['seq']=下标#重编号
    return 事件们#交给会话事件
