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
                yield scrapy.Request(self.user_irl.format(user=result.get('url_token'), include=self.user.query), self.parse_user)
        if 'paging' in results.keys() and results.get('paging').get('is_end') == False:
            next_page = results.get('paging').get('next')
            yield scrapy.Request(next_page, self.parse_followers)