import requests
import json

url = "https://www.autohdr.com/api/auth/session"

payload = {}
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Referer': 'https://www.autohdr.com/',
  'Content-Type': 'application/json',
  'sentry-trace': 'cd460caa6d3342abb975c95c9bae012a-aa3b99bac3a79fba-1',
  'baggage': 'sentry-environment=vercel-production,sentry-release=fa15a4d88295ae74c65a99ff2a823bbc08614163,sentry-public_key=3bcbb0b6bfc4d191c0e54d7a05e89abd,sentry-trace_id=cd460caa6d3342abb975c95c9bae012a,sentry-sample_rate=1,sentry-sampled=true',
  'Connection': 'keep-alive',
  'Cookie': '_ga_X6J5L6EM4W=GS2.1.s1775038777$o9$g1$t1775039115$j59$l0$h0; _ga=GA1.1.1237035395.1774500533; _gcl_au=1.1.410779035.1774500533; _ga_session=031b408c0fc3a605b4e8abf05ee1cccc; __cf_bm=031b408c0fc3a605b4e8abf05ee1cccc; _fbp=031b408c0fc3a605b4e8abf05ee1cccc; __stripe_mid=4ef52319-1184-437d-9aa7-26e379703809ad7e46; __client_uat=0; __client_uat_bPuDYU_V=0; SL_C_23361dd035530_SID={"25588168972d551dd916c323235b61fc0ae0dcb1":{"sessionId":"hZ6s60zKyhZFR0BrDmP90","visitorId":"IHQGGutZ77HoLRyDkvEAq"}}; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..A_luiKjAqRl0YSTK.yJU4ogON_OCzsTNpV7ZME-zbQLNR3H2Yx33WwkGbUF64CeszvXqBVbaudopTHbbOjfqln557BOaHZXekcpmDp2yhuSiDHhtELE_I-UPlChVPxXrT24-XKJdKsxIZvT1nUDphskp3pekW7G2ZTGf--zlhdIaQXENnCXjMMdtsKDOe8G__iGYCuwUMkA112zdEVhUCWzSFuKGGbIroURz_aiBNSqL1g-XLTnY8sUdDa11RllbXCeBdb0ktX4EqRr-IpR-7L0TvWu4pjzR9YEHMpq9oCE6hoCqWBd3JQ7lMA85j-ogFnRrwYFP2ToU7JtExGapdAhFcDpIVPdlHK3YWha3V1ertMo3_-YLUdgpHp5mUiyIDuTCgLMm172VjOHo8gRLVBQvkETq6e3W12GH7vbF1FxhvfZ-EvJU66jVpbMVrjNffpX-W9UPns2oj5H3dFem8xIO4zfv-9s-c1dNxiyCjQwnx5aEOwWtBQ_9beAiRLjXIqIawV2oVRxRbTOqkEMJo5HdYKOfg6r52H_v37qMOL7Y5wS5eryFNjaybi7ifSgoeg-QRi7k9iCWhCEKgl5iWDiSjGKXLCU-qUAEgg7thGse0PhBWsARbUs21gKHbL3WmuFqO2ZuRyQqZpQOfrkNGKHa2XOrjdRQa.yqLkNFZ7zNw9xYuUBy5w_Q; autohdr_market_state=1; __Host-next-auth.csrf-token=5083c450312ff4f3adc6cd45ff3dec1dae41c649d6ab2b82267467069dcbf2e8%7C2cfb19b614a4af3873e2fff4c7f8bd05e3c903cc5785b3e8df97ff55cd904c06; __Secure-next-auth.callback-url=https%3A%2F%2Fwww.autohdr.com%2Fpost-signin%3Funique_str%3Dd56055db-8bc6-4fbd-9d30-d9cccecdad11; __stripe_sid=a9e731d6-53d5-4868-a51b-b6cb62814e71d29cd0; _dd_s=logs=1&id=088e6bfe-e7c0-43d3-b03a-96438097f6e3&created=1775039116918&expire=1775040016918; __Host-next-auth.csrf-token=345ae7bd76eb324e2c6fdd63094de134c1acaceb03bfa837caa1da5b968dcc39%7C2d6fb53f8667d3bdb3d918d12f18450735b03f5da558d332cdcfd1932c8dee31; __Secure-next-auth.callback-url=https%3A%2F%2Fwww.autohdr.com; __Secure-next-auth.session-token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIn0..20FKdWps5I4MFzSj.WmzDth7CP0Alt21BZVC3o-tWYF3waYQ64m230pQM6RFeBwk3nWVmsZ9sk9uPE40HL6xFdokN8ZlJrlI38NiFq-ADUZ-hh2nPFNx_zENewsW-Tc5RCaXsqf5F-v0O0MlJi86tzQgNU-r08oJvYhUxUdDavrC60IyN_JviCA9-wZqnpIUiu7KewcFl5EeQ9In9FglvAKRgdJdQJZ7YuRGLZogw1quYVYKbQ2G_iPYMwEenpEO3LmLPoAjv0FCFJNE2Yx0IGfJ90gxWX0Nz5vaFK59HgbIOvskfB0_r3WcHtQFU6Ejd5-FzxK6rP5HhwlpYWzHAtfItTGa4wmjAm0Zc5v-Ey6d0dG2RB0QCGV68HAAoo61kBRTcugzJp6Dz8Md1PWtMTYMSCoJNPfe63yDdbYKmPepUrivA2QfnnWqTAmTpv0x4FHR2-3xFi5JWuBRQ97NCWQpVWhUXZ7QBU1cyXYwFoJ7BnBjBOC6kXsNzs9RESxPK7eip40SXKbkrjukEFBSMFW4ldYrzR-2g8YkpeFXbBEXnRePSadP_ISPwQuggXe5igAnmnBf7u0gpRD6A1MEpPpcQfufXFTddVdh9E4KLwAAAQu8o14S-7IHbV9Y05AtFuUSz8dAYhdizvYPah0YR8QSB3aqEAPVN.ecXHDf4WN6F5_dln1qxW9A; autohdr_market_state=0',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'same-origin',
  'Priority': 'u=4',
  'TE': 'trailers'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
