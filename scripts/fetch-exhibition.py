#!/usr/bin/env python3
"""重磅展会数据：国内教育信息化领域重点展会精选 → public/data/exhibition.json

口径变更（2026-10-14 老大拍板）：
  旧口径抓 jyb.cn 新闻 + 教育装备采购网会展频道，结果关键词过滤失效、混入大量无关资讯
  （长征主题展览、读书评论等），真正的展会内容几乎为零。
  新口径改为【人工核验的精选展会清单】：只收录时间、地点、主办方明确的国内
  教育信息化展会/大会（硬件装备展 + 软件会议论坛类），每条附官网/权威通知链接。

核验时间：2026-10-14（网页检索逐条核实，来源见各条目 url）
排序：按开展日期升序（越临近越靠前）。

落选说明（维护者参考）：
  - SmartShow 国际智慧教育展览会（北京国家会议中心，12 月）：两个信息源日期互相矛盾
    （一说 12-05~07，一说 12-18~20，且页面内容疑似旧届复用），按「宁缺毋滥」原则暂不收录，
    待官方确认后再加。

产物字段：{updatedAt, total, items:[{id,title,url,image,summary,date,source}]}
"""
import json
import os
from datetime import datetime, timezone, timedelta

OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'public', 'data', 'exhibition.json')

# date 字段 = 展会档期（区间字符串，前端直接展示）；summary 首句含展馆地点。
EXHIBITIONS = [
    {
        'id': 'cq-expo-2026',
        'title': '2026重庆智慧教育装备与体育装备博览会',
        'date': '2026-10-16 ~ 10-18',
        'venue': '重庆悦来国际博览中心',
        'summary': '📍重庆悦来国际博览中心。设智慧校园建设及IT基础设施、人工智能与创客教育、在线智慧教育与远程教育、职教实训等板块，覆盖教育装备全品类。',
        'url': 'https://news.softunis.com/50671.html',
        'source': '软盟资讯',
    },
    {
        'id': 'caet-wuxi-2026',
        'title': '第九届中国教育技术发展与应用大会暨2026年中国教育技术协会会员代表大会',
        'date': '2026-11-09 ~ 11-12',
        'venue': '无锡国际会议中心',
        'summary': '📍无锡国际会议中心。主题"技术赋能育人，AI点亮未来"，设1场主论坛+20场专题分论坛，含"AI+教育"创新应用技能大赛总决赛与教育技术创新成果展览。',
        'url': 'https://www.caet.org.cn/site/content/1311.html',
        'source': '中国教育技术协会',
    },
    {
        'id': 'jyz-88-changsha',
        'title': '第88届中国教育装备展示会',
        'date': '2026-10-30 ~ 11-01',
        'venue': '长沙国际会展中心',
        'summary': '📍长沙国际会展中心。主题"人工智能引领教育装备高质量发展"，国内规模最大的教育装备行业盛会，集中展示教育大模型、智慧课堂、AI学情分析、虚拟仿真实验等，同期20余场学术交流活动。',
        'url': 'https://wap.ceeia.cn/news/detail_4135.htm',
        'source': '中国教育装备行业协会',
    },
    {
        'id': 'gz-smartedu-2026',
        'title': '中国（广州）智慧教育·智慧校园展览会',
        'date': '2026-11-17 ~ 11-19',
        'venue': '广州琶洲保利世贸博览馆',
        'summary': '📍广州琶洲保利世贸博览馆。主题"共筑共创共享共赢"，聚焦智慧校园信息化解决方案、智慧教室、在线教育与远程教育、创客教育及教育信息化软硬件。',
        'url': 'https://exhibit.56ye.net/show-220366.html',
        'source': '深圳振华展览',
    },
    {
        'id': 'cd-expo15-2026',
        'title': '第15届成都智慧教育展',
        'date': '2026-11-25 ~ 11-26',
        'venue': '成都世纪城新国际会展中心',
        'summary': '📍成都世纪城新国际会展中心。中国西部教育博览会旗下主题展，设智慧与创新教育、在线教育、数字化信息化智慧校园、人工智能机器人与创客教育等展区。',
        'url': 'https://exhibit.56ye.net/show-154532.html',
        'source': '中国西部教育博览会组委会',
    },
    {
        'id': 'get2026',
        'title': 'GET2026教育科技大会',
        'date': '2026-11-25 ~ 11-26',
        'venue': '北京新云南皇冠假日酒店',
        'summary': '📍北京新云南皇冠假日酒店。主题"与爱共生，与AI同育：智能时代教育新范式"，聚焦AI打通教育全链路、校园智慧教育新生态、AI智能硬件创新迭代等方向。',
        'url': 'https://get.jiemodui.com/',
        'source': '芥末堆',
    },
]


def main():
    print(f'== 重磅展会（人工核验精选） {datetime.now().isoformat(timespec="seconds")} ==')
    items = []
    for e in EXHIBITIONS:
        items.append({
            'id': e['id'],
            'title': e['title'],
            'url': e['url'],
            'image': '',  # 无外链图，走前端本地占位图轮换
            'summary': e['summary'],
            'date': e['date'],
            'source': e['source'],
        })
    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')
    data = {'updatedAt': now, 'total': len(items), 'items': items}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'== 写出 {OUT_PATH}：{len(items)} 条 ==')


if __name__ == '__main__':
    main()
