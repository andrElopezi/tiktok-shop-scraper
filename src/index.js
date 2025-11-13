import Apify from 'apify';
import { logger } from './utils/logger.js';
import { validateInput } from './utils/validation.js';
import { createClient } from './scraper/tiktokClient.js';
import { parseProducts } from './scraper/parser.js';
import { DEFAULT_CONFIG } from './config.js';

async function runScraper(apifyEnv = true) {
logger.info('TikTok Shop scraper started');

let input = {};
if (apifyEnv) {
input = (await Apify.getInput()) || {};
} else {
// Fallback input for local debugging
input = {
categoryUrl: 'https://example.com/tiktok-shop-category.html',
maxItems: 20
};
}

const config = {
...DEFAULT_CONFIG,
...(input.config || {})
};

const query = {
categoryUrl: input.categoryUrl,
productUrl: input.productUrl,
maxItems: input.maxItems || config.maxItems
};

validateInput(query);

const client = createClient(config);

logger.info('Fetching TikTok Shop page...');
const { body: rawBody, url: finalUrl } = await client.fetchProductsPage(query);

logger.info(`Page fetched successfully from ${finalUrl}. Parsing products...`);
const products = parseProducts(rawBody, { maxItems: query.maxItems });

logger.info(`Parsed ${products.length} product(s). Saving to dataset...`);

if (apifyEnv) {
const dataset = await Apify.openDataset();
for (const product of products) {
await dataset.pushData(product);
}
} else {
// Local mode: just log the products
logger.info('Products:', JSON.stringify(products, null, 2));
}

logger.info('TikTok Shop scraper finished.');
return products;
}

// When running on Apify platform
Apify.main(async () => {
try {
await runScraper(true);
} catch (err) {
logger.error('Scraper failed:', err);
throw err;
}
});

// Allow local execution via `node src/index.js`
if (import.meta.url === `file://${process.argv[1]}`) {
runScraper(false).catch((err) => {
logger.error('Local run failed:', err);
process.exit(1);
});
}