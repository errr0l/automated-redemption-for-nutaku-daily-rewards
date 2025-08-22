# from src.util.common import load_json
#
#
# def test_get_rewards_calendar(config, logger, html_data):
#     resp_data = load_json(config, "test_response.json", logger)
#     logger.debug("resp_data: {}".format(resp_data))
#     current_gold = 0
#     total_gold = 0
#     claimed = 0
#     for item in resp_data["rewards"]:
#         if item['benefitType'] == 'gold':
#             gold = int(item['slotTitle'].replace("Gold", "").strip())
#             total_gold += gold
#             # 当日没签到时为current-not-claimed，签到后为current-claimed
#             if item['status'] == 'current-not-claimed':
#                 if current_gold == 0:
#                     current_gold = gold
#             elif item['status'] == 'claimed':
#                 claimed += gold
#     html_data['destination'] = resp_data['areAllRewardClaimed']
#     html_data['gold'] = current_gold
#     html_data['total_gold'] = total_gold
#     html_data['calendar_id'] = resp_data.get('id')
#     html_data['is_reward_claimed'] = resp_data['isRewardClaimed']
#     html_data['claimed'] = claimed
#     return 1
#
#
# def test_get_rewards_calendar2():
#     print("1111")
#     return None
#
#
# def test_get_nutaku_home():
#     return {}
#
#
# def test_parse_html_for_data():
#     _d = {
#         'csrf_token': '123456',
#         'url': 'https://www.nutaku.net/rewards-calendar/rewards-calendar/redeem/'
#     }
#     return _d
#
#
# def test_get_rewards():
#     return {'userGold': '343'}
#
#
# def test_login(config, cookies, proxies, csrf_token):
#     return {
#         "NUTAKUID": "32EhlsDF2qjFD3WA8nw7PzrlflMcwIgHqL8nbYG2",
#         "Nutaku_TOKEN": "a35affb96791115d8b26d6fc77b6fd2c28d9d34b70f3ea86a6e031c9a78a6380",
#         "Nutaku_cookiesConsent": "1",
#         "Nutaku_gamePreferences": "%5B%5D",
#         "Nutaku_locale": "en",
#         "Nutaku_returningVisitor": "1755828985",
#         "Nutaku_userLoggedIn": "1",
#         "_m": "150226158",
#         "LBSERVERID": "ded4486"
#     }
