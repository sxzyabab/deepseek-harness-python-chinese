'提供方的准备步骤，以及会保存的识别偏好'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件位置
import time#已等待秒数
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块样式
from ....客户端.ui_基础界面组件.按钮 import 按钮#准备和取消
from ....客户端.ui_基础界面组件.状态点 import 状态点#步骤点
from ....客户端.ui_基础界面组件.icons import 图标下箭头描边常规#收起时的箭头
from .音频 import 逐项#页面数组
from .麦克风选择器 import 麦克风选择器#输入设备

__all__=['准备卡片','语音准备工作','下载进度','准备失败','准备披露']#详情槽和内部界面

样式路径=os.path.join(os.path.dirname(__file__),'语音输入.module.css')#本目录样式
样式模块='VoiceInput'#与样式表对应的模块名


def 全选快照(值):
    '选择整份就绪快照'
    return 值#原样


def 取(对象,键,默认=None):
    '字典用键，对象用同名属性'
    if 对象 is None:#没有
        return 默认#缺省
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else 默认#键
    return getattr(对象,键,默认)#属性


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


def 准备语气(态):
    '步骤点的颜色'
    阶段=取(态,'phase')#准备阶段
    if 阶段=='ready' or 阶段=='standby':#已经能用
        return 'done'#完成
    if 阶段=='failed':#失败
        return 'error'#错误
    if 阶段=='unprepared' or 阶段=='cancelled':#还没开始或已取消
        return 'idle'#空闲
    return 'ongoing'#进行中


def 量文本(值):
    '整数不带小数点，和字符串化的数字一样'
    数=float(值)#数字
    if 数==int(数):#整数值
        return str(int(数))#不带 .0
    return str(数)#保留小数


def 套入(模板,表):
    '把花括号占位换成具体文字'
    句=模板#中文模板
    for 名 in 表:#每个占位
        句=句.replace('{'+名+'}',str(表[名]))#换上
    return 句#句子


def 步骤句(种类,名称):
    '准备步骤的中文名'
    if 种类=='check':#检查
        return '检查本地资源'#中文表
    if 种类=='model':#识别模型
        return '准备语音识别模型'#中文表
    if 种类=='vad':#检测模型
        return '准备语音检测模型'#中文表
    if 种类=='verify':#校验
        return '校验模型文件'#中文表
    if 种类=='load':#加载
        return 套入('加载 {name}',{'name':'' if 名称 is None else 名称})#中文表
    return '' if 种类 is None else str(种类)#没有对应句子时留空


class 下载进度:
    '已知总大小时画出进度条'
    def __init__(自身,属性=None):
        '记下准备状态'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#progress
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的状态'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 拆除(自身):
        '从页面拿掉'
        if 自身.根 is not None:#还在
            自身.根.remove()#拆掉
            自身.根=None#记下

    def 渲染(自身):
        '只有正在下载且知道总字节时才显示'
        态=自身.属性.get('state')#准备状态
        窗口=取窗口(自身.属性)#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        总计=取(态,'totalBytes')#总字节
        if 取(态,'phase')!='downloading' or 总计 is None:#不用画
            自身.拆除()#拿掉旧的
            return None#没有
        条=文档.createElement('progress')#进度
        设类(条,'progress')#模块类
        条.setAttribute('aria-label','下载进度')#中文表
        条.value=取(态,'completedBytes')#已完成
        条.max=总计#总量
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住
            旧.remove()#拆掉
        自身.根=条#留下
        if 父 is not None:#挂回
            父.appendChild(条)#挂上
        return 条#节点


class 准备失败:
    '下载失败时写出原因、建议、来源和错误码'
    def __init__(自身,属性=None):
        '记下失败状态'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#说明
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的失败'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 拆除(自身):
        '从页面拿掉'
        if 自身.根 is not None:#还在
            自身.根.remove()#拆掉
            自身.根=None#记下

    def 下载句(自身,原因,资源,状态码):
        '按失败原因取中文表里的下载句'
        表={'resource':'' if 资源 is None else 资源,'status':'' if 状态码 is None else 状态码}#占位
        if 原因=='network':#连不上
            return 套入('无法下载 {resource}：连接下载服务失败。',表)#中文表
        if 原因=='dns':#解析失败
            return 套入('无法下载 {resource}：无法解析下载地址。',表)#中文表
        if 原因=='timeout':#超时
            return 套入('下载 {resource} 超时。',表)#中文表
        if 原因=='certificate':#证书
            return 套入('无法下载 {resource}：安全连接的证书校验失败。',表)#中文表
        if 原因=='http':#HTTP 状态
            return 套入('无法下载 {resource}：下载服务返回 HTTP {status}。',表)#中文表
        if 原因=='integrity':#校验
            return 套入('{resource} 下载不完整或文件校验失败。',表)#中文表
        if 原因=='storage':#磁盘或权限
            return 套入('无法保存 {resource}：磁盘空间不足或没有写入权限。',表)#中文表
        return 套入('准备 {resource} 失败。',表)#未知原因

    def 建议句(自身,原因):
        '按失败原因取中文表里的建议'
        if 原因=='network':#网络
            return '请检查运行 DSH 的机器能否访问下载来源及其模型下载服务；如需代理，请在该机器上配置后重试。'#中文表
        if 原因=='dns':#DNS
            return '请检查运行 DSH 的机器的 DNS 和代理设置，确认可以解析下载来源的域名后重试。'#中文表
        if 原因=='timeout':#超时
            return '请检查运行 DSH 的机器的网络或代理连接，稍后重试。已下载并通过校验的文件会保留。'#中文表
        if 原因=='certificate':#证书
            return '请检查运行 DSH 的机器的系统时间、受信任证书和代理设置后重试。'#中文表
        if 原因=='http':#HTTP
            return '请确认下载地址可用、代理可正常连接下载服务，或稍后重试。'#中文表
        if 原因=='integrity':#校验
            return '请重试下载。已完成并通过校验的其他文件会保留。'#中文表
        if 原因=='storage':#磁盘
            return '请检查运行 DSH 的机器的剩余磁盘空间，以及模型目录的写入权限后重试。'#中文表
        return '请检查运行 DSH 的机器的网络、磁盘空间和模型目录权限后重试。'#未知

    def 渲染(自身):
        '没有下载分类时只显示准备失败'
        态=自身.属性.get('state')#失败状态
        窗口=取窗口(自身.属性)#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        失败=取(态,'download')#下载分类
        if 失败 is None:#普通失败
            根=文档.createElement('p')#一段
            设类(根,'preparationError')#错误色
            根.setAttribute('role','alert')#提醒
            根.textContent=套入('准备失败：{message}',{'message':取(态,'message') or ''})#中文表
        else:#分类失败
            根=文档.createElement('div')#一组
            设类(根,'downloadFailure')#网格
            根.setAttribute('role','alert')#提醒
            原因=取(失败,'reason')#原因
            段=文档.createElement('p')#原因
            设类(段,'preparationError')#错误色
            段.textContent=自身.下载句(原因,取(失败,'resource'),取(失败,'status'))#中文
            根.appendChild(段)#挂上
            建议=文档.createElement('p')#建议
            建议.textContent=自身.建议句(原因)#中文
            根.appendChild(建议)#挂上
            来源=文档.createElement('small')#来源
            设类(来源,'metric')#次要
            来源.textContent=套入('下载来源：{source}',{'source':取(失败,'source') or ''})#中文表
            根.appendChild(来源)#挂上
            错误码=取(失败,'code')#可选
            if 错误码:#有错误码
                码=文档.createElement('small')#错误码
                设类(码,'metric')#次要
                码.textContent=套入('错误码：{code}',{'code':错误码})#中文表
                根.appendChild(码)#挂上
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住
            旧.remove()#拆掉
        自身.根=根#留下
        if 父 is not None:#挂回
            父.appendChild(根)#挂上
        return 根#节点


class 准备披露:
    '准备步骤的展开行。整行可点，收起时不把图标换成箭头'
    def __init__(自身,属性=None):
        '记下开合和内容'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#整块
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的开合'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 拆除(自身):
        '从页面拿掉'
        if 自身.根 is not None:#还在
            自身.根.remove()#拆掉
            自身.根=None#记下

    def 点行(自身,事件=None):
        '整行点击时切换'
        切换=自身.属性.get('onToggle')#回调
        if callable(切换):#有
            切换()#切换

    def 按键(自身,事件):
        '回车或空格也切换'
        键=取(事件,'key')#键名
        if 键!='Enter' and 键!=' ':#不是这两个
            return#忽略
        if hasattr(事件,'preventDefault'):#能取消默认
            事件.preventDefault()#不要滚动
        自身.点行(事件)#切换

    def 渲染(自身):
        '展开时标题前是上箭头，收起时是状态点'
        窗口=取窗口(自身.属性)#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        打开=自身.属性.get('open') is True#展开
        可展=自身.属性.get('expandable') is True#有步骤
        根=文档.createElement('div')#整块
        根.style.display='flex'#纵向
        根.style.flexDirection='column'#标题在上
        根.style.width='100%'#铺满
        根.style.minWidth='0'#允许缩小
        if 打开:#展开标记
            根.setAttribute('data-open','true')#与上游 data-open 一致
        头=文档.createElement('div')#标题行外层
        头.style.display='flex'#横向
        头.style.alignItems='center'#居中
        头.style.minWidth='0'#允许缩小
        行=文档.createElement('div')#可点的行
        设类(行,'summaryRow')#模块类
        行.style.display='flex'#类名本身没有 display
        行.style.alignItems='center'#居中
        行.style.flex='1'#占满
        行.style.minWidth='0'#允许缩小
        行.style.color='var(--dsw-alias-label-tertiary)'#次要文字
        if 可展:#整行可点
            行.style.cursor='pointer'#手型
            行.setAttribute('role','button')#按钮
            行.setAttribute('tabIndex','0')#可聚焦
            行.setAttribute('aria-expanded','true' if 打开 else 'false')#开合
            行.setAttribute('data-expandable','true')#可展开
            行.addEventListener('click',自身.点行)#点击
            行.addEventListener('keydown',自身.按键)#键盘
        前=文档.createElement('span')#图标位
        前.style.display='inline-flex'#居中图标
        前.style.flex='none'#不伸缩
        前.style.marginRight='6px'#与标题的间距
        前.style.alignItems='center'#垂直居中
        if 打开:#展开后换成上箭头。共享图标没有常规描边的这一只
            上图=文档.createElement('svg')#图标
            上图.setAttribute('width','14')#宽
            上图.setAttribute('height','14')#高
            上图.setAttribute('viewBox','0 0 16 16')#坐标
            上图.setAttribute('fill','none')#不填充
            上图.setAttribute('aria-hidden','true')#装饰
            上图.setAttribute('stroke-width','1')#常规描边
            上路=文档.createElement('path')#箭头
            上路.setAttribute('d','M12 10L8.70711 6.70711C8.31658 6.31658 7.68342 6.31658 7.29289 6.70711L4 10')#路径
            上路.setAttribute('stroke','currentColor')#跟文字颜色
            上图.appendChild(上路)#挂上
            前.appendChild(上图)#上箭头
        else:#收起时用状态点
            图标=自身.属性.get('icon')#调用方画好的点
            if 图标 is not None:#有
                前.appendChild(图标)#放上
        行.appendChild(前)#图标
        题=文档.createElement('span')#标题
        设类(题,'summaryTitle')#模块类
        题.style.fontSize='var(--dsh-content-font-size-secondary, 13px)'#次级字号
        题.style.lineHeight='calc(24px + var(--dsh-content-font-delta, 0px))'#行高
        题.style.color='inherit'#跟着行
        题.textContent=自身.属性.get('title') or ''#标题
        行.appendChild(题)#标题
        if 打开 is False:#收起时显示度量
            for 子 in 自身.属性.get('collapsed') or []:#度量和下箭头
                if 子 is not None:#有节点
                    行.appendChild(子)#挂上
        头.appendChild(行)#行
        根.appendChild(头)#头
        if 打开:#展开体
            体=自身.属性.get('children')#步骤列表
            if 体 is not None:#有
                根.appendChild(体)#挂上
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住
            旧.remove()#拆掉
        自身.根=根#留下
        if 父 is not None:#挂回
            父.appendChild(根)#挂上
        return 根#节点


class 准备卡片:
    '一个识别器的资源就绪和准备按钮'
    def __init__(自身,属性=None):
        '记下展开、下载源和提交状态'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.窗口=取窗口(自身.属性)#窗口
        自身.根=None#整节
        自身.已展开=False#步骤列表
        自身.现在=int(time.time()*1000)#用来算已等待
        自身.错误=''#这一次动作的失败
        自身.源=''#这次选择的下载源
        自身.提交中=False#按钮禁用
        自身.计时=None#每秒刷新
        自身.绘制中=False#避免重入
        自身.待重画=False#绘制中又来了一次
        自身.披露=准备披露({'window':自身.窗口})#步骤行
        自身.失败视图=准备失败({'window':自身.窗口})#失败说明
        自身.步骤进度=下载进度({'window':自身.窗口})#步骤里的进度
        自身.总进度=下载进度({'window':自身.窗口})#收起时的进度
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的提供方'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        自身.窗口=取窗口(自身.属性)#窗口

    def 拆除(自身):
        '停掉计时并拆掉子界面'
        if 自身.计时 is not None:#还在走
            自身.窗口.clearInterval(自身.计时)#停
            自身.计时=None#记下
        自身.披露.拆除()#步骤行
        自身.失败视图.拆除()#失败
        自身.步骤进度.拆除()#进度
        自身.总进度.拆除()#进度

    def 切展开(自身):
        '展开或收起步骤'
        自身.已展开=自身.已展开 is False#翻转
        自身.渲染()#重画

    def 改源(自身,事件):
        '记下这一次要使用的下载源'
        目标=取(事件,'target')#选择框
        自身.源=取(目标,'value') or ''#值
        自身.渲染()#重画

    def 执行(自身,动作):
        '跑一项动作。失败写到错误行，无论成败都结束提交'
        自身.错误=''#先清掉
        自身.提交中=True#禁用按钮
        自身.渲染()#重画
        try:#调用宿主
            动作()#准备或取消
        except Exception as 失败:#失败
            自身.错误=str(失败)#留下消息
        自身.提交中=False#结束
        自身.渲染()#重画

    def 开始准备(自身):
        '按所选源启动或加入准备'
        提供方=自身.属性.get('provider')#这一家
        标识=取(提供方,'id')#提供方 id

        def 动作():
            '空源表示自动选择'
            if 自身.所选源()=='':#自动
                自身.属性['prepare'](标识)#不带选项
            else:#指定源
                自身.属性['prepare'](标识,{'downloadSource':自身.所选源()})#只从这一源

        自身.执行(动作)#跑

    def 取消这一次(自身):
        '显式取消准备'
        标识=取(自身.属性.get('provider'),'id')#提供方 id

        def 动作():
            '调用取消'
            自身.属性['cancelPreparation'](标识)#取消

        自身.执行(动作)#跑

    def 所选源(自身):
        '合法源。只有一个源时用那一个，否则空表示自动'
        来源=自身.来源列表()#可选源
        if 自身.源 in 来源:#还有效
            return 自身.源#用它
        if len(来源)==1:#只有一个
            return 来源[0]#用它
        return ''#自动

    def 来源列表(自身):
        '复制成列表，便于判断选中项'
        原始=取(自身.属性.get('provider'),'downloadSources')#可能没有
        return [项 for 项 in 逐项(原始)]#列表

    def 同步计时(自身,准备中,开始于):
        '准备过程中每秒刷新已等待'
        需要=准备中 and 开始于 is not None#要走表
        if 需要 and 自身.计时 is None:#还没开始

            def 滴答():
                '更新现在并重画'
                自身.现在=int(time.time()*1000)#毫秒
                自身.渲染()#重画

            自身.计时=自身.窗口.setInterval(滴答,1000)#每秒
        if 需要 is False and 自身.计时 is not None:#已经结束
            自身.窗口.clearInterval(自身.计时)#停
            自身.计时=None#记下

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
        '估算、步骤、下载源和动作'
        提供方=自身.属性.get('provider')#这一家
        态=取(提供方,'preparation')#准备状态
        阶段=取(态,'phase')#阶段
        名称=取(提供方,'name') or ''#显示名
        已连接=自身.属性.get('connected') is True#远程还连着
        窗口=自身.窗口#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        当前步=None#正在跑或刚失败的一步
        for 步 in 逐项(取(态,'steps')):#步骤
            步态=取(步,'status')#状态
            if 步态=='running' or 步态=='failed' or 步态=='cancelled':#当前
                当前步=步#这一步
                break#只要第一个
        准备中=准备语气(态)=='ongoing'#还在进行
        开始于=取(当前步,'startedAt') if 当前步 is not None else None#步骤上的开始时间
        if 开始于 is None and isinstance(态,dict) and 'startedAt' in 态:#状态自己带了
            开始于=态['startedAt']#用它
        elif 开始于 is None and 态 is not None and isinstance(态,dict) is False:#对象
            开始于=getattr(态,'startedAt',None)#属性
        自身.同步计时(准备中,开始于)#每秒
        if 阶段=='downloading':#下载字节
            已完成数=取(态,'completedBytes') or 0#已下
            已完成=format(已完成数/1000000,'.1f')#兆字节，一位小数
            总计=取(态,'totalBytes')#总量
            if 总计 is None:#不知道总大小
                度量=套入('已下载 {completed} MB',{'completed':已完成})#中文表
            else:#知道总量
                百分比=str(int(已完成数/总计*100))#向下取整
                度量=套入('下载：{completed} / {total} MB，{percent}%',{#中文表
                    'completed':已完成,#已下
                    'total':format(总计/1000000,'.1f'),#总量
                    'percent':百分比,#百分比
                })
        elif 准备中 and 开始于 is not None:#已等待
            秒=int((自身.现在-开始于)/1000)#秒
            if 秒<0:#时钟回拨
                秒=0#不能为负
            度量=套入('已等待 {seconds} 秒',{'seconds':秒})#中文表
        else:#没有度量
            度量=''#空
        if 已连接 is False:#正在重连
            摘要='正在连接语音服务…'#中文表
        elif 准备中 and 当前步 is not None:#当前步骤
            摘要=步骤句(取(当前步,'kind'),名称)#步骤名
        elif 阶段=='downloading':#下载
            摘要='下载中'#中文表
        elif 阶段=='failed':#失败
            摘要='准备失败'#中文表
        elif 阶段=='ready' and 取(提供方,'location')=='cloud':#云端已就绪
            摘要='云端语音识别已就绪。'#中文表
        elif 阶段=='unprepared':#未准备
            摘要='首次使用需要下载本地识别模型。'#中文表
        elif 阶段=='checking':#检查
            摘要='正在检查本地资源…'#中文表
        elif 阶段=='loading':#加载
            摘要=套入('正在加载 {name}…',{'name':名称})#中文表
        elif 阶段=='waking':#唤醒
            摘要='正在唤醒本地语音…'#中文表
        elif 阶段=='ready':#本地就绪
            摘要='本地语音已就绪。'#中文表
        elif 阶段=='standby':#待命
            摘要='本地资源已准备，录音时自动唤醒。'#中文表
        elif 阶段=='cancelled':#已取消
            摘要='准备已取消，已完成的下载会保留。'#中文表
        elif 阶段=='cancelling':#取消中
            摘要='正在取消准备…'#中文表
        else:#其余阶段没有句子
            摘要='' if 阶段 is None else str(阶段)#留空
        节=文档.createElement('section')#一整节
        设类(节,'preparation')#卡片
        节.setAttribute('data-speech-provider','' if 取(提供方,'id') is None else str(取(提供方,'id')))#提供方 id
        名=文档.createElement('strong')#名称
        名.textContent=名称#提供方名
        节.appendChild(名)#挂上
        估算=取(提供方,'setupEstimate')#空间和内存
        if 阶段=='unprepared' and 取(提供方,'location')=='host-local' and 估算 is not None:#首次本地
            盒=文档.createElement('div')#估算
            设类(盒,'setupEstimate')#底
            本地=文档.createElement('p')#说明
            本地.textContent='将在运行 DSH 的机器上下载本地模型，无需安装 Python 或编译工具。'#中文表
            盒.appendChild(本地)#挂上
            表=文档.createElement('dl')#三项
            自身.加估算(文档,表,'硬盘空间',套入('建议预留约 {gb} GB，包含模型、运行时和下载缓存',{'gb':量文本(取(估算,'recommendedDiskBytes')/1000000000)}))#硬盘
            自身.加估算(文档,表,'运行内存',套入('模型加载后约 {gb} GB，识别时可能更高',{'gb':量文本(取(估算,'expectedMemoryBytes')/1000000000)}))#内存
            自身.加估算(文档,表,'首次准备',套入('参考 {min}–{max} 分钟，取决于网络和机器性能',{#时间
                'min':量文本(取(估算,'minimumMinutes')),#最短
                'max':量文本(取(估算,'maximumMinutes')),#最长
            }))
            盒.appendChild(表)#表
            注=文档.createElement('small')#注
            注.textContent='以上为估算；网络较慢时可能更久。已下载的资源会复用，默认在闲置后释放模型内存。'#中文表
            盒.appendChild(注)#挂上
            节.appendChild(盒)#估算
        步骤=list(逐项(取(态,'steps')))#步骤
        列表=文档.createElement('ol')#有序列表
        设类(列表,'steps')#步骤
        for 步 in 步骤:#每一步
            种类=取(步,'status')#状态
            项=文档.createElement('li')#一项
            项.setAttribute('data-step','' if 取(步,'kind') is None else str(取(步,'kind')))#种类
            项.setAttribute('data-step-state','' if 种类 is None else str(种类))#状态
            步名=步骤句(取(步,'kind'),名称)#中文名
            if 种类=='complete':#完成
                点态='done'#完成
                状态名='已完成'#中文表
            elif 种类=='running':#进行
                点态='ongoing'#进行
                状态名='进行中'#中文表
            elif 种类=='failed':#失败
                点态='error'#错误
                状态名='失败'#中文表
            elif 种类=='cancelled':#取消
                点态='idle'#空闲
                状态名='已取消'#中文表
            else:#未开始
                点态='idle'#空闲
                状态名='未开始'#中文表
            项.setAttribute('aria-label',步名+' · '+状态名)#读屏
            点=状态点({'window':窗口,'appearance':'step','size':16,'state':点态}).渲染()#点
            if 点 is not None:#画出来了
                项.appendChild(点)#放前面
            身=文档.createElement('div')#文字
            设类(身,'stepBody')#伸缩
            字=文档.createElement('span')#名称
            字.textContent=步名#名称
            身.appendChild(字)#挂上
            if 种类=='running':#正在这一步
                进=文档.createElement('div')#进度区
                设类(进,'stepProgress')#纵向
                量=文档.createElement('span')#度量
                设类(量,'metric')#次要
                量.setAttribute('role','status')#读屏
                量.textContent=度量#字节或秒
                进.appendChild(量)#挂上
                自身.步骤进度.更新({'window':窗口,'state':态})#进度条
                条=自身.步骤进度.渲染()#条
                if 条 is not None:#有总大小
                    进.appendChild(条)#挂上
                if 阶段=='downloading':#显示资源名
                    小=文档.createElement('small')#资源
                    小.textContent='' if 取(态,'resource') is None else str(取(态,'resource'))#名字
                    进.appendChild(小)#挂上
                身.appendChild(进)#进度
            项.appendChild(身)#文字
            列表.appendChild(项)#一项
        收起=[]#收起时跟在标题后
        量=文档.createElement('span')#度量
        设类(量,'metric')#次要
        量.setAttribute('role','status')#读屏
        量.textContent=度量#字节或秒
        收起.append(量)#度量
        if len(步骤)>0:#有步骤才有下箭头
            收起.append(图标下箭头描边常规({'window':窗口}))#下箭头
        语气=准备语气(态)#标题前的点
        点=状态点({'window':窗口,'state':语气,'size':16,'appearance':'step'}).渲染()#点
        自身.披露.更新({#展开行
            'window':窗口,#窗口
            'open':自身.已展开,#开合
            'expandable':len(步骤)>0,#有步骤才能展
            'title':'准备步骤' if 自身.已展开 else 摘要,#中文表或摘要
            'icon':点,#状态点
            'collapsed':收起,#度量和箭头
            'children':列表,#步骤
            'onToggle':自身.切展开,#切换
        })
        节.appendChild(自身.披露.渲染())#行
        if 自身.已展开 is False:#收起时进度在行下
            自身.总进度.更新({'window':窗口,'state':态})#同一状态
            条=自身.总进度.渲染()#条
            if 条 is not None:#有
                节.appendChild(条)#挂上
        if 阶段=='failed':#失败说明
            自身.失败视图.更新({'window':窗口,'state':态})#失败
            节.appendChild(自身.失败视图.渲染())#说明
        来源=自身.来源列表()#下载源
        可准备=阶段 in ('unprepared','cancelled','failed')#可以开始或重试
        if 可准备 and len(来源)>0:#要选源
            所选=自身.所选源()#当前
            盒=文档.createElement('div')#源
            设类(盒,'sourceChoice')#网格
            标签=文档.createElement('label')#标签加选择框
            标签.appendChild(文档.createTextNode('模型下载源'))#中文表
            选择=文档.createElement('select')#源
            选择.setAttribute('aria-label','模型下载源')#中文表
            选择.value=所选#受控
            if 已连接 is False or 自身.提交中 or len(来源)==1:#不能改
                选择.disabled=True#禁用
            选择.addEventListener('change',自身.改源)#改源
            if len(来源)>1:#多个才有自动
                自动=文档.createElement('option')#自动
                自动.value=''#空
                自动.textContent='自动选择（推荐）'#中文表
                选择.appendChild(自动)#挂上
            for 源 in 来源:#每个源
                项=文档.createElement('option')#一项
                项.value=源#地址
                if 源=='https://huggingface.co':#官方
                    项.textContent='Hugging Face'#中文表
                elif 源=='https://hf-mirror.com':#镜像
                    项.textContent='HF-Mirror（国内镜像）'#中文表
                else:#其余显示地址
                    项.textContent=源#原样
                选择.appendChild(项)#挂上
            标签.appendChild(选择)#选择框
            盒.appendChild(标签)#标签
            助=文档.createElement('small')#说明
            设类(助,'metric')#次要
            if 所选=='':#自动
                助.textContent='优先使用响应较快的源，下载失败时自动尝试其他源。'#中文表
            else:#手动
                助.textContent='仅从所选源下载；已下载并通过校验的文件会复用。'#中文表
            盒.appendChild(助)#挂上
            节.appendChild(盒)#源
        动作行=文档.createElement('div')#按钮
        设类(动作行,'preparationActions')#横向
        if 可准备:#准备或重试
            准备钮=按钮({#轮廓按钮
                'window':窗口,#窗口
                'variant':'outline',#轮廓
                'size':'sm',#小
                'disabled':已连接 is False or 自身.提交中,#不能点
                'children':'下载并准备' if 阶段=='unprepared' else '重试准备',#中文表
                'onClick':自身.开始准备,#开始
            }).渲染()#按钮
            动作行.appendChild(准备钮)#挂上
        if 准备中 and 阶段!='waking':#可以取消，唤醒中不行
            取消钮=按钮({#幽灵按钮
                'window':窗口,#窗口
                'variant':'ghost',#幽灵
                'size':'sm',#小
                'disabled':已连接 is False or 自身.提交中 or 阶段=='cancelling',#不能点
                'children':'取消准备',#中文表
                'onClick':自身.取消这一次,#取消
            }).渲染()#按钮
            动作行.appendChild(取消钮)#挂上
        节.appendChild(动作行)#按钮
        if 自身.错误!='':#这一次动作失败
            错=文档.createElement('p')#一段
            设类(错,'preparationError')#错误色
            错.setAttribute('role','alert')#提醒
            错.textContent=套入('语音识别失败：{message}',{'message':自身.错误})#中文表
            节.appendChild(错)#挂上
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住
            旧.remove()#拆掉
        自身.根=节#留下
        if 父 is not None:#挂回
            父.appendChild(节)#挂上
        return 节#节点

    def 加估算(自身,文档,表,名,值):
        '估算表里的一行'
        行=文档.createElement('div')#一行
        题=文档.createElement('dt')#名
        题.textContent=名#中文
        答=文档.createElement('dd')#值
        答.textContent=值#句子
        行.appendChild(题)#名
        行.appendChild(答)#值
        表.appendChild(行)#挂上

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画


class 语音准备工作:
    '识别偏好和每家提供方的准备卡片'
    def __init__(自身,属性=None):
        '记下保存状态，并订上就绪'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.窗口=取窗口(自身.属性)#窗口
        自身.根=None#整块
        自身.保存中=False#选择框禁用
        自身.错误=''#保存失败
        自身.卡片表={}#提供方 id 到卡片
        自身.麦克风=None#设备选择，有钩子才建
        自身.绘制中=False#避免重入
        自身.待重画=False#绘制中又来了一次
        自身.退订=[]#就绪订阅
        钩=自身.属性.get('useSpeechReadiness')#就绪钩子
        if callable(钩) and hasattr(钩,'_subscribe'):#能订
            自身.退订.append(钩._subscribe(自身.源变了))#目录变了就重画
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的份额'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新
        自身.窗口=取窗口(自身.属性)#窗口

    def 源变了(自身):
        '就绪变了就重画'
        if 自身.绘制中:#正在画
            自身.待重画=True#等结束
            return#不重入
        自身.渲染()#重画

    def 拆除(自身):
        '退订并拆掉卡片'
        for 退 in 自身.退订:#逐个
            if callable(退):#是函数
                退()#退订
        自身.退订=[]#清空
        for 卡片 in list(自身.卡片表.values()):#每张
            卡片.拆除()#停计时
        自身.卡片表={}#清空
        if 自身.麦克风 is not None:#有设备选择
            自身.麦克风.拆除()#停预览

    def 读就绪(自身):
        '读共享就绪'
        钩=自身.属性.get('useSpeechReadiness')#钩子
        if callable(钩) is False:#没有
            return {'catalog':None,'connected':False,'error':None}#空
        就绪=钩(全选快照)#快照
        if isinstance(就绪,dict) is False:#不是字典
            return {'catalog':None,'connected':False,'error':None}#空
        return 就绪#快照

    def 配置(自身,补丁):
        '保存偏好。失败写到错误行'
        自身.保存中=True#禁用
        自身.错误=''#清掉
        自身.渲染()#重画
        try:#写入
            自身.属性['configure'](补丁)#持久化
        except Exception as 失败:#失败
            自身.错误=str(失败)#留下
        自身.保存中=False#结束
        自身.渲染()#重画

    def 改提供方(自身,事件):
        '写入 providerId'
        目标=取(事件,'target')#选择框
        自身.配置({'providerId':取(目标,'value')})#保存

    def 改语言(自身,事件):
        '写入 language'
        目标=取(事件,'target')#选择框
        自身.配置({'language':取(目标,'value')})#保存

    def 卡片(自身,提供方,已连接):
        '按 id 复用准备卡片'
        标识=取(提供方,'id')#id
        已有=自身.卡片表.get(标识)#已有
        份额={'window':自身.窗口,'provider':提供方,'connected':已连接,'prepare':自身.属性.get('prepare'),'cancelPreparation':自身.属性.get('cancelPreparation')}#份额
        if 已有 is None:#新建
            已有=准备卡片(份额)#一张
            自身.卡片表[标识]=已有#记下
        else:#复用
            已有.更新(份额)#换提供方
        return 已有#这张

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
        '偏好选择器和各提供方卡片'
        就绪=自身.读就绪()#目录
        目录=就绪.get('catalog') if isinstance(就绪,dict) else None#目录
        窗口=自身.窗口#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式
        根=文档.createElement('div')#整块
        if isinstance(目录,dict):#有目录
            偏好=文档.createElement('div')#偏好
            设类(偏好,'preferences')#网格
            if 自身.麦克风 is None and callable(自身.属性.get('useMicrophoneDevice')):#还没建
                自身.麦克风=麦克风选择器(自身.属性)#设备
            if 自身.麦克风 is not None:#有
                自身.麦克风.更新(自身.属性)#换份额
                偏好.appendChild(自身.麦克风.渲染())#设备行
            提供方列表=list(逐项(目录.get('providers')))#提供方
            选中标识=取(目录.get('selection'),'providerId')#当前
            选中=None#对象
            for 项 in 提供方列表:#找选中
                if 取(项,'id')==选中标识:#就是
                    选中=项#记下
                    break#完
            服务标签=文档.createElement('label')#识别服务
            服务标签.appendChild(文档.createTextNode('识别服务'))#中文表
            服务=文档.createElement('select')#选择
            服务.value='' if 选中标识 is None else str(选中标识)#受控
            if 就绪.get('connected') is not True or 自身.保存中:#不能改
                服务.disabled=True#禁用
            服务.addEventListener('change',自身.改提供方)#保存
            for 项 in 提供方列表:#每一家
                选项=文档.createElement('option')#一项
                选项.value='' if 取(项,'id') is None else str(取(项,'id'))#id
                选项.textContent='' if 取(项,'name') is None else str(取(项,'name'))#名称
                服务.appendChild(选项)#挂上
            服务标签.appendChild(服务)#选择框
            偏好.appendChild(服务标签)#服务
            语言标签=文档.createElement('label')#语言
            语言标签.appendChild(文档.createTextNode('识别语言'))#中文表
            语言=文档.createElement('select')#选择
            当前语言=取(目录.get('selection'),'language')#当前
            语言.value='' if 当前语言 is None else str(当前语言)#受控
            if 就绪.get('connected') is not True or 自身.保存中:#不能改
                语言.disabled=True#禁用
            语言.addEventListener('change',自身.改语言)#保存
            语言名={'auto':'自动识别','zh':'中文','en':'英语','yue':'粤语','ja':'日语','ko':'韩语'}#中文表
            for 码 in 逐项(取(选中,'languages')):#这一家支持的语言
                选项=文档.createElement('option')#一项
                选项.value='' if 码 is None else str(码)#代码
                选项.textContent=语言名[码] if 码 in 语言名 else ('' if 码 is None else str(码))#中文或原码
                语言.appendChild(选项)#挂上
            语言标签.appendChild(语言)#选择框
            偏好.appendChild(语言标签)#语言
            说明=文档.createElement('p')#位置说明
            if 取(选中,'location')=='cloud':#云端
                说明.textContent='音频将发送至所选云端服务。'#中文表
            else:#本地
                说明.textContent='音频在运行 DSH 的机器上识别。需要下载模型时，请确保该机器能访问所选下载源及其文件服务。如需代理，请在该机器上配置。'#中文表
            偏好.appendChild(说明)#说明
            if 自身.错误!='':#保存失败
                错=文档.createElement('p')#一段
                错.setAttribute('role','alert')#提醒
                错.textContent=套入('语音识别失败：{message}',{'message':自身.错误})#中文表
                偏好.appendChild(错)#挂上
            根.appendChild(偏好)#偏好
            还在=set()#这一轮还在的 id
            for 项 in 提供方列表:#每家一张卡
                还在.add(取(项,'id'))#记下
                根.appendChild(自身.卡片(项,就绪.get('connected') is True).渲染())#卡片
            for 标识 in list(自身.卡片表):#消失的提供方
                if 标识 not in 还在:#已经没有
                    自身.卡片表[标识].拆除()#停计时
                    del 自身.卡片表[标识]#删掉
        else:#还没有目录
            等=文档.createElement('p')#一句
            等.setAttribute('role','status')#读屏
            等.textContent='正在读取识别服务…'#中文表
            根.appendChild(等)#挂上
        if isinstance(就绪,dict) and 就绪.get('error'):#传输错误
            警=文档.createElement('p')#一段
            警.setAttribute('role','alert')#提醒
            警.textContent=套入('语音识别失败：{message}',{'message':就绪.get('error')})#中文表
            根.appendChild(警)#挂上
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#换掉
            父=旧.parentNode#记住
            旧.remove()#拆掉
        自身.根=根#留下
        if 父 is not None:#挂回
            父.appendChild(根)#挂上
        return 根#节点

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画
