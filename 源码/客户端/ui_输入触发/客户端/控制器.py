'一场会话的触发管线。菜单归约和触发检测只在这里用一次，所以写在这里'
from ...模块.客户端.通告 import 取握手窗口
import re
import unicodedata
from ....上下文.文件引用.词法 import 光标处活动令牌#光标处的 @ 令牌
from ...存储 import 创建快照存储#快照仓
from ..内核.菜单归约 import 菜单关闭,铺分组,源字段#初态、铺组和源字段

__all__=['触发控制器']

def 等返回(值):
    '上游 await 的同步等待。对象带等待方法就等它交回结果'
    等待=getattr(值,'等待',None)#可能是带等待的结果
    if callable(等待):#要等
        return 等待()#交回结果
    return 值#已经是结果

def 是空白(字符):
    'Unicode 空白，含换行'
    return 字符.isspace()#空白

def 收成关闭(状态):
    '关上菜单，世代留着，好让还在飞的结算可以丢掉'
    if 状态['open'] or 状态['hit'] is not None or len(状态['groups'])>0 or 状态['highlight'] is not None:#还有残留
        return {'open':False,'hit':None,'generation':状态['generation'],'groups':[],'highlight':None}#关上
    return 状态#本来就是关的，留同一份

def 首个高亮(组列表):
    '第一个非空就绪组的第一项，否则 None'
    for 组 in 组列表:#组顺序
        if 组['status']=='ready' and len(组['items'])>0:#有就绪行
            return {'source':组['source'],'index':0}#第一项
    return None#没有

def 仍有效高亮(高亮,组列表):
    '高亮仍指向就绪项时原样返回，否则 None'
    if 高亮 is None:#没有高亮
        return None#没有
    组=None#它所在的组
    for 项 in 组列表:#找组
        if 项['source']==高亮['source']:#这个源
            组=项#记下
            break#找到了
    if 组 is not None and 组['status']=='ready' and 高亮['index']<len(组['items']):#还指着一行
        return 高亮#原样
    return None#指空了

def 各组就绪且空(组列表):
    '每一组都就绪且没有候选项。空名册也算'
    for 组 in 组列表:#逐组
        if 组['status']!='ready' or len(组['items'])!=0:#还在等，或还有行
            return False#不关
    return True#可以自己关上

class 拉取信号:
    '一次候选拉取的取消通道'
    def __init__(自身):
        '还没取消'
        自身.aborted=False#未取消
        自身.reason=None#取消原因

    def is_set(自身):
        '和 aborted 是同一件事。技能源用线程事件的这个方法看取消'
        return 自身.aborted#是否已取消

class 拉取控制器:
    '发出取消的控制器'
    def __init__(自身):
        '配上信号'
        自身.signal=拉取信号()#配套信号

    def abort(自身):
        '取消这一轮拉取'
        if 自身.signal.aborted:#已经取消
            return#不用再写
        自身.signal.aborted=True#标记
        自身.signal.reason=Exception('The operation was aborted')#原因

class 触发控制器:
    '一场会话的命中、菜单、候选拉取和点选。MenuView 读 menu，点选走 pick'
    def __init__(自身,依赖):
        '作用域诞生时预热当时的名册，并订上词表'
        自身.依赖=依赖#作用域、会话号、名册
        自身.menu=创建快照存储(菜单关闭)#菜单仓
        自身.launcher=创建快照存储(None)#启动器打开的源名
        自身.headers=创建快照存储({})#各源面包屑
        自身.lexicon=创建快照存储({})#按触发字符合并的热词
        自身.命中=None#当前权威命中
        自身.已驳回=None#用户刚刚驳回的那一个词
        自身.已钻=False#这次菜单是下钻打开的
        自身.拉取=None#当前这一轮候选拉取
        自身.已拆除=False#作用域已经拆掉
        自身.词表拆除={}#源身份到退订
        投影=自身.投影()#这场会话的身份
        for 源 in 依赖['roster']['all']():#诞生时名册上的源
            预热=源字段(源,'warm')#可选预热
            if 预热 is not None:#有预热
                预热(投影)#拉一次背后的数据
            自身.盯词表(源,投影)#词表变了就刷新
        自身.刷新词表()#先发一版

    def track(自身,草稿,光标,守卫,草稿修订):
        '用草稿和光标检测触发，再驱动菜单'
        if 自身.已拆除:#已经拆掉
            return#不再跟踪
        启动中=自身.launcher.getSnapshot() is not None#这一拍之前是启动器打开的
        自身.清启动器()#跟踪接手之后启动器标记清掉
        原始=None#光标下没有活触发
        if 守卫['tier']!='frozen':#冻结时 / 和 @ 都不活
            艾特=光标处活动令牌(草稿,光标)#@ 可以是未闭合的引号路径
            if 艾特 is not None:#光标在 @ 令牌里
                起点=光标-len(艾特['prefix'])#令牌起点
                非空白=re.search(r'\S',草稿)#草稿里第一个非空白
                首个=-1 if 非空白 is None else 非空白.start()#没有则对不上起点
                原始={#@ 命中
                    'trigger':'@',#触发字符
                    'query':艾特['query'],#@ 后面的查询
                    'quoted':艾特['quoted'],#是否开着引号
                    'position':'leading' if 首个==起点 else 'inline',#是不是整段草稿的开头
                    'span':{'start':起点,'end':光标,'draftRev':0},#修订先占 0
                }
            else:#再向左找 /
                下标=光标-1#从光标左边开始
                while 下标>=0:#还没走出草稿
                    字符=草稿[下标]#这一格
                    if 是空白(字符):#碰到空白，这一段没有斜杠触发
                        break#停
                    if 字符!='/' or 守卫['tier']=='claimed':#不是斜杠，或斜杠这一档被压住
                        下标-=1#继续向左
                        continue#下一格
                    可开=False#这一处斜杠能不能当触发
                    if 下标==0:#草稿开头
                        可开=True#可以
                    else:#看前一个字符
                        前一字=草稿[下标-1]#前一格
                        if 是空白(前一字):#空白之后
                            可开=True#可以
                        elif 前一字=='_' or unicodedata.category(前一字).startswith('L') or unicodedata.category(前一字).startswith('N'):#词字符之后
                            可开=False#不当触发
                        elif 前一字=='/':#连续斜杠，URL 的第二条
                            可开=False#不当触发
                        elif 前一字==':' and 下标>=2 and 是空白(草稿[下标-2]) is False:#方案名后面的斜杠
                            可开=False#不当触发
                        else:#标点之后
                            可开=True#可以
                    if 可开 is not True:#这一个斜杠只是词里的字符
                        下标-=1#继续向左
                        continue#再找
                    非空白=re.search(r'\S',草稿)#第一个非空白
                    首个=-1 if 非空白 is None else 非空白.start()#没有则对不上
                    原始={#斜杠命中
                        'trigger':'/',#触发字符
                        'query':草稿[下标+1:光标],#斜杠到光标
                        'quoted':False,#斜杠没有引号路径
                        'position':'leading' if 首个==下标 else 'inline',#是不是整段开头
                        'span':{'start':下标,'end':光标,'draftRev':0},#修订先占 0
                    }
                    break#找到了
        if 原始 is None:#没有活触发
            if 启动中:#启动器刚打开，这一拍空跟踪不能把它关上
                return#只放过这一拍
            自身.命中=None#权威命中清掉
            if 守卫['tier']!='frozen':#冻结是提交自己的记账，不能把驳回解除
                自身.已驳回=None#换了意图
            自身.停拉取()#停掉候选
            自身.归约({'type':'close'})#关上
            return#结束
        跨度=dict(原始['span'])#抄跨度
        跨度['draftRev']=草稿修订#盖上这一次修订
        命中=dict(原始)#抄命中
        命中['span']=跨度#带修订的跨度
        if 启动中:#启动器是新的一次意图
            自身.已驳回=None#早先的驳回不能压住它
        if 自身.已驳回 is not None:#可能还是刚才驳回的那个词
            驳回=自身.已驳回#记下的身份
            同一=(驳回['trigger']==命中['trigger'] and 驳回['query']==命中['query'] and 驳回['quoted']==命中['quoted'] and 驳回['start']==命中['span']['start'] and 驳回['end']==命中['span']['end'])#同一个词、同一段查询
            if 同一 is not True:#已经换成别的词
                自身.已驳回=None#解除
            else:#还是那一个
                自身.命中=命中#跨度可以更新，菜单保持关闭
                return#不再打开
        前=自身.menu.getSnapshot()#上一份菜单
        相同=启动中 is not True and 前['open'] is True and 前['hit'] is not None and 前['hit']['trigger']==命中['trigger'] and 前['hit']['query']==命中['query'] and 前['hit']['quoted']==命中['quoted'] and 前['hit']['span']['start']==命中['span']['start'] and 前['hit']['span']['end']==命中['span']['end']#查询和跨度都没变
        自身.命中=命中#权威命中换成这一次
        if 相同:#菜单已经对着这个词
            return#不用重拉
        名册=自身.依赖['roster']['sources'](命中['trigger'])#这个字符的源
        if len(名册)==0:#没有源
            自身.停拉取()#停掉
            自身.归约({'type':'close'})#关上
            return#结束
        if 启动中 or 前['open'] is not True or 前['hit'] is None or 前['hit']['trigger']!=命中['trigger']:#新开，或换成另一个触发字符
            自身.menu.set(铺分组(自身.menu.getSnapshot(),名册))#先铺等待中的名册
        自身.归约({'type':'hit','hit':命中})#打开新世代
        自身.刷新页眉(命中,名册)#页眉跟这一次查询
        自身.拉候选(命中,名册)#拉候选

    def toggleSource(自身,源名,命中):
        '只打开一个已登记的源。再点同一个源就关掉'
        if 自身.已拆除:#已经拆掉
            return#不再切换
        if 自身.launcher.getSnapshot()==源名 and 自身.menu.getSnapshot()['open'] is True:#同一个源已经开着
            自身.dismiss()#关掉
            return#结束
        匹配=None#名册里的这个源
        for 项 in 自身.依赖['roster']['sources'](命中['trigger']):#这个字符的源
            if 源字段(项,'name')==源名:#名字对上
                匹配=项#记下
                break#找到了
        if 匹配 is None:#没有这个源
            自身.dismiss()#关掉残留
            return#结束
        自身.停拉取()#停掉上一轮
        自身.命中=命中#用调用方给的合成命中
        自身.launcher.set(源名)#记下是启动器打开的
        自身.menu.set(铺分组(自身.menu.getSnapshot(),[匹配]))#只铺这一组
        自身.归约({'type':'hit','hit':命中})#打开
        自身.刷新页眉(命中,[匹配])#只要这一源的页眉
        自身.拉候选(命中,[匹配])#只拉这一源

    def pick(自身,源名,下标,动作='pick'):
        '把点中的候选交给源，再执行认领或插入'
        态=自身.menu.getSnapshot()#当前菜单
        命中=自身.命中#权威命中
        if 自身.已拆除 or 态['open'] is not True or 命中 is None:#关着或已拆
            return#不点
        组=None#这一组
        for 项 in 态['groups']:#找组
            if 项['source']==源名:#这个源
                组=项#记下
                break#找到了
        候选=None#点中的行
        if 组 is not None and 组['status']=='ready' and 0<=下标<len(组['items']):#就绪且下标还在
            候选=组['items'][下标]#这一行
        if 候选 is None:#没有可点的行
            return#停
        源=None#拥有这组的源
        for 项 in 自身.依赖['roster']['sources'](命中['trigger']):#这个字符的源
            if 源字段(项,'name')==源名:#名字对上
                源=项#记下
                break#找到了
        if 源 is None:#源已经不在
            return#停
        自身.落定(源,候选,命中,动作)#走点选

    def pickCrumb(自身,源名,下标):
        '点页眉上的一节，走和下钻同一条结果'
        命中=自身.命中#权威命中
        if 自身.已拆除 or 自身.menu.getSnapshot()['open'] is not True or 命中 is None:#关着
            return#不点
        屑列=自身.headers.getSnapshot().get(源名)#这一源的面包屑
        屑=None#点中的那一节
        if 屑列 is not None and 0<=下标<len(屑列):#下标还在
            屑=屑列[下标]#这一节
        if 屑 is None or 屑.get('current') is True:#没有，或已经是当前这一节
            return#不点
        源=None#拥有这组的源
        for 项 in 自身.依赖['roster']['sources'](命中['trigger']):#这个字符的源
            if 源字段(项,'name')==源名:#名字对上
                源=项#记下
                break#找到了
        if 源 is None:#源不在
            return#停
        自身.落定(源,{'name':屑['label'],'value':屑['value']},命中,'drill')#当成下钻

    def hover(自身,源名,下标):
        '把共享高亮停在指针下的这一行'
        if 自身.已拆除:#已拆
            return#不移
        自身.归约({'type':'hover','source':源名,'index':下标})#停高亮

    def arbitrate(自身,键,合成中):
        '菜单打开时裁决按键。pass、consumed 或 pick-highlighted'
        if 合成中 or 自身.已拆除:#输入法组合中，或已拆
            return 'pass'#交给浏览器
        态=自身.menu.getSnapshot()#当前菜单
        if 态['open'] is not True:#没开
            return 'pass'#交给浏览器
        if 键=='up':#向上
            自身.归约({'type':'move','dir':-1})#高亮上移
            return 'consumed'#菜单吃掉
        if 键=='down':#向下
            自身.归约({'type':'move','dir':1})#高亮下移
            return 'consumed'#菜单吃掉
        if 键=='escape' or 键=='tabBack':#离开，不落定候选
            自身.记下驳回()#这个词先别再打开
            自身.停拉取()#停掉
            自身.归约({'type':'close'})#关上
            return 'consumed'#菜单吃掉
        if 键=='enter':#回车
            if 态['highlight'] is None:#没有高亮
                return 'pass'#交给浏览器
            组=None#高亮所在组
            for 项 in 态['groups']:#找组
                if 项['source']==态['highlight']['source']:#这个源
                    组=项#记下
                    break#找到了
            if 组 is None or 组['status']!='ready':#还在等，不点旧行，也不提交
                return 'consumed'#吃掉这一下
            自身.pick(态['highlight']['source'],态['highlight']['index'])#落定
            return 'pick-highlighted'#高亮已落定
        if 键=='tab':#Tab
            if 态['highlight'] is None:#没有高亮
                return 'pass'#交给浏览器
            组=None#高亮所在组
            for 项 in 态['groups']:#找组
                if 项['source']==态['highlight']['source']:#这个源
                    组=项#记下
                    break#找到了
            if 组 is None or 组['status']!='ready':#还在等
                return 'consumed'#吃掉，不把焦点移走
            行=None#高亮行
            if 0<=态['highlight']['index']<len(组['items']):#下标还在
                行=组['items'][态['highlight']['index']]#这一行
            if 行 is None:#行没了
                return 'pass'#交给浏览器
            if 行.get('drill') is True:#这一行可以下钻
                自身.pick(态['highlight']['source'],态['highlight']['index'],'drill')#下钻
                return 'consumed'#菜单还开着
            自身.pick(态['highlight']['source'],态['highlight']['index'])#普通落定
            return 'pick-highlighted'#高亮已落定
        return 'pass'#不认识的键交给浏览器

    def onSpace(自身):
        '空格时问各个源。输入真的应用了认领或插入才返回 True'
        命中=自身.命中#权威命中
        if 自身.已拆除 or 命中 is None or 命中['position']!='leading':#不是行首词
            return False#不吃空格
        令牌=命中['trigger']+命中['query']#刚完成的词
        投影=自身.投影()#会话身份
        for 源 in 自身.依赖['roster']['sources'](命中['trigger']):#登记顺序
            匹配=源字段(源,'matchSpace')#可选的空格裁决
            if 匹配 is None:#不参加
                continue#下一个
            结果=匹配(投影,令牌)#同步问热状态
            if 结果 is None:#这一源不认
                continue#下一个
            if 结果=='handled':#源自己处理完了
                return True#调用方要阻止默认
            return 自身.执行(结果,命中['span'])#应用认领或插入
        return False#没有源认领

    def serializeReference(自身,源名,引用,信号):
        '把一处引用交给拥有源的编解码。没有编解码就抛出'
        拥有=None#拥有这个名字的源
        for 源 in 自身.依赖['roster']['all']():#全部源
            if 源字段(源,'name')==源名:#名字对上
                拥有=源#记下
                break#找到了
        编解码=None if 拥有 is None else 源字段(拥有,'codec')#编解码
        if 编解码 is None:#没有
            raise Exception('slash: no serializer for reference source "'+源名+'"')#不能降成剪贴板文本
        序列化=编解码['serialize'] if isinstance(编解码,dict) else 编解码.serialize#序列化函数
        return 等返回(序列化(引用,信号))#模型文本

    def openReference(自身,源名,引用):
        '把芯片交给拥有源，或把可编辑词交给当前词表里的源'
        if 自身.已拆除:#已拆
            return False#不打开
        会话=自身.投影()#会话身份
        for 拥有 in 自身.依赖['roster']['all']():#全部源
            if 源名 is None:#可编辑文本
                原文=引用['ref']#带触发字符的文本
                触发符=源字段(拥有,'trigger')#源的字符
                词表=源字段(拥有,'lexicon')#热词
                名字=None#还没问
                if isinstance(触发符,str) and 原文.startswith(触发符) and 词表 is not None:#前缀对上，并且源有词表
                    名字=词表(会话)#当前热词
                匹配=名字 is not None and 原文[1:] in 名字#去掉触发字符后在词表里
            else:#芯片已经带着源名
                匹配=源字段(拥有,'name')==源名#就是这个源
            打开=源字段(拥有,'openReference')#可选预览
            if 匹配 and 打开 is not None and 打开(会话,引用):#这个源接下了
                自身.dismiss()#关掉菜单
                return True#已打开
        return False#没有源接

    def adjudicate(自身,行,信号,信封):
        '回车时按登记顺序问 matchEnter。第一个有结果的赢'
        投影=自身.投影()#会话身份
        for 源 in 自身.依赖['roster']['all']():#登记顺序
            if 信号.aborted:#这次提交已经取消
                原因=信号.reason#取消原因
                if isinstance(原因,BaseException):#已经是异常
                    raise 原因#原样
                raise Exception('slash adjudication aborted')#否则收成这句
            匹配=源字段(源,'matchEnter')#可选的回车裁决
            触发符=源字段(源,'trigger')#源的字符
            if 匹配 is None or not isinstance(触发符,str) or 行.startswith(触发符) is not True:#不参加，或行首不是它的字符
                continue#下一个
            结果=等返回(匹配(投影,行,信号,信封))#可以等它自己的预热
            if 结果 is not None:#这一源认了
                return 结果#它赢
        return None#没有源认，走默认

    def resolveClaim(自身,令牌,信号):
        '按登记顺序问 matchClaim。只回答认领，不执行'
        投影=自身.投影()#会话身份
        for 源 in 自身.依赖['roster']['all']():#登记顺序
            if 信号.aborted:#恢复已经取消
                原因=信号.reason#取消原因
                if isinstance(原因,BaseException):#已经是异常
                    raise 原因#原样
                raise Exception('command restore aborted')#否则收成这句
            匹配=源字段(源,'matchClaim')#可选的认领恢复
            触发符=源字段(源,'trigger')#源的字符
            if 匹配 is None or not isinstance(触发符,str) or 令牌.startswith(触发符) is not True:#不参加，或令牌不是它的
                continue#下一个
            认领=等返回(匹配(投影,令牌,信号))#等它自己的预热
            if 认领 is not None:#这一源认
                return 认领#它赢
        return None#没有源认这个令牌

    def sourceRemoved(自身,源):
        '源拆掉时丢掉它的菜单组，并把它从词表里拿掉'
        态=自身.menu.getSnapshot()#当前菜单
        if 态['open'] is True and 态['hit'] is not None and 态['hit']['trigger']==源字段(源,'trigger'):#正开着这个字符
            自身.归约({'type':'source-failed','generation':态['generation'],'source':源字段(源,'name')})#摘掉这一组
        键=id(源)#源的身份
        退订=自身.词表拆除.get(键)#它的退订
        if 退订 is not None:#订过
            退订()#卸掉
            del 自身.词表拆除[键]#忘掉
        自身.刷新词表()#重发词表

    def sourceAdded(自身,源):
        '晚登记的源也要预热，并折进当前词表'
        投影=自身.投影()#会话身份
        预热=源字段(源,'warm')#可选预热
        if 预热 is not None:#有
            预热(投影)#预热
        自身.盯词表(源,投影)#订词表
        自身.刷新词表()#重发

    def dismiss(自身):
        '从外面关掉菜单，例如指针点在编写区外'
        if 自身.已拆除:#已拆
            return#不用关
        自身.记下驳回()#这个词先别再打开
        自身.停拉取()#停掉
        自身.归约({'type':'close'})#关上

    def refreshOpenMenu(自身):
        '不改命中和可见行，把当前开着的菜单再拉一次'
        if 自身.已拆除 or 自身.menu.getSnapshot()['open'] is not True or 自身.命中 is None:#没开
            return#不拉
        启动=自身.launcher.getSnapshot()#启动器源名
        名册=[]#要拉的源
        for 源 in 自身.依赖['roster']['sources'](自身.命中['trigger']):#这个字符的源
            if 启动 is None or 源字段(源,'name')==启动:#全部，或只要启动器那一个
                名册.append(源)#留下
        if len(名册)==0:#没有
            return#不拉
        自身.拉候选(自身.命中,名册)#再拉

    def dispose(自身):
        '作用域拆掉时关上并停掉拉取'
        自身.已拆除=True#标记
        自身.停拉取()#停掉
        自身.归约({'type':'close'})#关上
        自身.命中=None#清掉命中
        for 退订 in list(自身.词表拆除.values()):#每个词表退订
            退订()#卸掉
        自身.词表拆除.clear()#清空

    def 投影(自身):
        '交给源的会话身份。这一场作用域里不变'
        return {'sessionId':自身.依赖['sessionId']}#只有会话号

    def 执行(自身,结果,跨度):
        '经作用域上的斜杠输入事件应用结果。输入真的写下了才是 True'
        作用域=自身.依赖['actx']#这场会话的上下文
        if 结果 is None or 结果=='handled':#没有要写的，或源已经自己处理
            return False#输入没写
        if isinstance(结果,dict) and 'claim' in 结果:#开始命令
            return 作用域.首个结果(作用域,'slash/input-begin-command',{'claim':结果['claim'],'span':跨度}) is True#写成命令
        if isinstance(结果,dict) and 'text' in 结果:#插入文本
            载荷={'text':结果['text'],'span':跨度}#文本和跨度
            if 结果.get('continue') is True:#还要继续编辑
                载荷['continue']=True#带上
            return 作用域.首个结果(作用域,'slash/input-insert-text',载荷) is True#写入
        return 作用域.首个结果(作用域,'slash/input-insert-reference',{'reference':结果['insert'],'span':跨度}) is True#插入引用

    def 刷新词表(自身):
        '重新问每个有词表的源，按触发字符合并后发布'
        投影=自身.投影()#会话身份
        卷={}#触发字符到名字列表
        for 源 in 自身.依赖['roster']['all']():#登记顺序
            取词=源字段(源,'lexicon')#词表函数
            if 取词 is None:#不参加
                continue#下一个
            try:#一个源失败不能挡住其余
                名字=取词(投影)#当前热词
            except Exception as 错误:#源自己抛了
                取握手窗口().console.error('[ui-input-trigger] source "'+str(源字段(源,'name'))+'" lexicon failed:',错误)#留下
                continue#丢掉这一源
            if 名字 is None:#还没热
                continue#不装饰
            触发符=源字段(源,'trigger')#它的字符
            已有=卷.get(触发符)#同一字符上已经有的
            if 已有 is None:#第一个
                卷[触发符]=list(名字)#这一份
            else:#后面的接上
                卷[触发符]=list(已有)+list(名字)#登记顺序拼接
        自身.lexicon.set(卷)#发布

    def 盯词表(自身,源,投影):
        '把这一源的词表失效接到刷新上。没有钩子的源不订'
        if 源字段(源,'lexicon') is None or 源字段(源,'subscribeLexicon') is None:#不通知
            return#不订
        def 失效():
            '词表变了就重发。开着的菜单等这一轮通知都走完再拉'
            自身.刷新词表()#先重发
            命中=自身.命中#失效当时的命中
            if 命中 is None or 自身.menu.getSnapshot()['open'] is not True or 命中['trigger']!=源字段(源,'trigger'):#菜单没开着这个字符
                return#不重拉
            def 稍后():
                '等同一轮失效都处理完，再按当时的名册重拉'
                if 自身.已拆除 or 自身.命中 is not 命中 or 自身.menu.getSnapshot()['open'] is not True:#已经换了或关上了
                    return#不拉
                自身.拉候选(命中,自身.依赖['roster']['sources'](命中['trigger']))#重拉
            取握手窗口().queueMicrotask(稍后)#排到这一轮之后
        自身.词表拆除[id(源)]=源字段(源,'subscribeLexicon')(投影,失效)#记下退订

    def 拉候选(自身,命中,名册):
        '按这一代命中拉候选。新的一轮先停掉上一轮'
        自身.停拉取()#停掉上一轮
        控制器=拉取控制器()#这一轮的取消
        自身.拉取=控制器#记下
        世代=自身.menu.getSnapshot()['generation']#必须对上这一代
        投影=自身.投影()#会话身份
        for 源 in 名册:#按菜单顺序，一个个等
            取候选=源字段(源,'candidates')#候选函数
            try:#失败就摘掉这一组
                项=等返回(取候选(投影,{#请求
                    'query':命中['query'],#查询
                    'quoted':命中['quoted'],#引号路径
                    'position':命中['position'],#位置
                    'drilled':自身.已钻,#是否下钻来的
                    'signal':控制器.signal,#取消通道
                }))
            except Exception as 错误:#源失败
                if 控制器.signal.aborted:#已经被换掉
                    continue#不记
                取握手窗口().console.error('[ui-input-trigger] source "'+str(源字段(源,'name'))+'" candidates failed:',错误)#留下
                自身.归约({'type':'source-failed','generation':世代,'source':源字段(源,'name')})#摘掉
                continue#下一个源
            if 控制器.signal.aborted:#等完时已经作废
                continue#不写
            自身.归约({'type':'source-settled','generation':世代,'source':源字段(源,'name'),'items':项})#写成就绪

    def 停拉取(自身):
        '有正在拉的候选就取消'
        if 自身.拉取 is not None:#有一轮
            自身.拉取.abort()#取消
            自身.拉取=None#忘掉

    def 落定(自身,源,候选,命中,动作):
        '把候选或面包屑交给源。下钻是唯一还让菜单开着的点选'
        选定=源字段(源,'onPick')#点选回调
        结果=选定({#交给源的材料
            'candidate':候选,#候选或面包屑投影
            'session':自身.投影(),#会话身份
            'position':命中['position'],#位置
            'via':'menu',#从菜单点的
            'action':动作,#落定或下钻
            'span':命中['span'],#跨度
        })
        自身.停拉取()#停掉候选
        if 动作=='pick':#落定是对这个词的决定
            自身.记下驳回()#先别再打开
        自身.归约({'type':'close'})#先关上，归约自己的清理不能清掉下面的下钻标记
        自身.已钻=动作=='drill'#下钻才记。同步的编辑可能马上再进 track
        if 自身.执行(结果,命中['span']) is not True:#编辑被拒绝，草稿没变
            自身.已钻=False#不能让页眉停在没下去的目录上

    def 刷新页眉(自身,命中,名册):
        '重新问名册里有页眉的源，再发布面包屑'
        投影=自身.投影()#会话身份
        屑表={}#源名到面包屑
        for 源 in 名册:#这一次的名册
            取页眉=源字段(源,'header')#可选页眉
            if 取页眉 is None:#不参加
                continue#下一个
            try:#页眉失败不能把菜单打掉
                发布=取页眉(投影,{'query':命中['query'],'quoted':命中['quoted'],'drilled':自身.已钻})#问一次
            except Exception as 错误:#源自己抛了
                取握手窗口().console.error('[ui-input-trigger] source "'+str(源字段(源,'name'))+'" header failed:',错误)#留下
                continue#丢掉这一源的页眉
            if 发布 is None or len(发布)==0:#没有面包屑
                continue#不占一行
            屑表[源字段(源,'name')]=发布#记下
        自身.写页眉(屑表)#发布

    def 写页眉(自身,下一):
        '两份都空就不要换引用'
        if len(自身.headers.getSnapshot())==0 and len(下一)==0:#都没有
            return#不写
        自身.headers.set(下一)#换一份

    def 记下驳回(自身):
        '记下当前这个词。光标回到原处也不能把菜单再打开'
        命中=自身.命中#当前命中
        if 命中 is None:#没有词
            自身.已驳回=None#清掉
            return#结束
        自身.已驳回={#这个词的身份
            'trigger':命中['trigger'],#字符
            'query':命中['query'],#查询
            'quoted':命中['quoted'],#引号
            'start':命中['span']['start'],#起点
            'end':命中['span']['end'],#终点
        }

    def 清启动器(自身):
        '有启动器标记就清掉'
        if 自身.launcher.getSnapshot() is not None:#有
            自身.launcher.set(None)#清掉

    def 归约(自身,事件):
        '把菜单事件归约后写回。关上时清掉启动器、下钻和页眉'
        当前=自身.menu.getSnapshot()#现在这份
        种类=事件['type']#事件种类
        下一=当前#空操作留同一份
        if 种类=='hit':#新查询，或用空命中关掉
            if 事件['hit'] is None:#空命中
                下一=收成关闭(当前)#关上
            else:#新世代。行和高亮先留着，状态改成等待
                新组=[]#等待中的组
                for 组 in 当前['groups']:#原分组
                    拷贝=dict(组)#抄一组
                    拷贝['status']='pending'#等新结果
                    新组.append(拷贝)#放回
                下一={#新世代
                    'open':True,#打开
                    'hit':事件['hit'],#这次命中
                    'generation':当前['generation']+1,#世代加一
                    'groups':新组,#行还在，状态是等待
                    'highlight':当前['highlight'],#高亮先停在原地
                }
        elif 种类=='source-settled':#一个源的候选到了
            if 当前['open'] is True and 事件['generation']==当前['generation']:#还是这一代
                下标=-1#组的位置
                序=0#扫描
                while 序<len(当前['groups']):#找这个源
                    if 当前['groups'][序]['source']==事件['source']:#对上了
                        下标=序#记下
                        break#停止
                    序+=1#下一组
                if 下标>=0:#名册里有
                    项=事件['items'] if 'items' in 事件 and 事件['items'] is not None else []#缺省当空
                    新组=[]#新分组
                    序=0#再扫
                    while 序<len(当前['groups']):#逐组
                        组=当前['groups'][序]#这一组
                        if 序==下标:#这一组落定
                            拷贝=dict(组)#抄
                            拷贝['status']='ready'#就绪
                            拷贝['items']=项#换行
                            新组.append(拷贝)#放回
                        else:#其他组不动
                            新组.append(组)#原样
                        序+=1#下一组
                    if 各组就绪且空(新组):#全都就绪而且没有行
                        下一=收成关闭(当前)#自己关上
                    else:#还有行，或还有组在等
                        高亮=仍有效高亮(当前['highlight'],新组)#旧高亮还在吗
                        if 高亮 is None:#指空了
                            高亮=首个高亮(新组)#第一行
                        下一=dict(当前)#抄状态
                        下一['groups']=新组#换组
                        下一['highlight']=高亮#换高亮
        elif 种类=='source-failed':#一个源失败，静默摘掉
            if 当前['open'] is True and 事件['generation']==当前['generation']:#还是这一代
                有=False#名册里有没有
                for 组 in 当前['groups']:#找
                    if 组['source']==事件['source']:#有
                        有=True#记下
                        break#停止
                if 有:#摘掉它
                    新组=[]#剩下的组
                    for 组 in 当前['groups']:#逐组
                        if 组['source']!=事件['source']:#不是失败的那个
                            新组.append(组)#留下
                    if len(新组)==0 or 各组就绪且空(新组):#没有组了，或剩下的都是空的
                        下一=收成关闭(当前)#关上
                    else:#还有可见的组
                        高亮=仍有效高亮(当前['highlight'],新组)#旧高亮还在吗
                        if 高亮 is None:#指空了
                            高亮=首个高亮(新组)#第一行
                        下一=dict(当前)#抄状态
                        下一['groups']=新组#换组
                        下一['highlight']=高亮#换高亮
        elif 种类=='move':#上下移动高亮
            if 当前['open'] is True:#开着才移
                位置列=[]#就绪行的位置
                for 组 in 当前['groups']:#组顺序
                    if 组['status']!='ready':#还在等的组不参加
                        continue#下一组
                    序=0#行号
                    while 序<len(组['items']):#每一行
                        位置列.append({'source':组['source'],'index':序})#记下位置
                        序+=1#下一行
                if len(位置列)>0:#有可移的行
                    高亮=当前['highlight']#当前高亮
                    所在=-1#它在位置列里的下标
                    if 高亮 is not None:#有高亮
                        序=0#扫描
                        while 序<len(位置列):#找同一行
                            点=位置列[序]#一个位置
                            if 点['source']==高亮['source'] and 点['index']==高亮['index']:#就是它
                                所在=序#记下
                                break#停止
                            序+=1#下一个
                    if 所在<0:#高亮不在表里
                        下一序=0 if 事件['dir']==1 else len(位置列)-1#向下从第一行，向上从最后一行
                    else:#循环移动
                        下一序=(所在+事件['dir']+len(位置列))%len(位置列)#绕回
                    下一高亮=位置列[下一序]#目标
                    if 高亮 is None or 下一高亮['source']!=高亮['source'] or 下一高亮['index']!=高亮['index']:#确实换了行
                        下一=dict(当前)#抄状态
                        下一['highlight']=下一高亮#换高亮
        elif 种类=='hover':#指针停在一行
            if 当前['open'] is True:#开着才停
                目标=仍有效高亮({'source':事件['source'],'index':事件['index']},当前['groups'])#必须是就绪行
                if 目标 is not None:#行还在
                    高亮=当前['highlight']#当前高亮
                    if 高亮 is None or 高亮['source']!=目标['source'] or 高亮['index']!=目标['index']:#不是同一行
                        下一=dict(当前)#抄状态
                        下一['highlight']=目标#停在这里
        elif 种类=='close':#明确关掉
            下一=收成关闭(当前)#关上
        if 下一 is not 当前:#有变化才写仓
            自身.menu.set(下一)#发布
        if 下一['open'] is True:#还开着
            return#启动器、下钻和页眉都留着
        自身.清启动器()#关上就没有启动器
        自身.已钻=False#下钻记录跟菜单一起清
        自身.写页眉({})#页眉清掉
