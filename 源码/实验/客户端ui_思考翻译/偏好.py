'宿主配置与浏览器偏好草稿共用的校验'
import re#语言代码

__all__=['语言偏好模式','提供方偏好']

语言偏好模式=re.compile(r'^(?:auto|[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*)$')#auto 或语言代码
提供方偏好=('bing','google','deepseek-account','deepseek-official')#显式提供方，不回落到别的
