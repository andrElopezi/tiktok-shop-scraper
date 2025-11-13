import assert from 'assert';
import { parseProducts } from '../src/scraper/parser.js';

function testParseHtmlMultipleProducts() {
const html = `
<div class="product-card">
<a href="https://tiktok.com/product/1">
<img src="https://example.com/image1.jpg" />
<span class="product-title">Product One</span>
<span class="product-price">$10</span>
</a>
</div>
<div class="product-card">
<a href="https://tiktok.com/product/2">
<img src="https://example.com/image2.jpg" />
<span class="product-title">Product Two</span>
<span class="product-price">$20</span>
</a>
</div>
`;

const products = parseProducts(html, { maxItems: 10 });
assert.strictEqual(products.length, 2, 'Should parse two products from HTML');
assert.strictEqual(products[0].title, 'Product One');
assert.strictEqual(products[0].price, '$10');
assert.strictEqual(products[0].url, 'https://tiktok.com/product/1');
assert.strictEqual(products[1].title, 'Product Two');
assert.strictEqual(products[1].price, '$20');
}

function testParseJsonProducts() {
const json = JSON.stringify({
products: [
{
id: '123',
title: 'JSON Product',
sale_price: 9.99,
product_link: 'https://tiktok.com/product/json1',
image: 'https://example.com/json1.jpg'
}
]
});

const products = parseProducts(json, { maxItems: 10 });
assert.strictEqual(products.length, 1, 'Should parse one product from JSON');
assert.strictEqual(products[0].id, '123');
assert.strictEqual(products[0].title, 'JSON Product');
assert.strictEqual(products[0].price, 9.99);
assert.strictEqual(products[0].url, 'https://tiktok.com/product/json1');
assert.strictEqual(products[0].image, 'https://example.com/json1.jpg');
}

function testMaxItemsLimit() {
const html = `
<div class="product-card">
<a href="https://tiktok.com/product/1">
<span class="product-title">Product One</span>
<span class="product-price">$10</span>
</a>
</div>
<div class="product-card">
<a href="https://tiktok.com/product/2">
<span class="product-title">Product Two</span>
<span class="product-price">$20</span>
</a>
</div>
<div class="product-card">
<a href="https://tiktok.com/product/3">
<span class="product-title">Product Three</span>
<span class="product-price">$30</span>
</a>
</div>
`;

const products = parseProducts(html, { maxItems: 2 });
assert.strictEqual(products.length, 2, 'maxItems should limit number of products');
}

(function run() {
try {
testParseHtmlMultipleProducts();
testParseJsonProducts();
testMaxItemsLimit();
console.log('All tests passed.');
process.exit(0);
} catch (err) {
console.error('Test failed:', err);
process.exit(1);
}
})();