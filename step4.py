import requests
import json

url = "https://www.autohdr.com/api/inference/associate-and-run"

payload = json.dumps({
  "unique_str": "83b93a60-aef6-409a-9f0d-7c1683c06e3f",
  "email": "ndinhnguyen.work@gmail.com",
  "firstname": "Nguyên",
  "lastname": "Nguyễn",
  "address": "147852",
  "spoofId": None,
  "smartlook_url": None,
  "indoor_model_id": 1,
  "outdoor_model_id": None,
  "files_count": 1,
  "grass_replacement": False,
  "perspective_correction": True,
  "special_attention": False,
  "declutter": False,
  "photoshoot_id": None
})
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://www.autohdr.com/',
  'Content-Type': 'application/json',
  'sentry-trace': 'b3498d9ff96046b3bb6561a29fe60385-bf962560985b6a1d-1',
  'baggage': 'sentry-environment=vercel-production,sentry-release=fa15a4d88295ae74c65a99ff2a823bbc08614163,sentry-public_key=3bcbb0b6bfc4d191c0e54d7a05e89abd,sentry-trace_id=b3498d9ff96046b3bb6561a29fe60385,sentry-sample_rate=1,sentry-sampled=true',
  'Origin': 'https://www.autohdr.com',
  'Connection': 'keep-alive',
  'Cookie': '_ga_X6J5L6EM4W=GS2.1.s1775011104$o5$g1$t1775011925$j26$l0$h0; _ga=GA1.1.1237035395.1774500533; _gcl_au=1.1.410779035.1774500533; _ga_session=031b408c0fc3a605b4e8abf05ee1cccc; __cf_bm=031b408c0fc3a605b4e8abf05ee1cccc; _fbp=031b408c0fc3a605b4e8abf05ee1cccc; __stripe_mid=4ef52319-1184-437d-9aa7-26e379703809ad7e46; __client_uat=0; __client_uat_bPuDYU_V=0; SL_C_23361dd035530_SID={"25588168972d551dd916c323235b61fc0ae0dcb1":{"sessionId":"hZ6s60zKyhZFR0BrDmP90","visitorId":"IHQGGutZ77HoLRyDkvEAq"}}; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..sSajjlcs36twO5Ie.tp97GcDVVsx_6xNPdrxwDN78NQZQaprXw5bWv2pOxIclcx2sBdK60MhHi72cX14sL0JLK4l4HX61kY2mV-lIYisXhm_GC9yWDpmG2EoOCiaLcnpfNpn-B9oJyrJ8wUlcBR3Bf-dIS65Fdx06XjAAY4ku7Veao-AnWId0DZtYaNoKaSKAkk-y_YX0beO8UxIlRT6S6shNhv78rEJZSzj0Lkz9NLU1qlxTMmcQv4Gpab1AWIQLMdzc_r_MaP4WQjEC4YKLV4ldxwcxTx7zf_GeRUv8rK9RlirgADtdK9gkvLoodRJF6TiJ1YKbRHcOOJv_joHYRXIX5hWT9kGlxtew90-Tpg_CFXbSPrVJGwHqV9uBdFa6RbByAC9jlrFLRcEawzFWuwJiu5uyqb3xyuXFgJ_Cx3XJp8mYli-P04TlrCmmnoh3LlZXmVawyJGK7K8JSfqaSZo86cfGggxqml5_WqOAMfSU6pDcqRywY8009SznAocXVqSm8oveFAmM7C8_wHRxeOCAZUclbu_gfP_TWpvfAlGqB9Aew6__UsHo09boRC_RWT8R-13aKwLOyTuVby1jFt8re1WvYD2FfbYclfzIux_AATWLoV6kvhuvoDph7EH3iVGKqUB_uDBUxebXYeWUh2JufkerwzcD.gYEGlaKDAwRhUOV7vhS9mw; autohdr_market_state=1; __Host-next-auth.csrf-token=5083c450312ff4f3adc6cd45ff3dec1dae41c649d6ab2b82267467069dcbf2e8%7C2cfb19b614a4af3873e2fff4c7f8bd05e3c903cc5785b3e8df97ff55cd904c06; __Secure-next-auth.callback-url=https%3A%2F%2Fwww.autohdr.com%2Fpost-signin%3Funique_str%3Dd56055db-8bc6-4fbd-9d30-d9cccecdad11; _dd_s=logs=1&id=515e7d31-c196-447b-9433-427c55f568a7&created=1775011105129&expire=1775012799884; __stripe_sid=ee7a9080-e6e6-46cd-8482-ef0f15eb9cd7af1ce3; autohdr_market_state=0',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Priority': 'u=4'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# response -> json
# {
#     "success": true,
#     "env": "prod"
# }