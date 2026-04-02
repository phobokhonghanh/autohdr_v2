import json
import requests
import json

url = "https://www.autohdr.com/api/proxy/photoshoots/907761/processed_photos?page=1&page_size=10"

payload = {}
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://www.autohdr.com/listings',
  'Content-Type': 'application/json',
  'ngrok-skip-browser-warning': 'true',
  'sentry-trace': 'a9712f8cab004fbc90fb1486a0d1c255-adfe7e910c5c1955-1',
  'baggage': 'sentry-environment=vercel-production,sentry-release=fa15a4d88295ae74c65a99ff2a823bbc08614163,sentry-public_key=3bcbb0b6bfc4d191c0e54d7a05e89abd,sentry-trace_id=a9712f8cab004fbc90fb1486a0d1c255,sentry-sample_rate=1,sentry-sampled=true',
  'Connection': 'keep-alive',
  'Cookie': '_ga_X6J5L6EM4W=GS2.1.s1775011104$o5$g1$t1775011133$j31$l0$h0; _ga=GA1.1.1237035395.1774500533; _gcl_au=1.1.410779035.1774500533; _ga_session=031b408c0fc3a605b4e8abf05ee1cccc; __cf_bm=031b408c0fc3a605b4e8abf05ee1cccc; _fbp=031b408c0fc3a605b4e8abf05ee1cccc; __stripe_mid=4ef52319-1184-437d-9aa7-26e379703809ad7e46; __client_uat=0; __client_uat_bPuDYU_V=0; SL_C_23361dd035530_SID={"25588168972d551dd916c323235b61fc0ae0dcb1":{"sessionId":"hZ6s60zKyhZFR0BrDmP90","visitorId":"IHQGGutZ77HoLRyDkvEAq"}}; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..fCS3O6-w4bDDT4Oy.ibybIj8476qbgasr28XJF5bJIuOV7wteABs5upl1_LuBiLdMIZ9Co10XzGAOQbLjvJnrwg-e4sl8utBj1M0QELBCfuoT4zG8IArnkCuQbqoT2Thui5IayCnW7YBwt3WMWgAFArbmmDbnFqD8azeX-eojQGUQlGx4V6Qga0OqwC9tn8tA8JNfHotgoHMDDFMXd1DBBUeF24XeCWSznOh0nlvyuYK5LWmu07H5m7iEmXvPxWQKU_xg70mKKBH22HYc3-0x8sHnHCghoqQe2vWfij9qKo5zjny1bhnJxiNo1Rw_4xrT2YOzaBpzdmr4e5gy80rIUnSJNMhRAAEXsxanid1MNNJC_KFtEXXM1YDroRrfed7bbO8TDy455w-RtYuc4OWBmbwABJYRG1Jb2b0kevirvj-V0kWWlR4pSSU9fOGAwSYhU997E-LY0hIiE9AlpG36Ka5GBrC9a2rJoYlwqm79XXP5U_Y9hJ7SIro6mAax8QRCDKGIwYp1ujW12yzeziqixoJehtUxocaVr9dWi9G-wp1cVrWj5CyA65w5TJowA6rdMYt1sEwT3iZu8f_fGDbiEWUVAMGqUKoNhCwIg29zRfO1Mww7N2uKObUaVmWYJrIfUFlw4OFG0fFCPo4fQ62IpBi3N13j5XUz.m-W7qHfrrlsfTkNXXwmXag; autohdr_market_state=1; __Host-next-auth.csrf-token=5083c450312ff4f3adc6cd45ff3dec1dae41c649d6ab2b82267467069dcbf2e8%7C2cfb19b614a4af3873e2fff4c7f8bd05e3c903cc5785b3e8df97ff55cd904c06; __Secure-next-auth.callback-url=https%3A%2F%2Fwww.autohdr.com%2Fpost-signin%3Funique_str%3Dd56055db-8bc6-4fbd-9d30-d9cccecdad11; _dd_s=logs=1&id=515e7d31-c196-447b-9433-427c55f568a7&created=1775011105129&expire=1775012125129; __stripe_sid=ee7a9080-e6e6-46cd-8482-ef0f15eb9cd7af1ce3; autohdr_market_state=0',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Priority': 'u=0',
  'TE': 'trailers'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

# response -> json
# [
#     {
#         "url": "https://image-upload-autohdr-j.s3.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/processed/anh-dep-1.jpg?response-content-disposition=inline&AWSAccessKeyId=AKIA4ZPZU4K2DBM7KGHU&Signature=WW%2FEhdUTk1MWWmmmKPiOnJxl%2BN0%3D&Expires=1775021384",
#         "id": 23985654,
#         "human_edit_requested": false,
#         "downloaded": false,
#         "order_index": 0,
#         "toggle_enum": "photo_url",
#         "cloud_url": "",
#         "fire_url": "",
#         "grass_url": "",
#         "twilight_url": "",
#         "staged_url": "",
#         "autoremove_url": "",
#         "autofill_url": "",
#         "declutter_url": "",
#         "realtor_sign_removed_url": "",
#         "upscale_url": "",
#         "re_edit_url": "",
#         "re_paint_url": "",
#         "stamped_overlay_url": "",
#         "lot_line_url": "",
#         "notes_for_editor": null,
#         "flagged_for_training": false,
#         "processing_status": null,
#         "original_photo_id": null
#     },
#     {
#         "url": "https://image-upload-autohdr-j.s3.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/processed/anh-dep-2.jpg?response-content-disposition=inline&AWSAccessKeyId=AKIA4ZPZU4K2DBM7KGHU&Signature=SWKfNDlvAyDFD4UFzzQAreQsTcQ%3D&Expires=1775021384",
#         "id": 23985655,
#         "human_edit_requested": false,
#         "downloaded": false,
#         "order_index": 1,
#         "toggle_enum": "photo_url",
#         "cloud_url": "",
#         "fire_url": "",
#         "grass_url": "",
#         "twilight_url": "",
#         "staged_url": "",
#         "autoremove_url": "",
#         "autofill_url": "",
#         "declutter_url": "",
#         "realtor_sign_removed_url": "",
#         "upscale_url": "",
#         "re_edit_url": "",
#         "re_paint_url": "",
#         "stamped_overlay_url": "",
#         "lot_line_url": "",
#         "notes_for_editor": null,
#         "flagged_for_training": false,
#         "processing_status": null,
#         "original_photo_id": null
#     }
# ]