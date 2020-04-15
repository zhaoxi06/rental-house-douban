[代码来源](https://github.com/yaodi833/rental_house_douban)
# rental_house_douban
本项目基于（非公开）豆瓣api，实时监控多个豆瓣租房小组发布租房信息，并支持小组订制，关键词订制，邮件推送等功能。

在原有代码的基础上，增加了一些功能：
* 帖子链接发送到邮箱的内容由纯链接改为标题超链接
* 增加了过滤掉帖子中包含的关键字的功能
* 将爬取的帖子用html文件保存到results文件夹中