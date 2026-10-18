__all__=['站点主机','匹配站点','站点字形']

站点主机=(
    'github.com','github.io','raw.githubusercontent.com','gitlab.com','npmjs.com','pypi.org',
    'stackoverflow.com','developer.mozilla.org','wikipedia.org','news.ycombinator.com',
    'youtube.com','youtu.be','x.com','twitter.com','bilibili.com','zhihu.com','juejin.cn',
    'csdn.net','google.com','baidu.com','duckduckgo.com','tiktok.com','netflix.com','spotify.com',
    'facebook.com','instagram.com','reddit.com','telegram.org','t.me','weixin.qq.com','qq.com',
    'whatsapp.com','wa.me','weibo.com','taobao.com','aliexpress.com','ebay.com','quora.com',
    'v2ex.com','apple.com',
)

def 匹配站点(网址):
    '绝对 http(s) 才认主机。最长后缀优先。没有商标路径，只返回主机后缀'
    if not isinstance(网址,str) or 网址=='':
        return None
    if '://' not in 网址:
        return None
    方案,其余=网址.split('://',1)
    if 方案 not in ('http','https'):
        return None
    主机=其余.split('/',1)[0].split('?',1)[0].split('#',1)[0]
    if '@' in 主机:
        主机=主机.rsplit('@',1)[-1]
    if ':' in 主机 and not 主机.startswith('['):
        主机=主机.rsplit(':',1)[0]
    主机=主机.lower()
    命中=None
    长度=0
    for 后缀 in 站点主机:
        if 主机==后缀 or 主机.endswith('.'+后缀):
            if len(后缀)>长度:
                命中=后缀
                长度=len(后缀)
    return 命中

def 站点字形(属性):
    '已知主机也不画商标。simple-icons 的 path 不在这棵树里，所以始终不返回 svg'
    if not isinstance(属性,dict):
        return None
    匹配站点(属性.get('href'))
    return None
