function normalizeServerAddress(value) {
    if (typeof value !== 'string' || !value.trim()) {
        throw new Error('Enter a server address.');
    }

    let address = value.trim();
    if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(address)) {
        address = `https://${address}`;
    }

    let parsed;
    try {
        parsed = new URL(address);
    } catch {
        throw new Error('Enter a valid server address.');
    }

    if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname
        || parsed.username || parsed.password) {
        throw new Error('Use an HTTP or HTTPS server address without login details.');
    }
    return parsed.toString();
}

module.exports = { normalizeServerAddress };
