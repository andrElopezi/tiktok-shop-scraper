import cheerio from 'cheerio';
import { logger } from '../utils/logger.js';

function normalizeProductFromJson(obj) {
return {
id: obj.id || obj.product_id || obj.productId || null,
title: obj.title || obj.name || '',
price: obj.sale_price ?? obj.price ?? null,
originalPrice: obj.origin_price ?? obj.original_price ?? null,
sold: obj.sold ?? obj.sales ?? null,
rating: obj.rating ?? obj.score ?? null,
url: obj.product_link || obj.url || null,
image: obj.image || obj.thumbnail || null,
raw: obj,
source: 'json'
};
}

function parseFromJson(rawBody, maxItems) {
const trimmed = rawBody.trim();
if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) {
return [];
}

try {
const data = JSON.parse(trimmed);
const arr = Array.isArray(data)
? data
: data.products || data.items || data.data || [];

if (!Array.isArray(arr)) {
return [];
}

const products = arr.map(normalizeProductFromJson);
return Number.isFinite(maxItems) ? products.slice(0, maxItems) : products;
} catch (err) {
logger.debug('Failed to parse JSON, falling back to HTML parsing:', err.message);
return [];
}
}

function parseFromHtml(rawBody, maxItems) {
const $ = cheerio.load(rawBody);
const items = [];

const selectors =
'[data-e2e="tiktok-shop-product-card"], .product-card, [data-product-id]';

$(selectors).each((_, el) => {
if (Number.isFinite(maxItems) && items.length >= maxItems) {
return false;
}

const root = $(el);

const title =
root.find('.product-title, [data-e2e="product-name"]').first().text().trim() ||
root.attr('data-product-name') ||
'';

const price =
root.find('.product-price, [data-e2e="product-price"]').first().text().trim() ||
root.attr('data-price') ||
null;

const anchor = root.find('a').first();
const link = anchor.attr('href') || null;

const image =
root.find('img').first().attr('src') || root.attr('data-image') || null;

if (!title && !link) {
return;
}

items.push({
title,
price,
url: link,
image,
source: 'html'
});
});

return items;
}

export function parseProducts(rawBody, options = {}) {
const maxItems =
typeof options.maxItems === 'number' && options.maxItems > 0
? options.maxItems
: Infinity;

if (!rawBody || typeof rawBody !== 'string') {
logger.error('parseProducts expected a non-empty string body.');
return [];
}

// 1) Try JSON first
const fromJson = parseFromJson(rawBody, maxItems);
if (fromJson.length > 0) {
logger.info(`Parsed ${fromJson.length} product(s) from JSON payload.`);
return fromJson;
}

// 2) Fallback to HTML
const fromHtml = parseFromHtml(rawBody, maxItems);
logger.info(`Parsed ${fromHtml.length} product(s) from HTML markup.`);
return fromHtml;
}