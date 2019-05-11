# Scrapy爬取知乎用户信息
### 目标
- 从一个大V用户开始，通过递归爬取粉丝列表和关注列表，以实现知乎所有用户详细信息的抓取。
- （可选）将抓取结果储存到数据库中，并进行去重操作。
### 环境需求
- Python3.6

通过miniconda创建python版本号为3.6的虚拟环境
> conda create -n spider python=3.6

> conda activate spider
- Scrapy
> pip install scrapy
>
注意，在安装scrapy框架前，还需安装下列库至虚拟环境中：
1. 安装lxml库(pip)
2. 安装pyOpenSSL库(pip)
3. 安装Twisted库(wheel+pip)
4. 安装PyWin32库(wheel+pip)


### 创建项目
在命令行通过以下命令创建一个项目：
> scrapy startproject zhihu_user

### 创建爬虫
通过命令行进入到项目中，运行genspider命令创建一个spider
> cd zhihu_user

> scrapy genspider zhihu www.zhihu.com

### 禁止ROBOTSTXT_OBEY
将settings.py中的ROBOTSTXT_OBEY设为False：
```python
ROBOTSTXT_OBEY = False
```
其默认为True，表示遵守robots.txt规则。 robots.txt 是遵循 Robot 协议的一个文件，它保存在网站的服务器中，它的作用是，告诉搜索引擎爬虫，本网站哪些目录下的网页**不希望**你进行爬取收录。在Scrapy启动后，会在第一时间访问网站的 robots.txt 文件，然后决定该网站的爬取范围。

### 加入请求头
未加入请求头headers中的User-Agent。访问知乎域名下的网页必须指定User-Agent，否则会被服务器检测为爬虫而遭封杀
添加方案：
1. 在settings.py文件中设置，取消DEFAULT_REQUEST_HEADERS的注释，加入如下内容（全局设置）：
```python
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
}
```
2. 在创建spider中加入：
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36',
}
```
3. 在Request的参数中加入。

本次爬取使用方案一。添加后在命令行中运行如下命令：
> scrapy crawl zhihu

即可得到返回（200）的结果。未添加时，则会出现返回状态码出错的问题。
同时会出现重定向状态码（301）/（302），这是由于自动创建的爬虫的url开头为http而非https。

### 爬取流程分析
为探寻获取用户详细信息和关注列表的接口，回到网页并检查网页，打开控制台切换到Network模式。


通过一个大V作为开头，其个人信息页面地址如下：
> https://www.zhihu.com/people/excited-vczh

通过观察个人信息页面，确定需要爬取得基本信息，如：姓名，签名，职业，关注数，赞同数等。

点击页面内选项卡中的关注，再翻页，可在控制台中发现出现了相应得Ajax请求。这个就是获取关注列表的接口。其形式如：
> followees?include=data...

观察其请求结构，请求方法为GET，URL为https://www.zhihu.com/api/v4/members/excited-vczh/followees?...，后跟了三个参数，分别为include，offset，limit。

可以发现，offset为偏移量，limit表示每页数量，结合这两项即可表示当前的页数。include中则是查询参数。
### 生成第一步请求一些

### O Auth

### parse_user

### prase_follows

### followers

### 小结