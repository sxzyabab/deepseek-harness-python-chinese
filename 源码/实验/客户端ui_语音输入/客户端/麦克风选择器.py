'选择输入设备，并在页面还开着时预览电平'
from ....客户端.模块.客户端.通告 import 取握手窗口
import math#电平格数
import os#样式文件位置
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块样式
from ..异常 import 录制错误#没有媒体设备
from .音频 import 逐项#页面数组
from .故障文本 import 失败文本#失败句子

__all__=['麦克风选择器','输入电平']#设备行和电平

样式路径=os.path.join(os.path.dirname(__file__),'语音输入.module.css')#本目录样式
样式模块='VoiceInput'#与样式表对应的模块名


def 取(对象,键,默认=None):
    '字典用键，对象用同名属性'
    if 对象 is None:#没有
        return 默认#缺省
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else 默认#键
    return getattr(对象,键,默认)#属性


def 全选(值):
    '选择整份快照'
    return 值#原样


def 取窗口(属性):
    '调用方窗口优先，否则用当前页'
    if isinstance(属性,dict) and 属性.get('window') is not None:#份额里带了窗口
        return 属性['window']#调用方窗口
    return 取握手窗口()#当前页


def 设类(节点,*类名):
    '挂上官方类名，让模块样式生效'
    留下=[]#非空类名
    for 名 in 类名:#逐个
        if isinstance(名,str) and 名!='':#有内容
            留下.append(名)#留下
    节点.className=' '.join(留下)#类名保持原文
    return 标样式模块(节点,样式模块)#模块属性


class 输入电平:
    '八格电平。不录音，只显示当前预览的响度'
    def __init__(自身,属性=None):
        '记下预览采集'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#格子外层
        自身.格=[]#八格
        自身.帧=None#动画编号
        自身.录音=None#当前动画对应的采集
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的预览'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 拆除(自身):
        '停掉动画'
        if 自身.帧 is not None:#还在请求帧
            取窗口(自身.属性).cancelAnimationFrame(自身.帧)#取消
            自身.帧=None#记下

    def 开动画(自身):
        '按帧点亮格子'
        窗口=取窗口(自身.属性)#窗口
        录音=自身.属性.get('recording')#预览
        if 自身.帧 is not None and 自身.录音 is 录音:#同一只
            return#继续
        自身.拆除()#停上一轮
        自身.录音=录音#记下

        def 画(现在=None):
            '按分贝点亮前几格'
            振幅=0#静音
            if 录音 is not None:#有预览
                振幅=录音.振幅()#RMS
            if 振幅<0.00001:#避免对数零
                振幅=0.00001#下限
            分贝=20*math.log10(振幅)#分贝
            比例=(分贝+60)/60#映到 0 到 1
            if 比例<0:#太小
                比例=0#零
            if 比例>1:#太大
                比例=1#满
            数量=int(math.ceil(比例*len(自身.格)))#点亮几格
            序号=0#下标
            for 格 in 自身.格:#每一格
                格.setAttribute('data-active','true' if 序号<数量 else 'false')#是否点亮
                序号=序号+1#下一格
            自身.帧=窗口.requestAnimationFrame(画)#下一帧

        自身.帧=窗口.requestAnimationFrame(画)#开始

    def 渲染(自身):
        '画出八格'
        窗口=取窗口(自身.属性)#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        if 自身.根 is None:#还没有
            根=文档.createElement('span')#外层
            设类(根,'inputLevel')#模块类
            根.setAttribute('role','img')#给读屏
            自身.格=[]#清空
            序号=0#下标
            while 序号<8:#八格
                格=文档.createElement('span')#一格
                根.appendChild(格)#挂上
                自身.格.append(格)#记下
                序号=序号+1#下一格
            自身.根=根#留下
        自身.根.setAttribute('aria-label',自身.属性.get('label') or '')#麦克风输入电平
        自身.开动画()#按当前预览画
        return 自身.根#节点


class 麦克风选择器:
    '列出输入设备，并在页面可见时预览电平'
    def __init__(自身,属性=None):
        '记下已选设备，并订上偏好'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.窗口=取窗口(自身.属性)#窗口
        自身.根=None#整行
        自身.已选={'id':'','label':''}#这一轮效果看到的选择
        自身.设备列表=[]#选项
        自身.预览=None#正在预览的采集
        自身.错误=None#失败
        自身.采集=None#效果里的那一次
        自身.媒体=None#mediaDevices
        自身.寿命=None#效果寿命
        自身.枚举=0#丢掉过期的枚举
        自身.已挂标识=None#效果对应的设备 id
        自身.已挂创建=None#效果对应的工厂
        自身.已听设备=False#devicechange
        自身.已听可见=False#visibilitychange
        自身.绘制中=False#避免重入
        自身.待重画=False#绘制中又来了一次
        自身.退订=[]#偏好订阅
        自身.电平=输入电平({'window':自身.窗口,'recording':None,'label':'麦克风输入电平'})#八格
        初选=自身.读已选()#当前偏好
        初标识=取(初选,'id') or ''#id
        自身.设备列表=[{'id':初标识,'label':'' if 初标识=='' else (取(初选,'label') or '')}]#先放当前这一只
        钩=自身.属性.get('useMicrophoneDevice')#偏好钩子
        if callable(钩) and hasattr(钩,'_subscribe'):#能订
            自身.退订.append(钩._subscribe(自身.源变了))#换了设备就重画
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的份额'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        自身.窗口=取窗口(自身.属性)#窗口

    def 源变了(自身):
        '偏好变了就重画'
        if 自身.绘制中:#正在画
            自身.待重画=True#等结束
            return#不重入
        自身.渲染()#重画

    def 拆除(自身):
        '退订并停掉预览'
        for 退 in 自身.退订:#逐个
            if callable(退):#是函数
                退()#退订
        自身.退订=[]#清空
        自身.拆效果()#停预览
        自身.电平.拆除()#停动画

    def 读已选(自身):
        '读浏览器记住的设备'
        钩=自身.属性.get('useMicrophoneDevice')#钩子
        if callable(钩) is False:#没有
            return {'id':'','label':''}#系统默认
        已选=钩(全选)#快照
        if isinstance(已选,dict) is False:#不是字典
            return {'id':'','label':''}#系统默认
        return 已选#快照

    def 已中止(自身):
        '这一轮效果是否已经停'
        if 自身.寿命 is None:#还没挂
            return True#当成停了
        return 自身.寿命.signal.aborted is True#已中止

    def 释放(自身):
        '关掉预览。关闭失败不挡住刷新'
        采集=自身.采集#这一次
        自身.采集=None#先摘掉
        if 采集 is None:#没有
            return#完
        try:#停轨
            采集.拆除()#释放
        except Exception as 关闭错误:#关闭失败
            关闭错误=None#不挡住后面的刷新

    def 失败(自身,失败):
        '记下预览失败'
        if 自身.已中止():#效果已经停
            return#不再画
        自身.错误={'failure':失败}#留给失败文本
        自身.渲染()#重画

    def 取得(自身):
        '打开预览。中断后重新枚举'
        创建=自身.已挂创建#工厂
        if callable(创建) is False:#没有
            return#不能预览
        录音=创建()#一次采集
        自身.采集=录音#记下

        def 中断了(失败):
            '预览中途设备断开'
            if 自身.采集 is not 录音 or 自身.已中止():#不是这一次
                return#忽略
            自身.释放()#关掉
            自身.预览=None#没有电平
            自身.失败(失败)#显示
            自身.刷新()#重新枚举

        try:#只要分析器，不录音
            录音.预览(中断了)#打开麦克风
            if 自身.采集 is not 录音 or 自身.已中止():#已经换了
                return#丢掉
            自身.预览=录音#显示电平
            自身.错误=None#清掉错误
            自身.渲染()#重画
            自身.刷新()#拿到标签后再列一次
        except Exception as 失败:#没打开
            if 自身.采集 is not 录音 or 自身.已中止():#已经换了
                return#丢掉
            自身.释放()#关掉
            自身.预览=None#没有电平
            自身.失败(失败)#显示

    def 刷新(自身):
        '重新列出音频输入'
        自身.枚举=自身.枚举+1#新的一轮
        请求=自身.枚举#这一轮
        已选=自身.已选#效果开始时的选择
        标识=取(已选,'id') or ''#选中的 id
        try:#向浏览器要设备
            if 自身.媒体 is None:#没有媒体设备
                raise 录制错误('unavailable')#不能列
            输入=[]#音频输入
            for 设备 in 逐项(自身.媒体.enumerateDevices()):#全部设备
                if 取(设备,'kind')=='audioinput':#只要麦克风
                    输入.append(设备)#留下
            if 自身.已中止() or 请求!=自身.枚举:#过期
                return#丢掉
            已知=len(输入)==0#一台都没有也算已知
            if 已知 is False:#还有设备
                for 设备 in 输入:#看有没有标签
                    if 取(设备,'label') not in ('',None):#已经授权，标签可见
                        已知=True#缺失才能判断
                        break#够了
            缺=False#选中的还在不在
            if 标识=='':#系统默认
                缺=len(输入)==0#一台都没有
            elif 已知:#标签已经可见
                还在=False#默认不在
                for 设备 in 输入:#找这只
                    if 取(设备,'deviceId')==标识:#还在
                        还在=True#在
                        break#完
                缺=还在 is False#不在
            系统=None#default 那条
            for 设备 in 输入:#找系统默认
                if 取(设备,'deviceId')=='default':#系统行
                    系统=设备#记下
                    break#完
            活动默认=None#正在预览的系统设备
            if 标识=='' and 自身.采集 is not None:#跟随系统且已经打开
                活动默认=自身.采集.设备信息()#实际打开的那只
            组=取(活动默认,'groupId') or 取(系统,'groupId')#设备组
            物理=None#组里真正的麦克风
            if 组:#有组
                for 设备 in 输入:#找同组、不是 default 也不是 communications
                    设备标识=取(设备,'deviceId')#id
                    if 取(设备,'groupId')==组 and 设备标识!='default' and 设备标识!='communications':#物理设备
                        物理=设备#记下
                        break#完
            默认标签=取(物理,'label') or 取(活动默认,'label') or 取(系统,'label') or ''#系统行的名字
            选项=[{'id':'','label':默认标签,'unavailable':len(输入)==0}]#系统默认永远在第一行
            for 设备 in 输入:#其余设备
                设备标识=取(设备,'deviceId')#id
                if 设备标识 not in ('',None,'default'):#去掉空的和系统行
                    选项.append({'id':设备标识,'label':取(设备,'label') or ''})#一只
            def 合并(先前):
                '选中的设备不在列表里时，插回原来的位置'
                下一=list(选项)#拷贝
                if 标识!='' and any(项.get('id')==标识 for 项 in 下一) is False:#列表里没有
                    已知设备=None#上次的标签
                    位置=-1#上次的位置
                    序号=0#下标
                    for 项 in 先前:#找上次
                        if 项.get('id')==标识:#就是
                            已知设备=项#留下标签
                            位置=序号#位置
                            break#完
                        序号=序号+1#下一项
                    插入于=位置 if 位置>1 else 1#至少插在系统行后面
                    if 位置<1:#上次不在或就在最前
                        插入于=1#系统行后面
                    下一.insert(插入于,{#插回去
                        'id':标识,#原来的 id
                        'label':'' if 已知设备 is None else (已知设备.get('label') or ''),#上次的名字
                        'unavailable':缺,#现在不可用
                    })
                return 下一#新列表
            自身.设备列表=合并(自身.设备列表)#先写上
            if 缺:#选中的不在了
                自身.释放()#关掉预览
                自身.预览=None#没有电平
                自身.错误=None#不把缺失显示成别的错误
                自身.渲染()#重画
            elif 自身.窗口.document.hidden is not True and 自身.采集 is None:#页面可见且还没打开
                自身.取得()#开始预览
            else:#只更新列表
                自身.渲染()#重画
        except Exception as 失败:#列设备失败
            if 请求==自身.枚举:#还是这一轮
                自身.失败(失败)#显示

    def 设备变化(自身,事件=None):
        '插拔设备后重新列举'
        自身.刷新()#重新列

    def 可见变化(自身,事件=None):
        '页面隐藏就停预览，回来再打开'
        if 自身.窗口.document.hidden:#隐藏
            自身.释放()#关掉
            自身.预览=None#没有电平
            自身.渲染()#重画
            return#完
        自身.设备变化()#重新列并按需要打开

    def 挂效果(自身,已选,创建):
        '按当前设备和工厂开始列举、预览'
        自身.拆效果()#先停上一轮
        自身.已选=已选#这一轮看到的选择
        自身.已挂标识=取(已选,'id') or ''#id
        自身.已挂创建=创建#工厂
        自身.媒体=自身.窗口.navigator.mediaDevices#媒体设备
        自身.寿命=自身.窗口.AbortController()#这一轮的取消
        自身.枚举=0#重新计数
        自身.采集=None#还没打开
        自身.预览=None#没有电平
        自身.错误=None#清掉
        if 自身.媒体 is not None:#有媒体设备
            自身.媒体.addEventListener('devicechange',自身.设备变化)#插拔
            自身.已听设备=True#记下
        自身.窗口.document.addEventListener('visibilitychange',自身.可见变化)#隐藏
        自身.已听可见=True#记下
        自身.刷新()#先列一次

    def 拆效果(自身):
        '停掉列举和预览'
        if 自身.寿命 is not None:#还活着
            自身.寿命.abort()#之后的回调丢掉
        if 自身.已听设备 and 自身.媒体 is not None:#还听着插拔
            自身.媒体.removeEventListener('devicechange',自身.设备变化)#摘掉
        if 自身.已听可见:#还听着可见性
            自身.窗口.document.removeEventListener('visibilitychange',自身.可见变化)#摘掉
        自身.已听设备=False#记下
        自身.已听可见=False#记下
        自身.释放()#关掉预览
        自身.预览=None#没有电平
        自身.寿命=None#清掉
        自身.已挂标识=None#允许下一轮再挂
        自身.已挂创建=None#同上

    def 改设备(自身,事件):
        '把选中的 id 和标签交给偏好'
        目标=取(事件,'target')#选择框
        值=取(目标,'value')#id
        if 值 is None:#没有
            值=''#系统默认
        设备=None#选项
        for 项 in 自身.可见选项(自身.读已选()):#在当前可见列表里找
            if 项.get('id')==值:#就是
                设备=项#记下
                break#完
        if 设备 is None:#列表里没有
            return#不写
        选择=自身.属性.get('selectMicrophone')#写入偏好
        if callable(选择):#有
            选择({'id':设备.get('id') or '','label':'' if 设备.get('id') in ('',None) else (设备.get('label') or '')})#空 id 不留标签

    def 可见选项(自身,已选):
        '不可用的设备只在它正是当前选择或系统行时留下'
        标识=取(已选,'id') or ''#当前 id
        结果=[]#可见
        for 设备 in 自身.设备列表:#逐个
            if 设备.get('unavailable') is not True or 设备.get('id')==标识 or 设备.get('id')=='':#留下
                结果.append(设备)#可见
        return 结果#列表

    def 渲染(自身):
        '重入时记一笔'
        if 自身.绘制中:#正在画
            自身.待重画=True#等结束
            return 自身.根#先交出现在的
        自身.绘制中=True#占住
        try:#画出
            return 自身.画出()#节点
        finally:#放开
            自身.绘制中=False#结束
            if 自身.待重画:#错过了一次
                自身.待重画=False#清掉
                自身.渲染()#再画

    def 画出(自身):
        '设备选择框。有预览且设备还在时显示电平'
        已选=自身.读已选()#当前偏好
        创建=自身.属性.get('createRecording')#工厂
        标识=取(已选,'id') or ''#id
        if 自身.已挂标识!=标识 or 自身.已挂创建 is not 创建:#选择或工厂变了
            自身.挂效果(已选,创建)#重新列举
        窗口=自身.窗口#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        选项=自身.可见选项(已选)#可见行
        缺失=False#当前这只是否不可用
        for 设备 in 选项:#找当前
            if 设备.get('id')==标识:#就是
                缺失=设备.get('unavailable') is True#不可用
                break#完
        行=文档.createElement('div')#整行
        设类(行,'deviceRow')#网格
        行.setAttribute('data-voice-input-device','')#标记，值保持空
        标签=文档.createElement('label')#输入设备
        标签.setAttribute('for','voice-input-device')#对应选择框
        标签.textContent='输入设备'#中文表
        行.appendChild(标签)#标签
        字段=文档.createElement('span')#选择框和电平
        设类(字段,'deviceField')#相对定位
        选择=文档.createElement('select')#设备
        选择.id='voice-input-device'#与标签对应
        选择.value=标识#受控
        if 自身.预览 is not None:#给电平留出右侧空白
            选择.className='deviceSelectMeter'#类名保持原文
            标样式模块(选择,样式模块)#模块
        选择.addEventListener('change',自身.改设备)#改偏好
        序号=0#选项序号
        for 设备 in 选项:#每一只
            项=文档.createElement('option')#一项
            项.value=设备.get('id') or ''#id
            if 设备.get('id')=='':#系统行
                if 设备.get('label'):#知道默认设备的名字
                    名字='系统默认（{name}）'.replace('{name}',str(设备.get('label')))#中文表
                else:#还不知道
                    名字='系统默认'#中文表
            else:#具体设备
                标签字=设备.get('label') or ''#浏览器给的名字
                if 标签字=='' and 设备.get('id')==标识:#用偏好里留下的名字
                    标签字=取(已选,'label') or ''#上次的标签
                if 标签字=='':#仍然没有名字
                    if 序号>0:#不是第一行
                        名字='麦克风 {number}'.replace('{number}',str(序号))#中文表
                    else:#当前选中但没有名字
                        名字='麦克风'#中文表
                else:#有名字
                    名字=标签字#原样
            if 设备.get('unavailable') is True:#不可用
                名字=名字+' — '+'不可用'#中文表
                项.disabled=True#不能选
            项.textContent=名字#显示
            选择.appendChild(项)#挂上
            序号=序号+1#下一项
        字段.appendChild(选择)#选择框
        if 自身.预览 is not None and 缺失 is False:#可以显示电平
            表=文档.createElement('span')#叠在选择框右侧
            设类(表,'deviceMeter')#不挡点击
            自身.电平.更新({'window':窗口,'recording':自身.预览,'label':'麦克风输入电平'})#中文表
            表.appendChild(自身.电平.渲染())#八格
            字段.appendChild(表)#挂上
        行.appendChild(字段)#字段
        if 自身.错误 is not None:#预览失败
            错=文档.createElement('span')#一句
            设类(错,'deviceError')#错误色
            错.setAttribute('role','alert')#提醒
            错.textContent=失败文本(自身.错误.get('failure'))#中文
            行.appendChild(错)#挂上
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住
            旧.remove()#拆掉
        自身.根=行#留下
        if 父 is not None:#挂回
            父.appendChild(行)#挂上
        return 行#节点

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画
