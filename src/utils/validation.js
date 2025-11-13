import { logger } from './logger.js';

export function validateInput(input) {
const errors = [];

if (!input) {
throw new Error('Input object is missing.');
}

const { categoryUrl, productUrl, maxItems } = input;

if (!categoryUrl && !productUrl) {
errors.push('Either "categoryUrl" or "productUrl" must be provided.');
}

if (categoryUrl && typeof categoryUrl !== 'string') {
errors.push('"categoryUrl" must be a string URL.');
}

if (productUrl && typeof productUrl !== 'string') {
errors.push('"productUrl" must be a string URL.');
}

if (maxItems != null) {
const num = Number(maxItems);
if (!Number.isFinite(num) || num <= 0) {
errors.push('"maxItems" must be a positive number when provided.');
}
}

if (errors.length > 0) {
const message = `Invalid input:\n- ${errors.join('\n- ')}`;
logger.error(message);
throw new Error(message);
}

logger.debug('Input validated successfully:', input);
}