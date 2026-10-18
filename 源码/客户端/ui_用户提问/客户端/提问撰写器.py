'作曲座位上的提问。计划审阅走自己的卡片，其余走逐题回答'
import os
import re
from ...ui_对话.异常 import 注入模块样式文件,模块节点,标样式模块#样式模块
from ...ui_基础界面组件.按钮 import 按钮#跳过、下一题、慢慢回答
from ...ui_基础界面组件.icons import (#题卡上的图标
    图标勾描边常规,图标关闭描边常规,图标下箭头描边常规,
    图标左chevron14,图标右chevron14,图标上chevron14,图标编辑16,
)
from ...ui_基础界面组件.markdown.Markdown文本 import 处理Markdown文本#问题细节
from .约定.槽位 import 计划审阅于#收窄计划
from .计划审阅面板 import 计划审阅面板#计划卡片

__all__=['提问撰写器','提问流','答案字段','解析推荐标签']

样式路径=os.path.join(os.path.dirname(__file__),'提问撰写器.module.css')#本目录样式
样式模块='QuestionComposer'#与样式表对应的模块名
推荐后缀=re.compile(r'\s*(?:\((?:recommended|推荐)\)|（(?:recommended|推荐)）)\s*$',re.I)#推荐标记
已移除卡片={'state':'open','waitState':'counting','countdown':None,'channel':'none','closed':True}#卡片已从登记表拿掉


def 设类(节点,*类名):
    '挂上官方类名，让模块样式生效'
    留下=[名 for 名 in 类名 if isinstance(名,str) and 名!='']#空的不要
    节点.className=' '.join(留下)#类名保持原文
    return 标样式模块(节点,样式模块)#模块属性


def 解析推荐标签(标签):
    '拆掉末尾的推荐标记。选中后送出的仍是原来的标签'
    if 推荐后缀.search(标签) is not None:#有标记
        return {'label':推荐后缀.sub('',标签),'recommended':True}#去掉标记
    return {'label':标签,'recommended':False}#原样


def 等待句(卡片):
    '倒计时或暂停。秒数按剩余毫秒向上取整'
    倒计时=卡片['countdown']#倒计时
    if 倒计时 is None:#没有
        return ''#不显示
    秒=int((倒计时['remainingMs']+999)/1000) if 倒计时['remainingMs']>0 else 0#向上取整
    if 秒<0:#不能为负
        秒=0#零
    if 倒计时['running']:#还在走
        return '{seconds} 秒后继续工作'.replace('{seconds}',str(秒))#中文表
    return '已暂停 · 剩余 {seconds} 秒'.replace('{seconds}',str(秒))#中文表


class 答案字段:
    '自动长高的自由文本。镜子决定高度，输入框跟它同一格'
    def __init__(自身,属性):
        '记下变体、草稿和事件'
        自身.属性=属性#绘制属性

    def 渲染(自身):
        '画出镜子和单行文本框'
        窗口=自身.属性['window']#窗口
        文档=窗口.document#文档
        根=文档.createElement('div')#字段
        if 自身.属性['variant']=='inline':#跟在选项后面
            设类(根,'field','customInline')#行内
        else:#没有选项时独占一块
            设类(根,'field','customBlock')#成块
        镜=模块节点(文档,'div',样式模块,'fieldMirror')#高度尺
        镜.setAttribute('aria-hidden','true')#不读
        镜.textContent=自身.属性['value']+'\n'#多留一行
        框=文档.createElement('textarea')#输入
        设类(框,'fieldInput')#输入
        框.value=自身.属性['value']#草稿
        框.disabled=自身.属性['disabled'] is True#锁定
        框.rows=1#自身高度不参与
        框.placeholder='输入你的答案'#中文表
        if 自身.属性.get('onFocus') is not None:#需要焦点回调
            框.addEventListener('focus',自身.属性['onFocus'])#焦点
        框.addEventListener('input',自身.属性['onChange'])#每次编辑
        框.addEventListener('keydown',自身.属性['onKeyDown'])#回车
        根.appendChild(镜)#镜子
        根.appendChild(框)#输入
        if 自身.属性.get('autoFocus') is True:#第一次给焦点
            框.focus()#聚焦
        return 根#节点


class 提问流:
    '逐题回答。草稿在会话存储里，倒计时在卡片上'
    实例表={}#请求键到这一轮

    @classmethod
    def 呈现(类,属性):
        '根还在页面上就更新。卸下后按存储里的草稿重新开始'
        键=属性['matched'].key#请求键
        已有=类.实例表[键] if 键 in 类.实例表 else None#已有
        if 已有 is not None and 已有.根 is not None and 已有.根.parentNode is not None:#还挂着
            已有.属性=属性#换属性
            return 已有.渲染()#更新
        if 已有 is not None:#上次已经卸下
            已有.拆除()#摘掉监听
        已有=object.__new__(类)#新的一轮
        类.实例表[键]=已有#记住
        已有.建立(属性)#初始化
        return 已有.渲染()#画出

    def 建立(自身,属性):
        '记下本地开关，并订上卡片和草稿'
        自身.属性=属性#槽位属性
        自身.忙碌=None#answer 或 cancel
        自身.错误=None#反馈
        自身.收起=False#收到标题条
        自身.已聚焦=set()#已经自动聚焦过的题号
        自身.等待处置=自身.初等待()#从草稿恢复的等待
        自身.发送经由=None#瀑布送出后还等着投影
        自身.已清草稿=False#关闭后只清一次
        自身.已修剪=False#只修剪一次过期草稿
        自身.已按等待=False#恢复等待只做一次
        自身.根=None#外层
        自身.体=None#题目区
        自身.脚=None#页脚
        自身.等待文=None#倒计时句子
        自身.头指纹=None#标题区
        自身.体指纹=None#题目区
        自身.脚指纹=None#页脚
        自身.下标=0#当前题
        自身.草稿=[]#当前草稿
        自身.问题列表=[]#问题
        自身.问题=None#当前题
        自身.卡片=已移除卡片#快照
        自身.审阅中=False#只读
        自身.锁定=False#不能改
        自身.可提交=False#有通道
        自身.绘制中=False#防止订阅重入
        自身.待重画=False#绘制中又来了一次
        自身.退订=[]#卡片和存储
        自身.已挂窗口=False#焦点监听
        待=属性['matched']#卡片
        def 变了():
            '卡片或草稿变了就重画'
            if 自身.绘制中:#正在画
                自身.待重画=True#等这一轮结束
                return
            自身.渲染()#重画
        自身.退订.append(待.subscribe(变了))#卡片
        存储钩=属性.get('useStore')#草稿钩子
        if callable(存储钩) and hasattr(存储钩,'_subscribe'):#能订
            自身.退订.append(存储钩._subscribe(变了))#草稿
        窗口=属性['window']#窗口
        窗口.addEventListener('blur',自身.窗口失焦)#窗口失焦
        窗口.addEventListener('focus',自身.窗口聚焦)#窗口聚焦
        窗口.document.addEventListener('visibilitychange',自身.可见变化)#页面隐藏
        自身.已挂窗口=True#已挂

    def 拆除(自身):
        '卸下后不再听卡片、草稿和窗口'
        for 退 in 自身.退订:#逐个
            if callable(退):#是函数
                退()#退订
        自身.退订=[]#清空
        if 自身.已挂窗口:#还挂着窗口
            窗口=自身.属性['window']#窗口
            窗口.removeEventListener('blur',自身.窗口失焦)#摘掉
            窗口.removeEventListener('focus',自身.窗口聚焦)#摘掉
            窗口.document.removeEventListener('visibilitychange',自身.可见变化)#摘掉
            自身.已挂窗口=False#记下

    def 读存储进度(自身):
        '只接受还对得上这批题的草稿'
        钩=自身.属性.get('useStore')#钩子
        if not callable(钩):#没有存储
            return None#无
        键=自身.属性['matched'].key#请求键
        def 选取(状态):
            '取出这一条的进度'
            表=状态.get('progressByRequest') if isinstance(状态,dict) else None#表
            if not isinstance(表,dict):#没有
                return None#无
            return 表.get(键)#这一条
        进度=钩(选取)#读出
        题数=len(自身.属性['matched'].questions)#题数
        if not isinstance(进度,dict):#不是对象
            return None#无效
        下标=进度.get('index')#题号
        草稿=进度.get('drafts')#草稿
        等待=进度.get('wait')#等待
        if not isinstance(下标,int) or isinstance(下标,bool) or 下标<0 or 下标>=题数:#题号不对
            return None#无效
        if not isinstance(草稿,list) or len(草稿)!=题数:#题数对不上
            return None#无效
        if 等待 is not None and 等待!='editing' and 等待!='waiting':#等待值不对
            return None#无效
        for 项 in 草稿:#逐题
            if not isinstance(项,dict):#不是对象
                return None#无效
            选择=项.get('selected')#选择
            if not isinstance(选择,list) or not isinstance(项.get('custom'),str) or not isinstance(项.get('skipped'),bool):#字段不对
                return None#无效
            for 标签 in 选择:#每个标签
                if not isinstance(标签,str):#不是字符串
                    return None#无效
        return 进度#可用

    def 初始草稿(自身):
        '只读卡用记录。活卡片把第一项推荐当作还没提交的草稿'
        待=自身.属性['matched']#卡片
        问题列表=待.questions#问题
        记录={}#按编号
        if 待.review is not None:#只读
            for 答案 in 待.review:#逐条
                记录[答案.get('id')]=答案#记下
        结果=[]#草稿
        for 问题 in 问题列表:#逐题
            答案=记录.get(问题.get('id'))#记录
            自定义=''#自定义
            if 答案 is not None and isinstance(答案.get('custom'),str):#有自定义
                自定义=答案['custom']#原文
            推荐=None#首项推荐
            if 待.review is None:#活卡片才预选
                选项=问题.get('options')#选项
                if isinstance(选项,list) and len(选项)>0 and isinstance(选项[0].get('label'),str):#有首项
                    标签=选项[0]['label']#原文标签
                    if 解析推荐标签(标签)['recommended'] is True:#标了推荐
                        推荐=标签#预选原文
            if 答案 is None and 推荐 is not None:#还没有记录
                选择=[推荐]#预选
            elif 答案 is None:#没有记录也没有推荐
                选择=[]#空
            else:#按记录
                选择=list(答案.get('selected') or [])#选择
            跳过=答案 is not None and len(答案.get('selected') or [])==0 and 自定义==''#空记录算跳过
            结果.append({'selected':选择,'custom':自定义,'skipped':跳过})#一题
        return 结果#草稿

    def 初等待(自身):
        '存储里的等待优先。草稿已经和初始不同就当成正在编辑'
        if 自身.属性['matched'].review is not None:#只读不恢复等待
            return None#无
        进度=自身.读存储进度()#存储
        if 进度 is None:#没有可用草稿
            return None#无
        if 进度.get('wait') in ('editing','waiting'):#存过等待
            return 进度['wait']#用它
        初始=自身.初始草稿()#对照
        序=0#题号
        for 项 in 进度['drafts']:#逐题
            原=初始[序]#初始
            if len(项['selected'])!=len(原['selected']):#选择数量不同
                return 'editing'#已经改过
            位=0#标签位置
            for 标签 in 项['selected']:#逐个
                if 位>=len(原['selected']) or 标签!=原['selected'][位]:#标签不同
                    return 'editing'#已经改过
                位+=1#下一个
            if 项['custom']!='' or 项['skipped'] is True:#写过或跳过
                return 'editing'#已经改过
            序+=1#下一题
        return None#还是初始

    def 读卡片(自身):
        '优先读键控钩子。卡片已经不在登记表里就当成已关闭'
        钩=自身.属性.get('useQuestionCard')#键控钩子
        键=自身.属性['matched'].key#请求键
        if not callable(钩):#没有钩子
            return 自身.属性['matched'].getSnapshot()#卡片自己的快照
        def 选择(快照):
            '没有快照就是已经移除'
            if 快照 is None:#移除
                return 已移除卡片#已关闭
            return 快照#原样
        return 钩(键,选择)#读出

    def 替换进度(自身,下标,草稿列表):
        '写回这一条的题号、草稿和等待'
        进度={'index':下标,'drafts':草稿列表}#进度
        if 自身.等待处置 is not None:#已经选过等待
            进度['wait']=自身.等待处置#一起存
        自身.属性['actions'].replace(自身.属性['matched'].key,进度)#写入

    def 已答(自身,项):
        '选了或写了非空白自定义就算答了'
        return len(项['selected'])>0 or 项['custom'].strip()!=''#有内容

    def 确保编辑(自身):
        '第一次改动就停掉前台倒计时'
        if 自身.等待处置 is not None:#已经记过
            return
        自身.等待处置='editing'#正在编辑
        自身.属性['matched'].开始编辑()#停表

    def 改草稿(自身,更新,下一标=None):
        '改当前题并清掉错误。单选可以顺便翻到下一题'
        自身.确保编辑()#停表
        if 下一标 is None:#留在这一题
            下一标=自身.下标#当前
        新=[]#下一份
        序=0#位置
        for 项 in 自身.草稿:#逐题
            if 序==自身.下标:#当前题
                新.append(更新(项))#替换
            else:#其它题
                新.append(项)#原样
            序+=1#下一题
        自身.替换进度(下一标,新)#写回
        自身.错误=None#清错误

    def 选择(自身,标签):
        '多选切换这一项。单选替换选择，不是最后一题就翻页'
        多选=自身.问题.get('multiSelect') is True#多选
        最后=自身.下标>=len(自身.问题列表)-1#最后一题
        def 更新(当前):
            '写出这一题的新草稿'
            if 多选:#切换
                if 标签 in 当前['selected']:#已选
                    选=[项 for 项 in 当前['selected'] if 项!=标签]#取消
                else:#未选
                    选=list(当前['selected'])+[标签]#加上
                return {'selected':选,'custom':当前['custom'],'skipped':False}#保留自定义
            return {'selected':[标签],'custom':'','skipped':False}#单选清掉自定义
        下一=自身.下标#默认留在这一题
        if not 多选 and not 最后:#单选还能翻
            下一=自身.下标+1#下一题
        自身.改草稿(更新,下一)#写回

    def 点慢慢答(自身,_事件=None):
        '停掉倒计时，并把这个选择存进草稿'
        自身.等待处置='waiting'#一直等
        自身.属性['matched'].慢慢答()#停表
        自身.替换进度(自身.下标,自身.草稿)#存等待

    def 收起流(自身,_事件=None):
        '能从工具调用打开的只离开座位。否则取消整组'
        待=自身.属性['matched']#卡片
        if 待.dismissal=='hide':#还能打开
            待.收起()#离开座位
            return
        if not 自身.可提交:#还不能取消
            自身.错误={'键':'error.unavailable'}#不能提交
            自身.渲染()#显示
            return
        自身.忙碌='cancel'#取消中
        自身.错误=None#清错误
        自身.发送经由='waterfall'#等投影
        自身.渲染()#禁用
        try:#取消
            待.收起()#取消请求
        except Exception as 原因:#失败
            自身.发送经由=None#不再等
            自身.忙碌=None#恢复
            自身.错误={'文':str(原因)}#原因
            自身.渲染()#显示

    def 提交草稿(自身,草稿列表):
        '每题都要答完或跳过。瀑布送出后先保持忙碌，远程送出后再收起'
        缺=-1#第一道没完成的
        序=0#位置
        for 项 in 草稿列表:#逐题
            if not (自身.已答(项) or 项['skipped'] is True):#没完成
                缺=序#记下
                break#停
            序+=1#下一题
        if 缺>=0:#还有空题
            自身.替换进度(缺,草稿列表)#翻到那一题
            自身.错误={'键':'error.incomplete'}#没完成
            自身.渲染()#显示
            return
        if not 自身.可提交:#没有通道
            自身.错误={'键':'error.unavailable'}#不能提交
            自身.渲染()#显示
            return
        答案=[]#整批
        序=0#位置
        for 问题 in 自身.问题列表:#逐题
            值=草稿列表[序]#草稿
            if 值['skipped'] is True:#跳过
                答案.append({'id':问题['id'],'selected':[]})#空选择
            else:#有答案
                自定义=值['custom'].strip()#去掉空白
                条={'id':问题['id'],'selected':[]}#一条
                if 自定义=='' or 问题.get('multiSelect') is True:#多选保留已选
                    条['selected']=list(值['selected'])#选择
                if 自定义!='':#有自定义
                    条['custom']=自定义#自定义
                答案.append(条)#留下
            序+=1#下一题
        自身.忙碌='answer'#送出中
        自身.错误=None#清错误
        通道=自身.属性['matched'].getSnapshot()['channel']#这一拍的通道
        自身.发送经由='waterfall' if 通道=='waterfall' else None#瀑布要等投影
        自身.渲染()#禁用
        try:#送出
            自身.属性['matched'].作答({'answers':答案})#整批
        except Exception as 原因:#失败
            自身.发送经由=None#不再等
            自身.忙碌=None#恢复
            自身.错误={'文':str(原因)}#原因
            自身.渲染()#显示
            return
        if 通道!='rpc':#瀑布只算送出
            return
        自身.发送经由=None#远程已经收下
        自身.忙碌=None#恢复
        自身.错误=None#清错误
        try:#收起面板
            自身.属性['matched'].收起()#离开座位
        except Exception:#没关上
            自身.错误={'键':'status.sent'}#留下这句
        自身.渲染()#写回

    def 继续(自身,_事件=None):
        '这一题有答案才翻页。最后一题则送出整批'
        if not 自身.已答(自身.草稿[自身.下标]):#还空着
            自身.错误={'键':'error.unanswered'}#没答
            自身.渲染()#显示
            return
        if 自身.下标<len(自身.问题列表)-1:#还能翻
            自身.替换进度(自身.下标+1,自身.草稿)#下一题
            自身.错误=None#清错误
            return
        自身.提交草稿(自身.草稿)#送出

    def 改自定义(自身,事件):
        '多选保留已选。单选的自定义答案替换选择'
        值=事件.target.value#当前文本
        多选=自身.问题.get('multiSelect') is True#多选
        def 更新(当前):
            '写上自定义并取消跳过'
            if 多选:#保留选择
                选=list(当前['selected'])#已选
            else:#自定义替换选择
                选=[]#清空
            return {'selected':选,'custom':值,'skipped':False}#新草稿
        自身.改草稿(更新)#写回

    def 自定义按键(自身,事件):
        '回车继续。换行和输入法组合留给文本框'
        组合=getattr(事件,'isComposing',False) is True or getattr(事件,'keyCode',None)==229#输入法
        if 事件.key!='Enter' or 事件.shiftKey or 组合:#不是确认
            return
        事件.preventDefault()#不换行
        自身.继续()#继续

    def 选项按键(自身,事件):
        '选项上的回车直接送出当前草稿'
        if 事件.key!='Enter':#不是回车
            return
        事件.preventDefault()#不点击
        自身.提交草稿(自身.草稿)#送出

    def 跳过(自身,_事件=None):
        '这一题记成跳过。最后一题就送出'
        自身.确保编辑()#停表
        新=[]#下一份
        序=0#位置
        for 项 in 自身.草稿:#逐题
            if 序==自身.下标:#当前题
                新.append({'selected':[],'custom':'','skipped':True})#跳过
            else:#其它
                新.append(项)#原样
            序+=1#下一题
        下一=自身.下标+1 if 自身.下标<len(自身.问题列表)-1 else 自身.下标#翻或留下
        自身.替换进度(下一,新)#写回
        自身.错误=None#清错误
        if 自身.下标<len(自身.问题列表)-1:#已经翻页
            return
        自身.提交草稿(新)#最后一题送出

    def 上一题(自身,_事件=None):
        '只翻页，不改答案'
        自身.替换进度(自身.下标-1,自身.草稿)#上一题
        自身.错误=None#清错误

    def 下一题(自身,_事件=None):
        '只翻页，不改答案'
        自身.替换进度(自身.下标+1,自身.草稿)#下一题
        自身.错误=None#清错误

    def 切换收起(自身,_事件=None):
        '收到标题条，或再展开'
        自身.收起=not 自身.收起#反过来
        自身.头指纹=None#标题按钮文案要换
        自身.体指纹=None#正文要换
        自身.脚指纹=None#页脚要换
        自身.渲染()#重画

    def 字段聚焦(自身,_事件=None):
        '这一题已经得到过焦点，再展开时不再抢'
        自身.已聚焦.add(自身.下标)#记下

    def 答案聚焦(自身,事件):
        '焦点从外面进入回答区时按住倒计时'
        if not 事件.currentTarget.contains(事件.relatedTarget):#从外面进来
            自身.属性['matched'].按住焦点()#按住

    def 答案失焦(自身,事件):
        '焦点离开回答区后继续倒计时'
        if not 事件.currentTarget.contains(事件.relatedTarget):#到了外面
            自身.属性['matched'].放开焦点()#放开

    def 窗口失焦(自身,_事件=None):
        '窗口失焦时放开倒计时'
        自身.属性['matched'].放开焦点()#放开

    def 窗口聚焦(自身,_事件=None):
        '正在编辑就保持编辑。焦点还在回答区就继续按住'
        if 自身.等待处置=='editing':#已经改过
            自身.属性['matched'].开始编辑()#保持
            return
        文档=自身.属性['window'].document#文档
        if 自身.体 is not None and 自身.体.contains(文档.activeElement) is True:#焦点还在
            自身.属性['matched'].按住焦点()#按住

    def 可见变化(自身,_事件=None):
        '页面隐藏当失焦，回来再按焦点恢复'
        文档=自身.属性['window'].document#文档
        if 文档.hidden:#隐藏
            自身.窗口失焦()#放开
        else:#回来
            自身.窗口聚焦()#恢复

    def 渲染(自身):
        '同步关闭、修剪和恢复等待，再按变化更新标题、正文和页脚'
        自身.绘制中=True#挡住重入
        try:#画完再处理排队的刷新
            自身.同步效果()#关闭和等待
            自身.读出()#草稿和快照
            窗口=自身.属性['window']#窗口
            if 自身.根 is None:#第一次
                自身.造骨架(窗口)#外层
            自身.刷新(窗口)#更新
        finally:#允许下一轮
            自身.绘制中=False#结束
        if 自身.待重画:#绘制中又变了
            自身.待重画=False#消费
            return 自身.渲染()#再画
        if 'parent' in 自身.属性 and 自身.根.parentNode is not 自身.属性['parent']:#指定了父节点
            自身.属性['parent'].appendChild(自身.根)#挂上
        return 自身.根#节点

    def 同步效果(自身):
        '瀑布送出后若工作已继续，就请用户再交一次'
        卡片=自身.读卡片()#当前快照
        if 自身.发送经由=='waterfall' and 卡片['state']=='continued':#没送到
            自身.发送经由=None#不再等
            自身.忙碌=None#恢复
            自身.错误={'键':'error.resubmit'}#再交一次
        if 卡片['closed'] is True and not 自身.已清草稿:#卡片关了
            自身.已清草稿=True#只清一次
            自身.属性['actions'].clear(自身.属性['matched'].key)#清草稿
        if not 自身.已修剪:#第一次
            自身.已修剪=True#记下
            自身.属性['actions'].prune(自身.属性['matched'].活键())#去掉过期草稿
        if not 自身.已按等待:#恢复等待
            自身.已按等待=True#记下
            if 自身.等待处置=='waiting':#一直等
                自身.属性['matched'].慢慢答()#停表
            if 自身.等待处置=='editing':#正在编辑
                自身.属性['matched'].开始编辑()#停表

    def 读出(自身):
        '题号可以从只读卡的草稿恢复，答案本身只用记录'
        待=自身.属性['matched']#卡片
        自身.问题列表=list(待.questions)#问题
        自身.卡片=自身.读卡片()#快照
        自身.审阅中=待.review is not None#只读
        合法=自身.读存储进度()#存储
        存储=None if 自身.审阅中 else 合法#只读不用草稿答案
        自身.下标=0 if 合法 is None else 合法['index']#题号
        if 存储 is None:#没有活草稿
            自身.草稿=自身.初始草稿()#初始
        else:#用存储
            自身.草稿=存储['drafts']#草稿
        if 自身.下标<0 or 自身.下标>=len(自身.问题列表):#越界
            自身.下标=0#回到第一题
        自身.问题=自身.问题列表[自身.下标]#当前题
        自身.可提交=自身.卡片['channel']!='none'#有通道
        自身.锁定=自身.忙碌 is not None or 自身.审阅中#不能改

    def 造骨架(自身,窗口):
        '外层、卡片和标题。正文等没有收起再放'
        文档=窗口.document#文档
        待=自身.属性['matched']#卡片
        根=模块节点(文档,'div',样式模块,'frame')#外层
        根.setAttribute('data-question-key',待.key)#请求键
        卡=模块节点(文档,'section',样式模块,'card')#卡片
        头=模块节点(文档,'header',样式模块,'header')#标题
        块=模块节点(文档,'div',样式模块,'headingBlock')#题干
        眉=模块节点(文档,'div',样式模块,'eyebrow')#眉题
        题=文档.createElement('h2')#标题
        设类(题,'title')#标题
        块.appendChild(眉)#眉题
        块.appendChild(题)#标题
        头.appendChild(块)#题干
        动作=模块节点(文档,'div',样式模块,'headerActions')#右侧
        头.appendChild(动作)#动作
        卡.appendChild(头)#标题
        根.appendChild(卡)#卡片
        注入模块样式文件(文档,'提问撰写器样式',样式路径,样式模块)#样式
        自身.根=根#留下
        自身.卡=卡#留下
        自身.眉=眉#留下
        自身.题=题#留下
        自身.动作=动作#留下

    def 刷新(自身,窗口):
        '倒计时只改句子。题目或页脚变了才重做那一块'
        卡片=自身.卡片#快照
        头=(卡片['waitState'],卡片['countdown'] is not None,卡片['state'],自身.审阅中,自身.忙碌,自身.收起,自身.下标,自身.问题.get('question'),自身.问题.get('header'))#标题事实
        if 头!=自身.头指纹:#标题要重做
            自身.头指纹=头#记下
            自身.画头(窗口)#重做
        elif 自身.等待文 is not None:#只剩秒数
            自身.等待文.textContent=等待句(卡片)#改句子
        草稿印=tuple((tuple(项['selected']),项['custom'],项['skipped']) for 项 in 自身.草稿)#草稿
        体=(自身.下标,自身.收起,自身.锁定,自身.审阅中,草稿印,自身.可提交,卡片['countdown'] is None)#正文事实
        if 体!=自身.体指纹:#正文要重做
            自身.体指纹=体#记下
            自身.画体(窗口)#重做
        当前=自身.草稿[自身.下标]#这一题
        错=None if 自身.错误 is None else tuple(sorted(自身.错误.items()))#错误
        脚=(自身.下标,自身.忙碌,错,自身.可提交,自身.已答(当前),自身.审阅中,自身.收起,len(自身.问题列表))#页脚事实
        if 脚!=自身.脚指纹:#页脚要重做
            自身.脚指纹=脚#记下
            自身.画脚(窗口)#重做
        if 自身.收起:#收到标题
            设类(自身.卡,'card','cardMinimized')#取消高度上限
        else:#展开
            设类(自身.卡,'card')#普通卡片
        自身.卡.setAttribute('aria-labelledby','question-'+自身.属性['matched'].key+'-'+str(自身.下标))#指向标题

    def 画头(自身,窗口):
        '眉题、标题，以及倒计时、慢慢回答、收起和关闭'
        文档=窗口.document#文档
        待=自身.属性['matched']#卡片
        问题=自身.问题#当前题
        眉文=问题.get('header')#眉题
        if 眉文 is None:#没有
            自身.眉.style.display='none'#藏起
            自身.眉.textContent=''#清空
        else:#有眉题
            自身.眉.style.display=''#显示
            自身.眉.textContent=眉文#眉题
        自身.题.id='question-'+待.key+'-'+str(自身.下标)#无障碍标识
        自身.题.textContent=问题.get('question') or ''#题干
        while 自身.动作.firstChild is not None:#清掉旧按钮
            自身.动作.removeChild(自身.动作.firstChild)#摘掉
        自身.等待文=None#等下面再挂
        卡片=自身.卡片#快照
        显示倒计时=卡片['countdown'] is not None and 卡片['waitState'] not in ('waiting','editing','continued')#还在走或暂停
        if 显示倒计时:#倒计时
            句=模块节点(文档,'span',样式模块,'waitStatus')#句子
            句.textContent=等待句(卡片)#句子
            自身.动作.appendChild(句)#放上
            自身.等待文=句#留下
            慢=按钮({#慢慢回答
                'window':窗口,
                'variant':'outline',
                'className':'waitButton',
                'disabled':False,
                'onClick':自身.点慢慢答,
                'children':'慢慢回答',
            })
            慢钮=慢.渲染()#按钮
            标样式模块(慢钮,样式模块)#样式
            自身.动作.appendChild(慢钮)#放上
        if 卡片['state']=='continued':#已经继续
            继=模块节点(文档,'span',样式模块,'waitStatus')#句子
            继.textContent='已继续工作，仍可回答'#中文表
            自身.动作.appendChild(继)#放上
        if 卡片['countdown'] is not None and 卡片['waitState'] in ('waiting','editing'):#按住了
            按=模块节点(文档,'span',样式模块,'waitStatus')#句子
            按.textContent='会一直等你回答'#中文表
            自身.动作.appendChild(按)#放上
        if 自身.审阅中:#只读
            读=模块节点(文档,'span',样式模块,'waitStatus')#句子
            读.textContent='已回答'#中文表
            自身.动作.appendChild(读)#放上
        收文='展开问题卡片' if 自身.收起 else '收起问题卡片'#开关文案
        收=文档.createElement('button')#收起
        收.type='button'#按钮
        设类(收,'iconButton')#图标钮
        收.setAttribute('aria-label',收文)#无障碍
        收.title=收文#悬停
        收.setAttribute('aria-expanded','false' if 自身.收起 else 'true')#展开态
        收.disabled=自身.忙碌 is not None#送出时不动
        收.addEventListener('click',自身.切换收起)#切换
        if 自身.收起:#现在是收起
            收.appendChild(图标上chevron14({'window':窗口}))#展开
        else:#现在是展开
            收.appendChild(图标下箭头描边常规({'window':窗口}))#收起
        自身.动作.appendChild(收)#放上
        关文='收起问题面板，可从工具调用重新打开' if 待.dismissal=='hide' else '放弃整组问题'#关闭文案
        关=文档.createElement('button')#关闭
        关.type='button'#按钮
        设类(关,'iconButton')#图标钮
        关.setAttribute('aria-label',关文)#无障碍
        关.title=关文#悬停
        关.disabled=自身.忙碌 is not None#送出时不动
        关.addEventListener('click',自身.收起流)#关闭
        关.appendChild(图标关闭描边常规({'window':窗口}))#叉
        自身.动作.appendChild(关)#放上

    def 画体(自身,窗口):
        '收起时拿掉正文。展开时重做选项，并尽量把焦点留在文本框'
        文档=窗口.document#文档
        活动=文档.activeElement#当前焦点
        选起=None#选区
        选止=None#选区
        if 活动 is not None and 自身.根.contains(活动) and getattr(活动,'tagName','')=='TEXTAREA':#正在输入
            选起=活动.selectionStart#起点
            选止=活动.selectionEnd#终点
        if 自身.体 is not None:#旧正文
            自身.体.remove()#摘掉
            自身.体=None#清空
        if 自身.收起:#只留标题
            return
        待=自身.属性['matched']#卡片
        问题=自身.问题#当前题
        草稿=自身.草稿[自身.下标]#这一题
        体=模块节点(文档,'div',样式模块,'body')#正文
        体.setAttribute('data-question-scroll','')#滚动标记
        体.addEventListener('focus',自身.答案聚焦,True)#捕获焦点
        体.addEventListener('blur',自身.答案失焦,True)#捕获失焦
        if 问题.get('detail') is not None:#有细节
            细节=模块节点(文档,'div',样式模块,'detail')#细节
            细节.appendChild(处理Markdown文本(窗口,{#细节
                'text':问题['detail'],#正文
                'window':窗口,#窗口
                'codeLabels':{#代码块上的字
                    'copyLabel':'复制',#复制
                    'copiedLabel':'复制成功',#已复制
                },
                'labels':{#上游交给共享组件的整份文案
                    'code':{
                        'copyLabel':'复制',#复制
                        'copiedLabel':'复制成功',#已复制
                        'toolbarLabels':{
                            'codeLabel':'代码块',#代码块
                            'wrapLabel':'自动换行',#换行
                            'unwrapLabel':'取消自动换行',#不换行
                        },
                    },
                    'footnotes':'脚注',#脚注
                },
            }))
            体.appendChild(细节)#细节
        选项区=模块节点(文档,'div',样式模块,'options')#选项
        选项区.setAttribute('role','group' if 问题.get('multiSelect') is True else 'radiogroup')#单选或多选
        选项表=问题.get('options') or []#选项
        序=0#序号
        for 选项 in 选项表:#逐项
            选中=选项.get('label') in 草稿['selected']#是否选中
            展示=解析推荐标签(选项.get('label') or '')#去掉推荐标记
            钮=文档.createElement('button')#选项
            钮.type='button'#按钮
            if 选中 and 问题.get('multiSelect') is not True:#单选中
                设类(钮,'option','optionSelected')#选中
            else:#未选或是多选
                设类(钮,'option')#普通
            钮.setAttribute('role','checkbox' if 问题.get('multiSelect') is True else 'radio')#角色
            钮.setAttribute('aria-checked','true' if 选中 else 'false')#选中态
            钮.setAttribute('aria-label',展示['label'])#无障碍名用展示标签
            钮.disabled=自身.锁定#锁定
            def 点下(事件,标签=选项.get('label')):
                '点这一项'
                自身.选择(标签)#选择
            钮.addEventListener('click',点下)#点击
            钮.addEventListener('keydown',自身.选项按键)#回车送出
            if 问题.get('multiSelect') is True:#多选框
                if 选中:#已选
                    盒=模块节点(文档,'span',样式模块,'checkbox checkboxChecked')#选中盒
                    盒.appendChild(图标勾描边常规({'window':窗口,'size':12}))#勾
                else:#未选
                    盒=模块节点(文档,'span',样式模块,'checkbox')#空盒
                盒.setAttribute('aria-hidden','true')#不读
                钮.appendChild(盒)#盒子
            else:#序号
                号=模块节点(文档,'span',样式模块,'number')#序号
                号.textContent=str(序+1)#从 1 起
                钮.appendChild(号)#序号
            文=模块节点(文档,'span',样式模块,'optionCopy')#文案
            行=模块节点(文档,'span',样式模块,'optionLine')#一行
            名=模块节点(文档,'span',样式模块,'optionLabel')#标签
            名.textContent=展示['label']#展示标签
            行.appendChild(名)#标签
            if 展示['recommended'] is True:#推荐
                徽=模块节点(文档,'span',样式模块,'badge')#徽标
                徽.textContent='推荐'#中文表
                行.appendChild(徽)#徽标
            if 选项.get('description') is not None:#有说明
                说明=模块节点(文档,'span',样式模块,'description')#说明
                说明.textContent=选项['description']#说明
                行.appendChild(说明)#说明
            文.appendChild(行)#一行
            钮.appendChild(文)#文案
            选项区.appendChild(钮)#选项
            序+=1#下一个
        if 自身.审阅中 and 草稿['skipped'] is True:#当时跳过
            注=文档.createElement('p')#说明
            设类(注,'reviewNote')#说明
            注.textContent='这道问题当时被跳过。'#中文表
            选项区.appendChild(注)#说明
        有选项=len(选项表)>0#有选项
        显示自定义=自身.审阅中 is False or 草稿['custom']!=''#只读时只有写过才留框
        if 显示自定义 and 有选项:#跟在选项后面
            行类=['customRow']#行
            if 草稿['custom']!='':#写了字
                行类.append('customRowActive')#激活
            if 问题.get('multiSelect') is not True and len(草稿['selected'])>0:#单选已经选了
                行类.append('customRowYielded')#让出选中样式
            行=文档.createElement('div')#自定义行
            设类(行,*行类)#行
            if 问题.get('multiSelect') is True:#多选的自定义也用盒子
                if 草稿['custom']!='':#写了字
                    盒=模块节点(文档,'span',样式模块,'checkbox checkboxChecked')#选中
                    盒.appendChild(图标勾描边常规({'window':窗口,'size':12}))#勾
                else:#还没写
                    盒=模块节点(文档,'span',样式模块,'checkbox')#空
                盒.setAttribute('aria-hidden','true')#不读
                行.appendChild(盒)#盒子
            else:#铅笔
                号=模块节点(文档,'span',样式模块,'number')#座位
                号.setAttribute('aria-hidden','true')#不读
                号.appendChild(图标编辑16({'window':窗口,'size':12}))#铅笔
                行.appendChild(号)#座位
            行.appendChild(答案字段({#行内输入
                'window':窗口,
                'variant':'inline',
                'value':草稿['custom'],
                'disabled':自身.锁定,
                'onChange':自身.改自定义,
                'onKeyDown':自身.自定义按键,
            }).渲染())
            选项区.appendChild(行)#自定义
        elif 显示自定义:#没有选项，输入框自己成块
            自动=自身.可提交 and 自身.卡片['countdown'] is None and not 自身.锁定 and 自身.下标 not in 自身.已聚焦 and 选起 is None#第一次才抢焦点
            选项区.appendChild(答案字段({#成块输入
                'window':窗口,
                'variant':'block',
                'value':草稿['custom'],
                'disabled':自身.锁定,
                'autoFocus':自动,
                'onFocus':自身.字段聚焦,
                'onChange':自身.改自定义,
                'onKeyDown':自身.自定义按键,
            }).渲染())
        体.appendChild(选项区)#选项
        if 自身.脚 is not None and 自身.脚.parentNode is 自身.卡:#页脚已经在
            自身.卡.insertBefore(体,自身.脚)#正文留在页脚前
        else:#还没有页脚
            自身.卡.appendChild(体)#正文
        自身.体=体#留下
        if 选起 is not None:#把焦点还回去
            框=None#文本框
            节点列=体.querySelectorAll('textarea') if hasattr(体,'querySelectorAll') else []#文本框
            if len(节点列)>0:#有
                框=节点列[0]#第一个
            if 框 is not None:#还在
                框.focus()#聚焦
                if hasattr(框,'setSelectionRange'):#能恢复选区
                    框.setSelectionRange(选起,选止)#选区

    def 画脚(自身,窗口):
        '翻页、错误，以及跳过和下一题。只读卡没有送出按钮'
        文档=窗口.document#文档
        if 自身.脚 is not None:#旧页脚
            自身.脚.remove()#摘掉
            自身.脚=None#清空
        if 自身.收起:#收起不留页脚
            return
        脚=模块节点(文档,'footer',样式模块,'footer')#页脚
        页=模块节点(文档,'div',样式模块,'pager')#翻页
        上=文档.createElement('button')#上一题
        上.type='button'#按钮
        设类(上,'iconButton')#图标钮
        上.setAttribute('aria-label','上一题')#中文表
        上.disabled=自身.下标==0 or 自身.忙碌 is not None#第一题或忙碌
        上.addEventListener('click',自身.上一题)#翻页
        上.appendChild(图标左chevron14({'window':窗口}))#左
        页.appendChild(上)#上一题
        进度=模块节点(文档,'span',样式模块,'progress')#页码
        进度.textContent=str(自身.下标+1)+' / '+str(len(自身.问题列表))#页码
        页.appendChild(进度)#页码
        下=文档.createElement('button')#下一题
        下.type='button'#按钮
        设类(下,'iconButton')#图标钮
        下.setAttribute('aria-label','下一题')#中文表
        下.disabled=自身.下标==len(自身.问题列表)-1 or 自身.忙碌 is not None#最后或忙碌
        下.addEventListener('click',自身.下一题)#翻页
        下.appendChild(图标右chevron14({'window':窗口}))#右
        页.appendChild(下)#下一题
        脚.appendChild(页)#翻页
        反馈=模块节点(文档,'div',样式模块,'feedback')#错误
        反馈.setAttribute('role','status')#状态
        错误=自身.错误#当前反馈
        if 错误 is None:#没有
            反馈文=''#空
        elif '文' in 错误:#线路原文
            反馈文=错误['文']#原样
        elif 错误.get('键')=='error.incomplete':#没答完
            反馈文='请先完成这道问题。'#中文表
        elif 错误.get('键')=='error.unanswered':#这一题还空着
            反馈文='请选择一个选项或填写自定义答案。'#中文表
        elif 错误.get('键')=='error.unavailable':#还不能送
            反馈文='当前无法提交，请稍候再试。'#中文表
        elif 错误.get('键')=='error.resubmit':#要再送一次
            反馈文='回答未送达，工作已继续，请再提交一次。'#中文表
        elif 错误.get('键')=='status.sent':#面板没关上
            反馈文='回答已发送；面板未能关闭。'#中文表
        else:#没有这句
            反馈文=''#空
        反馈.textContent=反馈文#句子
        脚.appendChild(反馈)#错误
        if not 自身.审阅中:#还能送出
            行=模块节点(文档,'div',样式模块,'footerActions')#按钮
            跳=按钮({#跳过
                'window':窗口,
                'variant':'outline',
                'disabled':自身.忙碌 is not None,
                'onClick':自身.跳过,
                'children':'跳过',
            })
            行.appendChild(跳.渲染())#跳过
            最后=自身.下标==len(自身.问题列表)-1#最后一题
            if 自身.忙碌=='answer':#正在送
                文='正在提交…'#中文表
            elif 最后:#送出
                文='提交'#中文表
            else:#翻页
                文='下一题'#中文表
            禁用=自身.忙碌 is not None or not 自身.已答(自身.草稿[自身.下标]) or (最后 and not 自身.可提交)#不能点
            进=按钮({#继续
                'window':窗口,
                'variant':'primary',
                'disabled':禁用,
                'onClick':自身.继续,
                'children':文,
            })
            行.appendChild(进.渲染())#继续
            脚.appendChild(行)#按钮
        自身.卡.appendChild(脚)#页脚
        自身.脚=脚#留下


class 提问撰写器:
    '作曲链上的提问入口。计划审阅和逐题回答互不抢同一条请求'
    def __new__(类,属性=None):
        '有计划意图就画审阅卡，否则画逐题回答'
        待=属性['matched']#选中的卡片
        审阅=计划审阅于(待.questions)#尝试收窄
        if 审阅 is None:#通用流程
            return 提问流.呈现(属性)#逐题
        带审阅=dict(属性)#拷贝
        带审阅['review']=审阅#交给审阅卡
        return 计划审阅面板.呈现(带审阅)#审阅卡
