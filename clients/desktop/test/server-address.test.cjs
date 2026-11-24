const assert = require('node:assert/strict');
const test = require('node:test');
const { normalizeServerAddress } = require('../server-address.cjs');

test('adds HTTPS to a server hostname and trims whitespace', () => {
    assert.equal(
        normalizeServerAddress(' blackjack.bcull.online '),
        'https://blackjack.bcull.online/'
    );
});

test('accepts custom HTTP and HTTPS server addresses', () => {
    assert.equal(
        normalizeServerAddress('http://192.168.1.20:3000'),
        'http://192.168.1.20:3000/'
    );
    assert.equal(
        normalizeServerAddress('https://games.example.com/blackjack'),
        'https://games.example.com/blackjack'
    );
});

test('rejects invalid schemes and embedded credentials', () => {
    for (const address of ['', 'not a URL', 'file:///etc/passwd', 'javascript:alert(1)', 'https://user:pass@example.com']) {
        assert.throws(() => normalizeServerAddress(address));
    }
});
