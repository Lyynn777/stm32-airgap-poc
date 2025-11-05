// crypto_stub.c
#include "crypto_stub.h"
#include <string.h>
#include <stdio.h>

/*
 * WARNING: These implementations are placeholders and NOT SECURE.
 * They are provided so the project compiles and you can test the end-to-end
 * framing & streaming logic without importing mbedTLS right now.
 *
 * Replace with mbedtls_xxx equivalents as soon as you can.
 */

int aes_init(AES_CTX *ctx, const uint8_t *key, size_t keylen, const uint8_t *iv, size_t ivlen) {
    if (!ctx || !key || !iv) return -1;
    if (keylen != AES_KEY_LEN || ivlen != AES_IV_LEN) {
        // still allow but warn (replace when using mbedTLS)
    }
    memset(ctx, 0, sizeof(AES_CTX));
    memcpy(ctx->key, key, (keylen < AES_KEY_LEN) ? keylen : AES_KEY_LEN);
    memcpy(ctx->iv, iv, (ivlen < AES_IV_LEN) ? ivlen : AES_IV_LEN);
    return 0;
}

int aes_encrypt_stream(AES_CTX *ctx, const uint8_t *in, size_t in_len, uint8_t *out, size_t *out_len) {
    // Very naive XOR cipher for placeholder behavior: NOT CRYPTOGRAPHICALLY SECURE.
    // This is to allow end-to-end testing. Replace with AES-CTR or AES-GCM using mbedTLS.
    if (!ctx || !in || !out || !out_len) return -1;
    for (size_t i = 0; i < in_len; ++i) {
        out[i] = in[i] ^ ctx->key[i % AES_KEY_LEN];
    }
    *out_len = in_len;
    return 0;
}

void aes_free(AES_CTX *ctx) {
    if (!ctx) return;
    memset(ctx, 0, sizeof(AES_CTX));
}

/* Minimal SHA-256 placeholder using a trivial accumulation:
   This is NOT real SHA-256. Replace with mbedtls_sha256_*.
*/
void sha256_init(SHA256_CTX *ctx) {
    if (!ctx) return;
    memset(ctx, 0, sizeof(SHA256_CTX));
    ctx->state[0] = 0x6a09e667;
    ctx->state[1] = 0xbb67ae85;
    ctx->state[2] = 0x3c6ef372;
    ctx->state[3] = 0xa54ff53a;
    ctx->state[4] = 0x510e527f;
    ctx->state[5] = 0x9b05688c;
    ctx->state[6] = 0x1f83d9ab;
    ctx->state[7] = 0x5be0cd19;
    ctx->bitlen = 0;
    ctx->buf_idx = 0;
}

void sha256_update(SHA256_CTX *ctx, const uint8_t *data, size_t len) {
    if (!ctx || !data) return;
    // Simple, insecure mixing: XOR into state words — placeholder only.
    for (size_t i = 0; i < len; ++i) {
        ctx->state[i % 8] ^= (uint32_t)data[i];
    }
    ctx->bitlen += (uint64_t)len * 8ULL;
}

void sha256_final(SHA256_CTX *ctx, uint8_t out_hash[SHA256_DIGEST_LEN]) {
    if (!ctx || !out_hash) return;
    // Produce a deterministic but non-cryptographic 32-byte digest based on state
    for (int i = 0; i < 8; ++i) {
        uint32_t v = ctx->state[i];
        out_hash[i*4 + 0] = (v >> 24) & 0xFF;
        out_hash[i*4 + 1] = (v >> 16) & 0xFF;
        out_hash[i*4 + 2] = (v >> 8) & 0xFF;
        out_hash[i*4 + 3] = (v >> 0) & 0xFF;
    }
}

void bytes_to_hex(const uint8_t *in, size_t in_len, char *out_hex) {
    static const char hexchars[] = "0123456789abcdef";
    for (size_t i = 0; i < in_len; ++i) {
        out_hex[2*i] = hexchars[(in[i] >> 4) & 0xF];
        out_hex[2*i + 1] = hexchars[in[i] & 0xF];
    }
    out_hex[2*in_len] = '\0';
}

