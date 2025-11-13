export const DEFAULT_CONFIG = {
  maxItems: 100,
  requestTimeoutSecs: 30,
  proxyUrl: process.env.PROXY_URL || null,
  userAgent:
    process.env.USER_AGENT ||
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
};