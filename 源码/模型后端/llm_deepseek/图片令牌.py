"""DeepSeek 视觉 token 记账：按公布的 v41 配置原样移植。"""
from math import floor,sqrt,trunc
from ...附件.附件.请求投影 import 长边尺寸

__all__=['深求请求图尺寸','深求图片令牌']

补丁边=14
降采样比=3
最大图令牌=1024
最小像素=544*544
单元边=补丁边*降采样比

def 整除(值,除数):
    """向零取整除法。"""
    return floor(值/除数)

def 向上整除(值,除数):
    """向上取整除法。"""
    return floor((值+除数-1)/除数)

def 网格令牌(网格高,网格宽):
    """一行一带分隔，外加两个成帧 token。"""
    return 网格高*(网格宽+1)+2

def 网格格数(填充边长):
    """一条已填充像素轴上的 token 格数。"""
    return 向上整除(整除(填充边长,补丁边),降采样比)

def 求解缩放比(高,宽,预算):
    """在预算内求解保比例的最大网格。"""
    纵横=高/宽
    理想宽=sqrt((预算-2)/纵横+0.25)-0.5
    理想高=理想宽*纵横
    if 理想宽<1:
        解宽=1
        解高=整除(预算-2,解宽+1)
        最佳宽=解宽*单元边
        最佳高=解高*单元边
    elif 理想高<1:
        解高=1
        解宽=整除(预算-2,解高)-1
        最佳宽=解宽*单元边
        最佳高=解高*单元边
    else:
        解宽=trunc(理想宽)
        解高=trunc(理想高)
        比例=min(解宽*单元边/宽,解高*单元边/高)
        最佳宽=trunc(宽*比例/补丁边)*补丁边
        最佳高=trunc(高*比例/补丁边)*补丁边
    网格高=网格格数(最佳高)
    网格宽=网格格数(最佳宽)
    return {
        'gridHeight':网格高,
        'gridWidth':网格宽,
        'bestHeight':最佳高,
        'bestWidth':最佳宽,
        'numTokens':网格令牌(网格高,网格宽),
    }

def 安全缩放(高,宽,填充高,填充宽):
    """把已填充像素投影到预算内最大网格。"""
    网格高=网格格数(填充高)
    网格宽=网格格数(填充宽)
    直接={
        'gridHeight':网格高,
        'gridWidth':网格宽,
        'bestHeight':填充高,
        'bestWidth':填充宽,
        'numTokens':网格令牌(网格高,网格宽),
    }
    if 直接['numTokens']<=最大图令牌:
        return 直接
    求解=求解缩放比(高,宽,最大图令牌)
    if 求解['numTokens']>最大图令牌:
        raise RuntimeError('deepseek 图片令牌: 无网格能放入 '+str(宽)+'x'+str(高)+' 的 token 预算')
    return 求解

def 缩放一次(宽,高):
    """一次缩放-填充-投影。"""
    缩放宽=宽
    缩放高=高
    像素=缩放宽*缩放高
    if 像素<最小像素 and 像素>0:
        比例=sqrt(最小像素/像素)
        缩放宽=trunc(缩放宽*比例)
        缩放高=trunc(缩放高*比例)
    填充宽=向上整除(缩放宽,补丁边)*补丁边
    填充高=向上整除(缩放高,补丁边)*补丁边
    return 安全缩放(缩放高,缩放宽,填充高,填充宽)

def 相同缩放(甲,乙):
    """两次网格求解是否相同。"""
    return (甲['gridHeight']==乙['gridHeight']
        and 甲['gridWidth']==乙['gridWidth']
        and 甲['bestHeight']==乙['bestHeight']
        and 甲['bestWidth']==乙['bestWidth']
        and 甲['numTokens']==乙['numTokens'])

def 深求请求图尺寸(宽,高):
    """Harness 发出的尺寸，使提供方保留整图。小图不放大。"""
    填充宽=向上整除(宽,补丁边)*补丁边
    填充高=向上整除(高,补丁边)*补丁边
    if 网格令牌(网格格数(填充高),网格格数(填充宽))<=最大图令牌:
        return {'width':宽,'height':高}
    求解=求解缩放比(高,宽,最大图令牌)
    长边=求解['bestWidth'] if 宽>=高 else 求解['bestHeight']
    return 长边尺寸(宽,高,长边)

def 深求图片令牌(宽,高):
    """给定请求图尺寸时 DeepSeek 收取的视觉 token，至多 1024。"""
    结果=缩放一次(宽,高)
    迭代=1
    while 迭代<10:
        下一=缩放一次(结果['bestWidth'],结果['bestHeight'])
        if 相同缩放(下一,结果):
            return 结果['numTokens']
        结果=下一
        迭代+=1
    raise RuntimeError('deepseek 图片令牌: 缩放未收敛于 '+str(宽)+'x'+str(高))
