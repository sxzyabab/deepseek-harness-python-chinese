'没有渲染器认领时，这些二进制后缀不走纯文本回落'
from .后缀 import 文档文件名,匹配后缀长度

__all__=['不可预览二进制路径']

不可预览二进制后缀=(
    'mp4','mov','avi','mkv','webm','flv','wmv','m4v',
    'mp3','wav','flac','ogg','m4a','aac','wma','opus',
    'zip','gz','tgz','bz2','xz','zst','7z','rar','tar','jar',
    'doc','docx','xls','xlsx','ppt','pptx','odt','ods','odp','pages','numbers',
    'exe','dll','so','dylib','bin','o','class','pyc','wasm',
    'ttf','otf','woff','woff2','eot',
    'dmg','iso','img','sqlite','db',
    'psd','ai','sketch','tiff','tif','heic','heif','avif',
)

def 不可预览二进制路径(路径):
    '文件名后缀是否在这份没有渲染器的二进制名单里'
    return 匹配后缀长度(文档文件名(路径),不可预览二进制后缀)>0
