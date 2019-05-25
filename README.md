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


选取一个知乎大V作为爬取开头，如：
> https://www.zhihu.com/people/excited-vczh

通过观察个人信息页面，确定需要爬取的基本信息，如：姓名，签名，职业，关注数，赞同数等。
> 注：Ajax，即Asynchronous JavaScript and XML，指异步的JavaScript和XML，指利用JavaScript在保证页面不被刷新、页面链接不改变的情况下与服务器交换数据并更新部分网页的技术。

点击页面内选项卡中的关注，再翻页，可在控制台中发现出现了相应的Ajax请求。这个就是获取关注列表的接口。其形式如：
> followees?include=data...

观察其请求结构（headers），请求方法为GET，URL为https://www.zhihu.com/api/v4/members/excited-vczh/followees?... ，后跟了三个参数，分别为include，offset，limit。可以发现，offset为偏移量，limit表示每页数量，结合这两项即可表示当前的页数。include中则是查询参数。

接下来查看返回结果（Preview），包括有data和paging两个字段。data中包含了关注列表的用户信息，每页有20个内容。paging内容中的字段则可用于请求下一页，其中is_end表示当前翻页是否结束，next则是下一页的链接。

由上，我们即可通过接口获取到获取关注列表了。

若将鼠标放在关注列表中的任意一个头像上，则又会出现新的Ajax请求。可以通过Network控制台中看到该次请求的链接为：
> https://www.zhihu.com/api/v4/members/...

后面同样跟了一个include参数，其包含了一些查询参数。在该请求的返回结果（Preview）中几乎可以获得所有详情。因此我们可以通过该接口获取关注列表中的用户的详细信息。

总结：
- 通过请求 https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&offset={offset}&limit={limit} 这样的接口以获取用户的关注列表，其中user为该用户的url_token。
- 通过请求 https://www.zhihu.com/api/v4/members/{user}?include={include} 这样的接口获取用户的详细信息，其中user同样为该用户的url_token。

有了上两条爬取逻辑后，即可开始构造请求。

### 构造请求
##### 1.生成第一步请求
第一步即为请求起始用户（excited-vczh）的基本信息，然后再获取其关注列表。首先在之前创建的spider中删除原本的start_urls，新构造一个格式化的url，将其中一些可变参数提取出来，然后重写start_requsets方法，以生成第一步的请求。

同时，还需要实现两个解析方法parse_user和parse_follow。修改后代码如下：
```python
import scrapy

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    # 查询用户信息的url地址
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'
    # 查询关注列表的url地址
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&amp;offset={offset}&amp;limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    # 起始用户
    start_user = 'excited-vczh'
 
    def start_requests(self):
        yield scrapy.Request(self.user_url.format(user=self.start_user, include=self.user_query), callback=self.parse_user)
        yield scrapy.Request(self.follows_url.format(user=self.start_user, include=self.follows_query, limit=20, offset=0), callback=self.parse_follows)

    def parse_user(self, response):
        print(response.text)
    
    def parse_follows(self, response):
        print(response.text)
```
>注：在url中\&amp;用于转义，表示&

修改完后即可通过在命令行运行下属命令运行，并观察结果：
> scrapy crawl zhihu

成功爬取得到结果。
##### 2.编写parse_user
接下来处理爬取得到的用户基本信息，通过查看接口信息所返回的数据，在items.py中新声明一个UserItem：
```python
import scrapy
class UserItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.fleid()
    type = scrapy.Field()
    gender = scrapy.Field()
    answer_count = scrapy.Field()
    articles_count = scrapy.Field()
    follower_count = scrapy.Field()
    is_vip = scrapy.Field()
    headline = scrapy.Field()
    url_token = scrapy.Field()
    url = scrapy.Field()
    ...   
```

以爬取需要的信息。接下来在spider.py的解析方法里接析我们得到的response，然后转为json对象，依次判断字段是否存在，若存在则赋值：
```python
def parse_user(self, response):
    result = json.loads(response.text)
    item = UserItem()
    for field in item.fields:
        if field in result.keys():
            item[field] = result.get(field)
    yield item
```

得到item后通过yield即可饭回。这样保存用户基本信息的步骤就完成了。接下来还需要获取该用户的关注列表，因此需要再发起一个获取关注列表的request。在parse_user后面在添加：
```python
yield scrapy.Request(
    self.follows_url.format(user=result.get('url_token'), 
    include=self.follows_query, limit=20, offset=0), 
    self.parse_follows)
```

这样就又生成了获取该用户关注列表的请求。
##### 3. 编写prase_follows
同样的步骤处理关注列表。先解析response的文本，然后做两件事：
- 通过关注列表的每一个用户，对每一个用户发起请求，获取其详细信息
- 处理分页，判断paging内容，获取下一页的关注列表
改写parse_follows如下：
```python
def parse_follows(self, response):
    results = json.loads(response.text)
    # 对用户关注列表的接析，json数据中有两个字段，分别为data和page，其中page是分页信息
    if 'data' in results.keys():
        for result in results.get('data'):
            yield scrapy.Request(self.user_url.format(user=result.get('url_token'), include=self.user_query), self.parse_user)
    ## 判断page是否存在切is_end是否为false，即判断是否最后一页
    if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
        next_page = results.get('paging').get('next')
        ## 获取下一页地址并返回request
         yield scrapy.Request(next_page, self.parse_follows)
```
运行爬虫，成功爬取信息。
##### 4. 编写prase_followers
通过获取关系列表实现循环递归爬取后，可以同样的方式获取用户的粉丝列表。经过分析后发现粉丝列表的api也类似，除了将followee换成follower外其他完全相同，所以我们也可通过同样的逻辑添加followers相关信息。

需要改动的位置有：
- 在zhihu.py中添加followers_url和followers_query
- 在start_requests中添加yield followers信息
- 在parse_user中添加yield followers信息
- 编写parse_followers

如此一来，该spider便完成了，我们便可通过其实现知乎社交网络的递归爬取。
完整的zhihu.py代码如下：
```python
# -*- coding: utf-8 -*-
from zhihu_user.items import UserItem
import json
import scrapy

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    # 查询用户信息的url地址
    user_url = 'https://www.zhihu.com/api/v4/members/{user}?include={include}'
    user_query = 'allow_message,is_followed,is_following,is_org,is_blocking,employments,answer_count,follower_count,articles_count,gender,badge[?(type=best_answerer)].topics'
    # 查询关注列表的url地址
    follows_url = 'https://www.zhihu.com/api/v4/members/{user}/followees?include={include}&amp;offset={offset}&amp;limit={limit}'
    follows_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics'
    # 查询粉丝列表的url地址
    followers_url = 'https://www.zhihu.com/api/v4/members/{iser}/followers?include={include}&amp;offset={offset}&amp;limit={limit}'
    followers_query = 'data[*].answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics' 
    # 起始用户
    start_user = 'excited-vczh'
 
    def start_requests(self):
        yield scrapy.Request(self.user_url.format(user=self.start_user, include=self.user_query), callback=self.parse_user)
        yield scrapy.Request(self.follows_url.format(user=self.start_user, include=self.follows_query, limit=20, offset=0), callback=self.parse_follows)
        yield scrapy.Request(self.followers_url.format(user=self.start_user, include=self.followers_query, limit=20, offset=0), callback=self.parse_followers)

    def parse_user(self, response):
        result = json.loads(response.text)
        item = UserItem()

        for field in item.fields:
            if field in result.keys():
                item[field] = result.get(field)
        yield item
        yield scrapy.Request(self.follows_url.format(user=result.get('url_token'), include=self.follows_query, limit=20, offset=0), self.parse_follows) 
        yield scrapy.Request(self.followers_url.format(user=result.get('url_token'), include=self.followers_query, limit=20, offset=9), self.parse_followers)

    def parse_follows(self, response):
        results = json.loads(response.text)
        # 对用户关注列表的接析，json数据中有两个字段，分别为data和page，其中page是分页信息
        if 'data' in results.keys():
            for result in results.get('data'):
                yield scrapy.Request(self.user_url.format(user=result.get('url_token'), include=self.user_query), self.parse_user)
        ## 判断page是否存在切is_end是否为false，即判断是否最后一页
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            ## 获取下一页地址并返回request
            yield scrapy.Request(next_page, self.parse_follows)
    
    # 编写逻辑同parse_follows
    def parse_followers(self, response):
        results = json.loads(response.text)
        if 'data' in results.keys():
            for result in  results.get('data'):
                yield scrapy.Request(self.user_irl.format(user=reslt.get('url_token'), include=self.user.query), self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield scrapy.Request(next_page, self.parse_followers)
```
在anaconda虚拟环境命令行中运行：
> scrapy crawl zhihu -o zhihu.csv

可将爬取得到的内容保存成csv格式。json，xml，pickle，marshal亦同。
### 小结


### 额外信息
##### 配置爬虫关闭的条件
在scrapy的默认配置文件中存在四个配置：
```python
CLOSESPIDER_TIMEOUT = 0
CLOSESPIDER_PAGECOUNT = 0
CLOSESPIDER_ITEMCOUNT = 0
CLOSESPIDER_ERRORCOUNT = 0
```
该四个配置用于配置爬虫的自动关闭条件，等于0代表不开启。其中：
- CLOSESPIDER_TIMEOUT表示指定爬虫运行的秒数
- CLOSESPIDER_ITEMCOUNT表示爬虫爬取的条目数
- CLOSESPIDER_PAGECOUNT表示爬虫爬取的响应数
- CLOSESPIDER_ERRORCOUNT表示爬虫爬取可以接受的最大错误数

当这四个值不为0时，spider的过程中的任意一项参数超过配置数后，爬虫便会被自动关闭。运行时在命令行中设置：
> scrapy crawl zhihu -s CLOSESPIDER_ITEMCOUNT=10

> scrapy crawl zhihu -s CLOSESPIDER_PAGECOUNT=10

> scrapy crawl zhihu -s CLOSESPIDER_TIMEOUT=10

> scrapy crawl zhihu -s CLOSESPIDER_ERRORCOUNT=10

### reference:
> 1. https://zhuanlan.zhihu.com/p/26378388
> 2. https://www.cnblogs.com/111testing/p/10325425.html
> 3. https://www.cnblogs.com/felixwang2/p/8807233.html
> 4. https://blog.csdn.net/qq_41020281/article/details/83315752
> 5. https://blog.csdn.net/Q_AN1314/article/details/51104701