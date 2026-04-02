import requests
import json

url = "https://www.autohdr.com/api/proxy/generate_presigned_urls"

payload = json.dumps({
  "unique_str": "83b93a60-aef6-409a-9f0d-7c1683c06e3f",
  "files": [
    {
      "filename": "anh-dep-1.jpg",
      "md5": ""
    },
    {
      "filename": "anh-dep-2.png",
      "md5": ""
    }
  ]
})
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://www.autohdr.com/',
  'Content-Type': 'application/json',
  'sentry-trace': '03dbfc2a55dc41b681a4bacb5583ad01-858deee0d47447a3-1',
  'baggage': 'sentry-environment=vercel-production,sentry-release=fa15a4d88295ae74c65a99ff2a823bbc08614163,sentry-public_key=3bcbb0b6bfc4d191c0e54d7a05e89abd,sentry-trace_id=03dbfc2a55dc41b681a4bacb5583ad01,sentry-sample_rate=1,sentry-sampled=true',
  'Origin': 'https://www.autohdr.com',
  'Connection': 'keep-alive',
  'Cookie': '_ga_X6J5L6EM4W=GS2.1.s1775029817$o7$g1$t1775029950$j60$l0$h0; _ga=GA1.1.1237035395.1774500533; _gcl_au=1.1.410779035.1774500533; _ga_session=031b408c0fc3a605b4e8abf05ee1cccc; __cf_bm=031b408c0fc3a605b4e8abf05ee1cccc; _fbp=031b408c0fc3a605b4e8abf05ee1cccc; __stripe_mid=4ef52319-1184-437d-9aa7-26e379703809ad7e46; __client_uat=0; __client_uat_bPuDYU_V=0; SL_C_23361dd035530_SID={"25588168972d551dd916c323235b61fc0ae0dcb1":{"sessionId":"hZ6s60zKyhZFR0BrDmP90","visitorId":"IHQGGutZ77HoLRyDkvEAq"}}; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..JqGHtiaquF2vBiM0.qz95FYyEOioNVdBvb-MOY4fHejjQe7-C5ZXybMENuXn4PE6zPPPW9kAWVFETVXN-9QyQye_6ymxIXq2fka25LPPbH6rMjyaUQsTixld3UjQbxMiUWlVcSqJ4dfht0KAkGl_VzvW8EVp7o7Sre7ckP7kGGxajGDxQG9lPp0f5vMs9lib9IQ45AJRuJRR6c-iOHqtdgcTrTTCBTzH_ZN1p12WvuY3v1oJJEcL6SRMb1A5FONZzLKIepf6OQUjD8fGFoC-QdRm4v_B8ALrF1iH5CBt2aTBItqNpkVEeo8CIYQ_x3z6UBrUJ_KOmxxb6MCATW1sinzj37VKwioNAxFXARHGskqH4C47K4Cp0IRYqzkM9lqTGR4w3YlMhPs9_0Mgyi4GTsYcT5xfY9U46_eMRwt9LzfiPoeXHD6ANoSIfxYZ5HNUrdcAMWTwzk6bhHHcg3CN6V380qUluEpK2WXtOHNpXMglWLOGpLlDphfeaYzbFrO9Bq8yDUmW5KP9i7LPWgtd0HbRYB44z6CUCPgzEe8mSijPJXUkqmSfGZGDDatscI0Nk3iIBqCojejBzZSCOtB4dPzSLgKujV9JfC_rXO4n01Xw38641pSW-4WhsoeaEOuphR8NhU4Pe5rxLU5VBg9zxcdUlAm6r-WaJ.oYdPYsUwXhnzPdO5BSjZPw; autohdr_market_state=1; __Host-next-auth.csrf-token=5083c450312ff4f3adc6cd45ff3dec1dae41c649d6ab2b82267467069dcbf2e8%7C2cfb19b614a4af3873e2fff4c7f8bd05e3c903cc5785b3e8df97ff55cd904c06; __Secure-next-auth.callback-url=https%3A%2F%2Fwww.autohdr.com%2Fpost-signin%3Funique_str%3Dd56055db-8bc6-4fbd-9d30-d9cccecdad11; __stripe_sid=a9e731d6-53d5-4868-a51b-b6cb62814e71d29cd0; autohdr_market_state=0',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Priority': 'u=0',
  'TE': 'trailers'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)

# response -> json
# {
# 	"presignedUrls": [
# 		{
# 			"filename": "anh-dep-1.jpg",
# 			"url": "https://image-upload-autohdr-j.s3-accelerate.amazonaws.com/6efd1121-d628-40d4-8688-1518adf31ff1/raw/anh-dep-1.jpg?AWSAccessKeyId=AKIA4ZPZU4K2DBM7KGHU&Signature=fcrSGWq%2B7xtEnUlZoiokR4184%2FE%3D&content-type=application%2Foctet-stream&x-amz-acl=private&content-md5=&Expires=1775033550"
# 		},
# 		{
# 			"filename": "anh-dep-2.png",
# 			"url": "https://image-upload-autohdr-j.s3-accelerate.amazonaws.com/6efd1121-d628-40d4-8688-1518adf31ff1/raw/anh-dep-2.png?AWSAccessKeyId=AKIA4ZPZU4K2DBM7KGHU&Signature=cJpuvWwu%2FWCDUo4oR6JqeGJ1tDQ%3D&content-type=application%2Foctet-stream&x-amz-acl=private&content-md5=&Expires=1775033550"
# 		}
# 	]
# }