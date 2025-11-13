import fetch from 'node-fetch';
import { logger } from '../utils/logger.js';

function fetchWithTimeout(url, options, timeoutMs) {
return new Promise((resolve, reject) => {
const timeoutId = setTimeout(() => {
const err = new Error(`Request timed out after ${timeoutMs} ms`);
err.code = 'ETIMEDOUT';
reject(err);
}, timeoutMs);

fetch(url, options)
.then((res) => {
clearTimeout(timeoutId);
resolve(res);
})
.catch((err) => {
clearTimeout(timeoutId);
reject(err);
});
});
}

export function createClient(config = {}) {
const {
requestTimeoutSecs = 30,
proxyUrl = null,
userAgent = 'Mozilla/5.0'
} = config;

async function fetchProductsPage(query) {
const targetUrl = query.productUrl || query.categoryUrl;

if (!targetUrl) {
throw new Error('No target URL provided to fetchProductsPage.');
}

const headers = {
'User-Agent': userAgent,
Accept: 'text/html,application/json;q=0.9,*/*;q=0.8'
};

const fetchOptions = {
method: 'GET',
headers
// Proxy support can be added here with a custom agent if required.
};

logger.info(`Requesting URL: ${targetUrl}`);
if (proxyUrl) {
logger.info(`Note: PROXY_URL is set (${proxyUrl}), but HTTP proxy agent is not wired in this example.`);
}

const timeoutMs = requestTimeoutSecs * 1000;

const response = await fetchWithTimeout(targetUrl, fetchOptions, timeoutMs);
const contentType = response.headers.get('content-type') || '';

if (!response.ok) {
const message = `Request failed with status ${response.status} (${response.statusText})`;
logger.error(message);
throw new Error(message);
}

const body = await response.text();
logger.debug(`Received ${body.length} bytes with content-type: ${contentType}`);

return {
body,
url: response.url || targetUrl,
contentType
};
}

return {
fetchProductsPage
};
}