'近期麦克风振幅。动画只改 SVG 线，不整页重画'
from ....客户端.模块.客户端.通告 import 取握手窗口
import os#样式文件位置
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块#模块样式

__all__=['波形图']#录音行里的振幅

样式路径=os.path.join(os.path.dirname(__file__),'语音输入.module.css')#本目录样式
样式模块='VoiceInput'#与样式表对应的模块名
条数=80#历史条数


def 设类(节点,*类名):
    '挂上官方类名，让模块样式生效'
    留下=[]#非空类名
    for 名 in 类名:#逐个
        if isinstance(名,str) and 名!='':#有内容
            留下.append(名)#留下
    节点.className=' '.join(留下)#类名保持原文
    return 标样式模块(节点,样式模块)#模块属性


def 取窗口(属性):
    '调用方窗口优先，否则用当前页'
    if isinstance(属性,dict) and 属性.get('window') is not None:#份额里带了窗口
        return 属性['window']#调用方窗口
    return 取握手窗口()#当前页


class 波形图:
    '画出最近测到的电平。没有声音时保持点状基线'
    def __init__(自身,属性=None):
        '记下录音和标签，并画出条带'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#SVG
        自身.条=[]#元素和电平
        自身.帧=None#动画编号
        自身.上次=-10**12#上次推进的时间
        自身.录音标识=None#当前动画对应的采集
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的录音或标签'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 拆除(自身):
        '停掉动画'
        if 自身.帧 is not None:#还在请求帧
            取窗口(自身.属性).cancelAnimationFrame(自身.帧)#取消
            自身.帧=None#记下

    def 推进(自身,现在):
        '满 50 毫秒就把当前振幅推进一格'
        if 现在-自身.上次<50:#还没到间隔
            return#等下一帧
        自身.上次=现在#记下这次
        录音=自身.属性.get('recording')#当前采集
        下一=0#没有采集就是静音
        if 录音 is not None:#正在采
            下一=录音.振幅()#当前 RMS
        for 条 in 自身.条:#从新到旧
            先前=条['level']#这一格的旧值
            条['level']=下一#换成较新的
            下一=先前#旧值传给下一格
            高度=1+min(1,条['level']*5)*17#1 到 18
            条['element'].setAttribute('y1',str(20-高度))#上端
            条['element'].setAttribute('y2',str(20+高度))#下端

    def 开动画(自身):
        '按帧推进。采集对象没变就沿用已有电平'
        窗口=取窗口(自身.属性)#窗口
        录音=自身.属性.get('recording')#当前采集
        if 自身.帧 is not None and 自身.录音标识 is 录音:#同一只采集
            return#不重置历史
        换了采集=自身.录音标识 is not 录音#采集对象变了就清历史
        自身.拆除()#停掉上一轮
        自身.录音标识=录音#记下
        自身.上次=-10**12#马上推进一次
        if 换了采集:#不要沿用上一只麦克风的电平
            for 条 in 自身.条:#每一格
                条['level']=0#静音
                条['element'].setAttribute('y1','19')#基线上端
                条['element'].setAttribute('y2','21')#基线下端

        def 画(现在):
            '这一帧推进后预约下一帧'
            自身.推进(现在)#改线
            自身.帧=窗口.requestAnimationFrame(画)#下一帧

        自身.帧=窗口.requestAnimationFrame(画)#开始

    def 渲染(自身):
        '画出 80 根竖线。已有条带只重开动画'
        窗口=取窗口(自身.属性)#窗口
        文档=窗口.document#文档
        注入模块样式文件(文档,'语音输入样式',样式路径,样式模块)#样式只插一次
        if 自身.根 is None:#还没有条带
            图=文档.createElement('svg')#条带
            设类(图,'waveform')#模块类
            图.setAttribute('viewBox','0 0 640 40')#坐标
            图.setAttribute('preserveAspectRatio','none')#拉满宽度
            图.setAttribute('role','img')#给读屏
            图.setAttribute('aria-label',自身.属性.get('label') or '')#正在录音
            自身.条=[]#清空
            序号=0#下标
            while 序号<条数:#80 根
                线=文档.createElement('line')#一根
                线.setAttribute('x1',str(序号*8+4))#横位置
                线.setAttribute('x2',str(序号*8+4))#竖线
                线.setAttribute('y1','19')#静音上端
                线.setAttribute('y2','21')#静音下端
                线.setAttribute('stroke','currentColor')#跟文字颜色
                线.setAttribute('stroke-width','3')#线宽
                线.setAttribute('stroke-linecap','round')#圆头
                线.setAttribute('opacity',str(0.25+序号/120))#越靠右越实
                图.appendChild(线)#挂上
                自身.条.append({'element':线,'level':0})#电平稳从 0
                序号=序号+1#下一根
            自身.条.reverse()#新电平从右边推进
            旧=自身.根#上一份
            父=None#挂载点
            if 旧 is not None:#换掉
                父=旧.parentNode#记住位置
                旧.remove()#拆掉
            自身.根=图#留下
            if 父 is not None:#还在页面上
                父.appendChild(图)#挂回
        else:#条带还在
            自身.根.setAttribute('aria-label',自身.属性.get('label') or '')#标签可能变了
        自身.开动画()#按当前采集推进
        return 自身.根#节点

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画
